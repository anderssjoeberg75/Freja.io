import asyncio
import base64
import json
import logging
import re
from typing import Dict, List, Optional, Any

from google import genai
from google.genai import types

from app.core.config import get_credential, settings
from app.core.database import get_history, get_user_state, save_message, save_user_state
from app.core.dependencies import get_code_executor, get_garmin, get_strava, get_withings
from app.core.prompts import get_system_prompt
from app.self_improving.hooks import handle_user_prompt_submit
from app.services.web_fallback_service import WebFallbackService, needs_web_fallback
from skills.homeassistant import get_homeassistant_command_processor
# --- Native Tooling Imports ---
from app.services.tool_registry import registry
from app.services.llm_providers.ollama import generate_ollama_response

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
            await save_message(session_id, "user", user_msg)
            await save_message(session_id, "assistant", ha_result.response)
            return ha_result.response

        # 3. Logic Hook (Self-improving)
        handle_user_prompt_submit(user_msg, project_root=".")

        # 3. User State & Profile Memory
        # Profile is now updated by the LLM calling `update_user_profile_impl` natively
        user_state = await get_user_state(session_id)

        # 4. Build Context (System Prompt + Profile)
        system_prompt = await get_system_prompt()
        
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
        user_id = get_credential("USER_NAME") or settings.USER_NAME or settings.USER_ID
        
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
        db_history = await get_history(session_id=session_id, limit=10)
        
        gemini_history = []

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

        # 7. Route to appropriate backend
        if not model_id.startswith("gemini"):
            # Assume Ollama for non-gemini models
            try:
                # We pass the constructed history (mapped for Gemini) to the helper, 
                # which will re-map it for Ollama.
                # Ideally we should have a generic history format, but for now we convert.
                final_text_response = await generate_ollama_response(
                    model_id=model_id,
                    system_prompt=full_system_block,
                    history=gemini_history[:-1], # Exclude current message which is handled separately
                    user_msg=user_msg,
                    image_data=image_data
                )
                
                await save_message(session_id, "user", user_msg)
                await save_message(session_id, "assistant", final_text_response)
                return final_text_response
                
            except Exception as e:
                logger.error(f"Ollama routing error: {e}")
                return f"Error: {str(e)}"

        # 8. Call Gemini with Tool Loop
        try:
            google_api_key = get_credential("GOOGLE_API_KEY")
            if not google_api_key:
                return "Error: GOOGLE_API_KEY is missing."

            client = genai.Client(api_key=google_api_key)
            tools_def = registry.get_gemini_function_declarations()
            config = types.GenerateContentConfig(
                system_instruction=full_system_block,
                tools=[{"function_declarations": tools_def}],
            )
            history = [
                types.Content(
                    role=("user" if msg["role"] == "user" else "model"),
                    parts=[types.Part(text=msg["content"])],
                )
                for msg in db_history
            ]
            chat = client.aio.chats.create(model=model_id, config=config, history=history)
            current_message_parts: list[types.Part] = [types.Part(text=user_msg)]
            if image_data:
                try:
                    b64_data = image_data.split(",", 1)[1] if "," in image_data else image_data
                    current_message_parts.append(types.Part.from_bytes(data=base64.b64decode(b64_data), mime_type="image/jpeg"))
                except Exception as exc:
                    logger.error(f"Image decode error: {exc}")
            
            # --- TOOL EXECUTION LOOP ---
            max_turns = 5
            final_text_response = ""
            
            for _ in range(max_turns):
                response = await chat.send_message(current_message_parts)
                
                if not response.candidates:
                    return "Error: AI returned no candidates."
                
                candidate = response.candidates[0]
                
                # Check for Function Calls
                function_calls = []
                for part in (candidate.content.parts or []):
                    if getattr(part, "function_call", None):
                        function_calls.append(part.function_call)
                
                if function_calls:
                    # Execute all function calls
                    next_parts: list[types.Part] = []
                    for fc in function_calls:
                        fname = fc.name
                        fargs = dict(fc.args)
                        
                        logger.info(f"AI requesting tool: {fname}({fargs})")
                        
                        # Execute Tool
                        result_text = await registry.execute(fname, fargs)
                        
                        # --- POINT 3: ENHANCED TOOL REFLECTION ---
                        # If the result looks like an error, give the AI a hint to reflect/retry
                        if isinstance(result_text, str) and ("Error" in result_text or "Fel" in result_text or "not found" in result_text.lower()):
                            result_text = (
                                f"{result_text}\n\n"
                                "[SYSTEM HINT]: The tool returned an error. Please analyze if you used the correct "
                                "arguments or if an alternative tool should be used. You can try a different approach "
                                "or explain the specific obstacle to the user."
                            )
                            # Ensure we don't count an error turn as a final turn if we want it to reflect
                            if _ == max_turns - 1:
                                max_turns += 1

                        next_parts.append(
                            types.Part(
                                function_response=types.FunctionResponse(
                                    name=fname,
                                    response={"result": result_text},
                                    id=getattr(fc, "id", None),
                                )
                            )
                        )
                    
                    current_message_parts = next_parts
                    continue
                
                # No function calls -> Final Response
                final_text_response = response.text or ""
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
            await save_message(session_id, "user", user_msg)
            await save_message(session_id, "assistant", final_text_response)

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
        system_prompt = await get_system_prompt()
        user_state = await get_user_state(session_id)
        
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
        if mem0_key and len(mem0_key) > 5:
             try:
                from mem0 import AsyncMemoryClient
                mem0 = AsyncMemoryClient(api_key=mem0_key)
                # Search for general preferences or goals
                relevant = await mem0.search("My daily goals and preferences", user_id=(get_credential("USER_NAME") or settings.USER_NAME or settings.USER_ID))
                # handle both dict-based results (from some mem0 versions) and objects
                mem_text = ""
                for m in relevant:
                    if isinstance(m, dict) and 'memory' in m:
                        mem_text += f"- {m['memory']}\n"
                    elif hasattr(m, 'memory'):
                        mem_text += f"- {m.memory}\n"
                        
                if mem_text:
                    full_system_block += f"\n\n--- LONG TERM MEMORY ---\n{mem_text}"
             except Exception as exc:
                 logger.warning(f"Mem0 proactive search failed (continuing without memory): {exc}")

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
            if not google_api_key:
                return "Error generating briefing: GOOGLE_API_KEY is missing"

            client = genai.Client(api_key=google_api_key)
            response = await client.aio.models.generate_content(
                model=model_id,
                contents=gemini_history,
            )
            
            # Secure text extraction (Google GenAI throws exceptions on BLOCKED content if accessing .text directly)
            try:
                output_text = response.text
            except ValueError:
                if response.candidates and response.candidates[0].finish_reason:
                    output_text = f"Content blocked due to: {response.candidates[0].finish_reason.name}"
                else:
                    output_text = "Error: Blocked or unparseable text format."
            
            if output_text:
                await save_message(session_id, "assistant", output_text)
                return output_text
                
            return "Error: No response generated."
            
        except Exception as e:
            logger.error(f"Proactive gen error: {e}")
            return f"Error generating briefing: {e}"

    # Regex manual profile extraction was removed in favor of tool calling.

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
