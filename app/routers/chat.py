from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Optional
import google.generativeai as genai
import asyncio
import base64
import json
import logging
import re
from app.core.database import get_history, get_user_state, save_message, save_user_state
from app.core.prompts import get_system_prompt
from app.core.dependencies import get_garmin, get_strava, get_code_executor
from app.core.config import get_credential

logger = logging.getLogger(__name__)

router = APIRouter()


async def process_code_execution_tags(text: str) -> str:
    """Process [EXEC_CODE:language]code[/EXEC_CODE] tags in AI response."""
    code_executor = get_code_executor()
    if not code_executor:
        return text

    pattern = r"\[EXEC_CODE:(\w+)\](.*?)\[/EXEC_CODE\]"

    def replace_code_tag(match):
        language = match.group(1)
        code = match.group(2).strip()

        try:
            if language == "python":
                result = code_executor.run_code(code, "python")
            elif language in ["bash", "shell", "sh"]:
                result = code_executor.run_command(code)
            else:
                return f"\n**[Error: Language '{language}' is not supported]**\n"

            output = result.get("output", "")
            error = result.get("error", "")

            if error:
                return f"\n**Code execution (Docker):**\n```{language}\n{code}\n```\n**Error:**\n```\n{error}\n```\n"

            return f"\n**Code execution (Docker):**\n```{language}\n{code}\n```\n**Result:**\n```\n{output}\n```\n"
        except Exception as exc:
            logger.error(f"Code execution error: {exc}")
            return f"\n**[Code execution error: {str(exc)}]**\n"

    return re.sub(pattern, replace_code_tag, text, flags=re.DOTALL)


def extract_user_state(user_input: str) -> Dict[str, str]:
    """Extract profile values from free-form text with lightweight regexes."""
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


def detect_requested_profile_field(assistant_text: str) -> Optional[str]:
    """Find which profile field the assistant asked for most recently."""
    lowered = assistant_text.lower()
    if any(token in lowered for token in ["ålder", "age"]):
        return "age"
    if any(token in lowered for token in ["maxpuls", "max pulse", "max hr", "maximum heart rate"]):
        return "max_hr"
    if any(token in lowered for token in ["vikt", "weight"]):
        return "weight"
    return None


def extract_numeric_fallback(user_input: str, field: str) -> Optional[str]:
    """Fallback extraction for short direct answers like '42' after a model question."""
    match = re.search(r"(\d{1,3}(?:[\.,]\d)?)", user_input)
    if not match:
        return None

    value = match.group(1).replace(",", ".")
    if field in {"age", "max_hr"}:
        value = str(int(float(value)))
    return value


def is_calculation_request(user_input: str) -> bool:
    """Detect if user asks for calculations where profile memory should be injected."""
    lowered = user_input.lower()
    markers = [
        "maf",
        "calculate",
        "beräkna",
        "zone",
        "zon",
        "maxpuls",
        "max pulse",
        "heart rate",
        "puls",
    ]
    return any(marker in lowered for marker in markers)


def build_user_state_context(user_state: Dict[str, str]) -> str:
    """Build a stable prompt block with remembered user profile values."""
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


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    session_id: str = "default"
    image: Optional[str] = None  # Base64 image data


@router.post("/api/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint with state extraction and context injection."""
    session_id = request.session_id
    model_id = request.model
    messages = request.messages
    image_data = request.image

    logger.info(f"Chat request [{model_id}]: {len(messages)} messages")

    if messages and messages[-1].role == "user":
        user_msg = messages[-1].content
    else:
        user_msg = "..."

    user_state = get_user_state(session_id)
    extracted_now = extract_user_state(user_msg)
    if extracted_now:
        user_state.update(extracted_now)
        save_user_state(session_id, extracted_now)

    recent_history = get_history(session_id=session_id, limit=4)
    if recent_history:
        last_assistant = next((item for item in reversed(recent_history) if item["role"] == "assistant"), None)
        if last_assistant:
            requested_field = detect_requested_profile_field(last_assistant["content"])
            if requested_field and not extracted_now.get(requested_field):
                fallback_value = extract_numeric_fallback(user_msg, requested_field)
                if fallback_value:
                    user_state[requested_field] = fallback_value
                    save_user_state(session_id, {requested_field: fallback_value})

    gemini_history = []
    system_prompt = get_system_prompt()

    context_parts = []

    logger.info("Attempting to fetch Garmin data for context")
    garmin_tool = get_garmin()
    if garmin_tool:
        try:
            health_data = garmin_tool.get_health_report()
            if health_data and not health_data.get("error"):
                context_parts.append(f"GARMIN DATA:\n{json.dumps(health_data, indent=2, ensure_ascii=False)}")
            else:
                logger.info(f"Garmin context empty or error: {health_data}")
        except Exception as exc:
            logger.warning(f"Garmin fetch exception: {exc}")
    else:
        logger.info("Garmin tool is not initialized")

    strava_tool = get_strava()
    if strava_tool and hasattr(strava_tool, "cached_data") and strava_tool.cached_data:
        context_parts.append(f"STRAVA DATA:\n{json.dumps(strava_tool.cached_data, indent=2, ensure_ascii=False)}")

    user_state_context = build_user_state_context(user_state)
    state_instructions = (
        "USER PROFILE MEMORY (persisted across turns):\n"
        f"{user_state_context}\n\n"
        "Use these values for calculations when missing from the latest user message. "
        "Only ask for missing fields."
    )

    if context_parts:
        realtime_context = "\n\n".join(context_parts)
        gemini_history.append(
            {
                "role": "user",
                "parts": [f"{system_prompt}\n\n{state_instructions}\n\nREALTIME DATA:\n{realtime_context}"],
            }
        )
        gemini_history.append({"role": "model", "parts": ["Jag har tagit emot kontexten och är redo att hjälpa till."]})
    else:
        gemini_history.append({"role": "user", "parts": [f"{system_prompt}\n\n{state_instructions}"]})
        gemini_history.append({"role": "model", "parts": ["Jag har tagit emot kontexten och är redo att hjälpa till."]})

    augmented_last_user_msg = user_msg
    if is_calculation_request(user_msg):
        memory_snapshot = build_user_state_context(user_state)
        augmented_last_user_msg = (
            f"{user_msg}\n\n[Memory context for calculations]\n{memory_snapshot}"
        )

    for msg in messages:
        role = "user" if msg.role == "user" else "model"
        content_to_send = augmented_last_user_msg if msg == messages[-1] and role == "user" else msg.content

        if role == "user" and image_data and msg == messages[-1]:
            try:
                b64_data = image_data.split(",", 1)[1] if "," in image_data else image_data
                img_bytes = base64.b64decode(b64_data)
                gemini_history.append(
                    {
                        "role": role,
                        "parts": [
                            content_to_send,
                            {"mime_type": "image/jpeg", "data": img_bytes},
                        ],
                    }
                )
                logger.info("Image attached to request")
            except Exception as exc:
                logger.error(f"Image decode error: {exc}")
                gemini_history.append({"role": role, "parts": [content_to_send]})
        else:
            gemini_history.append({"role": role, "parts": [content_to_send]})

    try:
        google_api_key = get_credential("GOOGLE_API_KEY")
        if not google_api_key:
            return {"response": "Error: GOOGLE_API_KEY is missing."}

        genai.configure(api_key=google_api_key)

        loop = asyncio.get_event_loop()
        gmodel = genai.GenerativeModel(model_id)

        from google.generativeai.types import HarmBlockThreshold, HarmCategory

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        final_response = await loop.run_in_executor(
            None,
            lambda: gmodel.generate_content(gemini_history, safety_settings=safety_settings),
        )

        if final_response.candidates:
            candidate = final_response.candidates[0]
            finish_reason = candidate.finish_reason

            if candidate.content and candidate.content.parts:
                response_text = final_response.text
                response_text = await process_code_execution_tags(response_text)
            elif str(finish_reason) == "12" or finish_reason == 12:
                response_text = (
                    "⚠️ **Safety filter was triggered (Finish Reason: 12).**\n"
                    "I will try to continue with a safer reformulation."
                )
            else:
                response_text = f"The AI generated no text response. (Finish Reason: {finish_reason})"
        else:
            response_text = "The AI returned no candidates."

        save_message(session_id, "user", user_msg)
        save_message(session_id, "assistant", response_text)

        return {"response": response_text}

    except Exception as exc:
        logger.error(f"Chat error: {exc}", exc_info=True)
        return {"response": f"Error: {str(exc)}"}
