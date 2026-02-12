from google import genai
from google.genai import types
from app.core.config import settings
from app.core.logging import logger
from app.services.tool_registry import registry
import base64

class LLMService:
    def __init__(self):
        self.gemini_client = None
        if settings.GOOGLE_API_KEY:
            self.gemini_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            logger.info("Gemini Client Initialized")
        else:
            logger.warning("GOOGLE_API_KEY not found. LLM capabilities limited.")

    async def generate_response(self, prompt: str, image_data: str = None, history: list | None = None):
        """
        Generates a streaming response from Gemini.
        """
        if not self.gemini_client:
            yield "Mainframe Error: LLM Offline (No API Key)"
            return

        model_id = "gemini-2.0-flash" 
        
        history = history or []
        contents = []
        # Add history
        # TODO: Format history correctly for Gemini 2.0
        
        # Current message
        parts = [types.Part(text=prompt)]
        
        if image_data:
            try:
                # Assuming base64 data url or raw base64
                if "," in image_data:
                    image_data = image_data.split(",")[1]
                
                img_bytes = base64.b64decode(image_data)
                parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
            except Exception as e:
                logger.error(f"Image decode error: {e}")

        contents.append(types.Content(role="user", parts=parts))

        try:
            # Config with Tools
            # tools_def = registry.get_definitions()
            
            response_stream = self.gemini_client.models.generate_content_stream(
                model=model_id,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.7
                )
            )

            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            yield f"Error: {str(e)}"

llm_service = LLMService()
