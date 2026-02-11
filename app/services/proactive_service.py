import asyncio
from app.core.logging import logger
from app.core.config import settings

class ProactiveService:
    def __init__(self, sio):
        self.sio = sio
        self.running = False
        self.task = None

    async def start(self):
        if self.running:
            return
        self.running = True
        logger.info("Proactive Service Started")
        self.task = asyncio.create_task(self._loop())

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Proactive Service Stopped")

    async def _loop(self):
        last_briefing_date = None
        
        while self.running:
            try:
                import datetime
                
                now = datetime.datetime.now()
                today = now.date()
                
                # --- MORNING BRIEFING (08:00) ---
                target_hour = 8
                run_window_minutes = 5
                
                # Trigger once per day inside a short morning window.
                # This avoids missing the run if the event loop is delayed
                # and prevents duplicate sends on the same day.
                should_send_briefing = (
                    now.hour == target_hour
                    and now.minute < run_window_minutes
                    and last_briefing_date != today
                )

                if should_send_briefing:
                    last_briefing_date = today
                    await self.send_morning_briefing()

                # Sleep (check every 30s to be precise enough)
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Proactive Service Error: {e}")
                await asyncio.sleep(60)

    async def send_morning_briefing(self):
        """Generates and sends the daily morning briefing."""
        logger.info("🕒 Generating Morning Briefing...")
        
        try:
            import datetime
            import json
            from app.services.telegram_service import telegram_service
            from app.core.dependencies import get_garmin
            from app.tools.weather_core import get_weather
            from app.services.llm_handler import stream_gemini
            from app.core.config import get_credential
            
            if not telegram_service or not telegram_service.chat_id:
                logger.warning("Morning Briefing skipped: Telegram not configured.")
                return

            # 1. Gather Context
            context_parts = []
            
            # Weather
            try:
                weather = await get_weather()
                context_parts.append(f"VÄDER:\n{weather}")
            except Exception as e:
                logger.error(f"Weather error: {e}")

            # Garmin
            try:
                garmin = get_garmin()
                if garmin:
                    health = garmin.get_health_report()
                    if health and not health.get('error'):
                        context_parts.append(f"HÄLSA (Garmin):\n{json.dumps(health, ensure_ascii=False)}")
                    else:
                        context_parts.append(f"HÄLSA (Garmin): Kunde inte hämta data ({health.get('error')})")
                else:
                    context_parts.append("HÄLSA (Garmin): Tjänst ej initierad")
            except Exception as e:
                logger.error(f"Garmin proactive error: {e}")
            
            # Compile Prompt
            context = "\n\n".join(context_parts)
            current_time_str = datetime.datetime.now().strftime("%H:%M")
            
            # Fetch prompt from DB
            from app.core.database import get_db_prompts
            prompts = get_db_prompts()
            prompt_template = prompts.get("MORNING_BRIEFING_PROMPT", 
                "Du är Freja. Klockan är {time}. Ge en morgonbriefing baserat på:\n{context}\n\nVIKTIGT: Inkludera detaljerad sömnanalys (REM, djup, vaken, start/stopp-tider) och vilopuls.")
                
            prompt = prompt_template.replace("{time}", current_time_str).replace("{context}", context)
            
            # Generate Response
            model_id = get_credential("SELECTED_MODEL") or "gemini-2.0-flash"
            full_response = ""
            async for chunk in stream_gemini(model_id, [], prompt):
                full_response += chunk
                
            # Send via Telegram (only to primary user)
            if full_response:
                target_chat = telegram_service.primary_chat_id
                if target_chat:
                    await telegram_service.send_message(f"🌅 **Morgonbriefing**\n\n{full_response}", chat_id=target_chat)
                    logger.info(f"Morning Briefing sent to {target_chat}")
                else:
                    logger.warning("Morning Briefing skipped: No primary chat ID found.")
                
        except Exception as e:
            logger.error(f"Error sending morning briefing: {e}")
    
    async def trigger_briefing(self):
        """Manually trigger the briefing for testing."""
        await self.send_morning_briefing()

proactive_service = None

def init_proactive_service(sio):
    global proactive_service
    proactive_service = ProactiveService(sio)
    return proactive_service
