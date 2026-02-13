import asyncio
import base64
import json
import logging
import re
from typing import Dict, List, Optional, Any

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory

from app.core.config import get_credential, settings
from app.core.database import get_history, get_user_state, save_message, save_user_state
from app.core.dependencies import get_code_executor, get_garmin, get_strava
from app.core.prompts import get_system_prompt
from app.self_improving.hooks import handle_user_prompt_submit
from app.services.web_fallback_service import WebFallbackService, needs_web_fallback
from skills.homeassistant import get_homeassistant_command_processor
# --- Native Tooling Imports ---
from app.services.tool_registry import registry
# Ensure tools are registered
import app.tools.implementations

logger = logging.getLogger(__name__)

class UnifiedChatService:
    """
    Service responsible for handling chat logic across different interfaces (Web, Telegram, Voice).
    Consolidates:
    - User state management
    - Context injection (Garmin, Strava)
    - LLM generation
    - Web fallback (Google/Wikipedia)
    - Code execution parsing
    """

    def __init__(self):
        self.web_fallback_service = WebFallbackService()

    async def process_message(
        self,
        session_id: str,
        user_msg: str,
        image_data: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> str:
        """
        Process a user message and return the AI response.
        Uses Native Function Calling (Tools) loop.
        """
        # 1. Setup & Defaults
        if not model_id:
            model_id = get_credential("SELECTED_MODEL") or "gemini-2.0-flash"

        logger.info(f"Processing message for session {session_id} with model {model_id}")

        # 2. Direct Home Assistant command route.
        # This keeps deterministic HA command behavior for inputs like "ha list".
        ha_processor = get_homeassistant_command_processor()
        ha_result = await ha_processor.process_message(session_id, user_msg)
        if ha_result.handled and ha_result.response:
            save_message(session_id, "user", user_msg)
            save_message(session_id, "assistant", ha_result.response)
            return ha_result.response

        # 3. Logic Hook (Self-improving)
        handle_user_prompt_submit(user_msg, project_root=".")

        # 3. User State & Profile Memory
        user_state = get_user_state(session_id)
        extracted_now = self._extract_user_state(user_msg)
        if extracted_now:
            user_state.update(extracted_now)
            save_user_state(session_id, extracted_now)

        # 4. Build Context (System Prompt + Profile)
        system_prompt = get_system_prompt()
        
        # User Profile Context
        user_state_context = self._build_user_state_context(user_state)
        state_instructions = (
            "USER PROFILE MEMORY (persisted across turns):\n"
            f"{user_state_context}\n\n"
            "Use these values for calculations when missing from the latest user message. "
            "Only ask for missing fields."
        )

        full_system_block = f"{system_prompt}\n\n{state_instructions}"

        # --- MEM0 INTEGRATION (Long Term Memory) ---
        mem0_client = None
        mem0_key = get_credential("MEM0_API_KEY")
        user_id = settings.USER_ID
        
        if mem0_key and len(mem0_key) > 5:
            try:
                from mem0 import AsyncMemoryClient
                mem0_client = AsyncMemoryClient(api_key=mem0_key)
                
                # Search for relevant memories
                relevant_memories = await mem0_client.search(user_msg, user_id=user_id)
                mem_text = ""
                for mem in relevant_memories:
                    # Mem0 returns list of dicts with 'memory' key
                    if isinstance(mem, dict) and 'memory' in mem:
                        mem_text += f"- {mem['memory']}\n"
                
                if mem_text:
                    full_system_block += f"\n\n--- LONG TERM MEMORY (Facts I know about {user_id}) ---\n{mem_text}"
                    logger.info(f"Injected {len(relevant_memories)} memories into context.")
            except Exception as e:
                logger.warning(f"Mem0 search failed (continuing without memory): {e}")

        
        # 5. Build History for Gemini
        db_history = get_history(session_id=session_id, limit=10)
        
        gemini_history = []
        # System Prompt
        gemini_history.append({"role": "user", "parts": [full_system_block]})
        gemini_history.append({"role": "model", "parts": ["Jag har tagit emot kontexten och är redo att hjälpa till."]})

        # DB History
        for msg in db_history:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

        # 6. Add Current User Message
        current_parts = [user_msg]
        
        if image_data:
            try:
                if "," in image_data:
                    b64_data = image_data.split(",", 1)[1]
                else:
                    b64_data = image_data
                
                img_bytes = base64.b64decode(b64_data)
                current_parts.append({"mime_type": "image/jpeg", "data": img_bytes})
                logger.info("Image attached to request")
            except Exception as exc:
                logger.error(f"Image decode error: {exc}")

        gemini_history.append({"role": "user", "parts": current_parts})

        # 7. Call Gemini with Tool Loop
        try:
            google_api_key = get_credential("GOOGLE_API_KEY")
            if not google_api_key:
                return "Error: GOOGLE_API_KEY is missing."

            genai.configure(api_key=google_api_key)
            tools_def = registry.get_gemini_function_declarations()
            
            # Helper to run blocking generate_content
            def generate(history):
                model = genai.GenerativeModel(model_id, tools=tools_def)
                return model.generate_content(
                    history,
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )

            loop = asyncio.get_event_loop()
            
            # --- TOOL EXECUTION LOOP ---
            max_turns = 5
            final_text_response = ""
            
            for _ in range(max_turns):
                response = await loop.run_in_executor(None, lambda: generate(gemini_history))
                
                if not response.candidates:
                    return "Error: AI returned no candidates."
                
                candidate = response.candidates[0]
                
                # Check for Function Calls
                function_calls = []
                for part in candidate.content.parts:
                    if part.function_call:
                        function_calls.append(part.function_call)
                
                if function_calls:
                    # Append AI's processing step to history
                    gemini_history.append(candidate.content)
                    
                    # Execute all function calls
                    for fc in function_calls:
                        fname = fc.name
                        fargs = dict(fc.args)
                        
                        logger.info(f"AI requesting tool: {fname}({fargs})")
                        
                        # Execute Tool
                        result_text = await registry.execute(fname, fargs)
                        
                        # Append Result to history
                        gemini_history.append({
                            "role": "function",
                            "parts": [
                                genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=fname,
                                        response={"result": result_text}
                                    )
                                )
                            ]
                        })
                    
                    # Loop continues to send results back to AI
                    continue
                
                # No function calls -> Final Response
                final_text_response = response.text
                break
            
            if not final_text_response:
                final_text_response = "Error: Maximum tool turns exceeded or no response."

            # 8. Web Fallback (Legacy / Safety net)
            web_fallback_enabled = str(get_credential("WEB_FALLBACK_ENABLED", "true")).lower() in {"1", "true", "yes", "on"}
            if web_fallback_enabled and needs_web_fallback(final_text_response):
                logger.info("Triggering Legacy Web Fallback (AI didn't use tool?)")
                final_text_response = await self.web_fallback_service.build_fallback_answer(
                    query=user_msg,
                    original_answer=final_text_response,
                )

            # 9. Save to DB
            save_message(session_id, "user", user_msg)
            save_message(session_id, "assistant", final_text_response)

            # --- MEM0 SAVE (Async) ---
            if mem0_client and final_text_response:
                try:
                    # Add interaction to memory
                    await mem0_client.add(
                        [
                            {"role": "user", "content": user_msg}, 
                            {"role": "assistant", "content": final_text_response}
                        ],
                        user_id=user_id
                    )
                    logger.info("Saved interaction to Mem0.")
                except Exception as e:
                    logger.warning(f"Failed to save to Mem0: {e}")

            return final_text_response

        except Exception as exc:
            logger.error(f"Chat error: {exc}", exc_info=True)
            return f"Error: {str(exc)}"

    async def run_proactive_task(self, session_id: str, prompt: str) -> str:
        """
        Executes a proactive task (like Morning Briefing) using the same core logic.
        Includes MEM0 access but skips user-specific message saving.
        """
        logger.info(f"Running proactive task for session {session_id}")
        
        # 1. Setup
        model_id = get_credential("SELECTED_MODEL") or "gemini-2.0-flash"
        system_prompt = get_system_prompt()
        user_state = get_user_state(session_id)
        
        # 2. Build Context
        user_state_context = self._build_user_state_context(user_state)
        state_instructions = (
            "USER PROFILE MEMORY:\n"
            f"{user_state_context}\n"
        )
        full_system_block = f"{system_prompt}\n\n{state_instructions}"

        # 3. MEM0 (Context Retrieval only)
        # We might want to find relevant memories for "Morning Briefing" or "Goals"
        mem0_key = get_credential("MEM0_API_KEY")
        if mem0_key:
             try:
                from mem0 import AsyncMemoryClient
                mem0 = AsyncMemoryClient(api_key=mem0_key)
                # Search for general preferences or goals
                # "Planning day, goals, preferences"
                relevant = await mem0.search("My daily goals and preferences", user_id=settings.USER_ID)
                mem_text = "\n".join([f"- {m['memory']}" for m in relevant if 'memory' in m])
                if mem_text:
                    full_system_block += f"\n\n--- LONG TERM MEMORY ---\n{mem_text}"
             except Exception:
                 pass

        # 4. Construct History for LLM
        # For proactive tasks, we treat the "Prompt" as a User message to trigger the response
        gemini_history = [
            {"role": "user", "parts": [full_system_block]},
            {"role": "model", "parts": ["System ready."]},
            {"role": "user", "parts": [prompt]}
        ]

        # 5. Generate
        try:
            google_api_key = get_credential("GOOGLE_API_KEY")
            genai.configure(api_key=google_api_key)
            model = genai.GenerativeModel(model_id)
            
            # Simple generation without tools loop for now, as briefing is mostly text generation from context
            response = await model.generate_content_async(gemini_history)
            
            if response.text:
                # Save only the assistant output to history?
                # Usually proactive messages are sent to Telegram, so we might want to log them.
                save_message(session_id, "assistant", response.text)
                return response.text
                
            return "Error: No response generated."
            
        except Exception as e:
            logger.error(f"Proactive gen error: {e}")
            return f"Error generating briefing: {e}"

    # --- Helper Methods (Internal) ---

    def _extract_user_state(self, user_input: str) -> Dict[str, str]:
        extracted: Dict[str, str] = {}
        lowered = user_input.lower()

        age_patterns = [
            r"(?:age|ålder)\s*(?:is|=|:|är)?\s*(\d{1,3})",
            r"(?:i am|jag är)\s*(\d{1,3})\s*(?:years|år)?",
        ]
        for pattern in age_patterns:
            match = re.search(pattern, lowered, re.IGNORECASE)
            if match:
                extracted["age"] = match.group(1)
                break

        max_hr_patterns = [
            r"(?:max\s*(?:hr|pulse|puls|maxpuls)|maximum\s*(?:hr|pulse|heart\s*rate))\s*(?:is|=|:|är)?\s*(\d{2,3})",
            r"(?:min\s*)?maxpuls\s*(?:är|is|=|:)?\s*(\d{2,3})",
        ]
        for pattern in max_hr_patterns:
            match = re.search(pattern, lowered, re.IGNORECASE)
            if match:
                extracted["max_hr"] = match.group(1)
                break

        weight_patterns = [
            r"(?:weight|vikt)\s*(?:is|=|:|är)?\s*(\d{2,3}(?:[\.,]\d)?)\s*(?:kg|kilo)?",
            r"(?:i weigh|jag väger|väger)\s*(\d{2,3}(?:[\.,]\d)?)\s*(?:kg|kilo)?",
        ]
        for pattern in weight_patterns:
            match = re.search(pattern, lowered, re.IGNORECASE)
            if match:
                extracted["weight"] = match.group(1).replace(",", ".")
                break

        return extracted

    def _detect_requested_profile_field(self, assistant_text: str) -> Optional[str]:
        lowered = assistant_text.lower()
        if any(token in lowered for token in ["ålder", "age"]):
            return "age"
        if any(token in lowered for token in ["maxpuls", "max pulse", "max hr", "maximum heart rate"]):
            return "max_hr"
        if any(token in lowered for token in ["vikt", "weight"]):
            return "weight"
        return None

    def _extract_numeric_fallback(self, user_input: str, field: str) -> Optional[str]:
        match = re.search(r"(\d{1,3}(?:[\.,]\d)?)", user_input)
        if not match:
            return None

        value = match.group(1).replace(",", ".")
        if field in {"age", "max_hr"}:
            value = str(int(float(value)))
        return value

    def _build_user_state_context(self, user_state: Dict[str, str]) -> str:
        if not user_state:
            return "No known user profile values in memory yet."

        lines = []
        if user_state.get("age"):
            lines.append(f"- age: {user_state['age']}")
        if user_state.get("max_hr"):
            lines.append(f"- max_hr: {user_state['max_hr']}")
        if user_state.get("weight"):
            lines.append(f"- weight_kg: {user_state['weight']}")

        return "\n".join(lines) if lines else "No known user profile values in memory yet."

# Singleton instance
shared_chat_service = UnifiedChatService()
