import asyncio
<<<<<<< HEAD
from app.core.logging import logger
from app.core.config import settings
=======
import pytz
from app.core.logging import logger
from app.core.config import settings, get_credential
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)


class ProactiveService:
    def __init__(self, sio):
        self.sio = sio
        self.running = False
        self.task = None

    async def start(self):
        if self.running:
            return
        self.running = True
        logger.info("Proactive service started")
        self.task = asyncio.create_task(self._loop())

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Proactive service stopped")

    async def _loop(self):
        last_briefing_date = None
<<<<<<< HEAD
=======
        last_audit_date = None
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)

        while self.running:
            try:
                import datetime

<<<<<<< HEAD
                now = datetime.datetime.now()
                today = now.date()

                # --- Morning briefing schedule (08:00 local time) ---
                target_hour = 8
                catch_up_window_minutes = 180
=======
                tz_name = settings.TIMEZONE
                try:
                    tz = pytz.timezone(tz_name)
                except Exception:
                    tz = pytz.UTC
                
                now = datetime.datetime.now(tz)
                today = now.date()

                # --- Morning briefing schedule (07:00 local time) ---
                target_hour = 7
                catch_up_window_minutes = 180
                
                # Use local hour for calculation
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
                minutes_since_target = ((now.hour * 60) + now.minute) - (target_hour * 60)

                # Send once per day after 08:00 with a catch-up window.
                # This avoids missed runs if startup or event-loop timing is delayed.
                should_send_briefing = (
                    last_briefing_date != today
                    and 0 <= minutes_since_target < catch_up_window_minutes
                )

                if should_send_briefing:
                    last_briefing_date = today
                    await self.send_morning_briefing()

<<<<<<< HEAD
=======
                # --- Daily Audit (12:00 local time) ---
                audit_target_hour = 12
                # 3 hour window to catch missed runs
                audit_window_minutes = 180
                
                minutes_since_audit = ((now.hour * 60) + now.minute) - (audit_target_hour * 60)
                
                should_run_audit = (
                    last_audit_date != today
                    and 0 <= minutes_since_audit < audit_window_minutes
                )
                
                if should_run_audit:
                    last_audit_date = today
                    await self.run_daily_audit()

>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
                # Check frequently enough to avoid timing gaps.
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Proactive service error: {e}")
                await asyncio.sleep(60)

<<<<<<< HEAD
=======
    async def run_daily_audit(self):
        """Run the daily code audit."""
        logger.info("Starting scheduled daily code audit...")
        try:
            # Import here to avoid circular dependencies
            from skills.codex.tools import audit_code_impl
            
            # This function handles its own Telegram notification
            result = await audit_code_impl()
            logger.info(f"Daily audit completed: {result[:100]}...")
            
        except Exception as e:
            logger.error(f"Daily audit failed: {e}")

>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
    async def send_morning_briefing(self):
        """Generate and send the daily morning briefing."""
        logger.info("Generating morning briefing")

        try:
            import datetime
            import json
            from app.services.telegram_service import telegram_service
            from app.core.dependencies import get_garmin
            from app.tools.weather_core import get_weather
            from app.tools.weather_core import get_weather
            # from app.services.llm_handler import stream_gemini # REMOVED
            from app.core.config import get_credential
<<<<<<< HEAD
            from app.core.config import get_credential
            from app.core.dependencies import get_strava  # Added Strava dependency
=======
            from app.core.dependencies import get_strava, get_withings  # Added Strava and Withings dependencies
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)

            if not telegram_service or not telegram_service.primary_chat_id:
                logger.warning("Morning briefing skipped: Telegram is not configured")
                return

            # 1) Gather context
            context_parts = []

            # Weather
            try:
                weather = await get_weather()
                context_parts.append(f"WEATHER:\n{weather}")
            except Exception as e:
                logger.error(f"Weather error: {e}")

            # Garmin
            try:
                garmin = get_garmin()
                if garmin:
                    health = garmin.get_health_report()
                    if health and not health.get("error"):
                        context_parts.append(f"HEALTH (Garmin):\n{json.dumps(health, ensure_ascii=False)}")
                    else:
                        context_parts.append(
                            f"HEALTH (Garmin): Could not fetch data ({health.get('error')})"
                        )
                else:
                    context_parts.append("HEALTH (Garmin): Service not initialized")
            except Exception as e:
                logger.error(f"Garmin proactive error: {e}")

            # Strava (Added)
            try:
                strava = get_strava()
                if strava:
<<<<<<< HEAD
                    # Fetch recent activities (last 5)
                    activities = await strava.get_health_report(limit=5)
=======
                    # Fetch recent activities (increased to 30 to cover ~7-14 days)
                    activities = await strava.get_health_report(limit=30)
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
                    if activities and "error" not in activities: # Check for error key if get_activities returns dict on error, or just list
                         # Simple formatting for context
                         activity_summary = json.dumps(activities, ensure_ascii=False)
                         context_parts.append(f"RECENT TRAINING (Strava):\n{activity_summary}")
                    else:
                         context_parts.append("RECENT TRAINING (Strava): Could not fetch recent activities.")
                else:
                    context_parts.append("RECENT TRAINING (Strava): Service not initialized")
            except Exception as e:
                logger.error(f"Strava proactive error: {e}")

<<<<<<< HEAD
            # Build prompt
            context = "\n\n".join(context_parts)
            current_time_str = datetime.datetime.now().strftime("%H:%M")
=======
            # Withings (Added)
            try:
                withings = get_withings()
                if withings:
                    health = withings.get_health_report()
                    if health and isinstance(health, dict) and "error" not in health:
                        context_parts.append(f"BODY COMPOSITION (Withings):\n{json.dumps(health, ensure_ascii=False)}")
                    elif isinstance(health, str):
                         context_parts.append(f"BODY COMPOSITION (Withings): {health}")
                else:
                    context_parts.append("BODY COMPOSITION (Withings): Service not initialized")
            except Exception as e:
                logger.error(f"Withings proactive error: {e}")

            # Build prompt
            context = "\n\n".join(context_parts)
            
            tz_name = settings.TIMEZONE
            try:
                tz = pytz.timezone(tz_name)
            except Exception:
                tz = pytz.UTC
            
            now_local = datetime.datetime.now(tz)
            current_time_str = now_local.strftime("%H:%M")
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)

            from app.core.database import get_db_prompts

            prompts = get_db_prompts()
            prompt_template = prompts.get(
                "MORNING_BRIEFING_PROMPT",
                (
                    "You are Freja. Current time is {time}. "
                    "Create a morning briefing in Swedish based on:\n{context}\n\n"
                    "IMPORTANT: You must include a specific section titled '🚴 Dagens Träningsråd'. "
                    "In this section, explicitly recommend a workout for today based on my recovery (Garmin Body Battery/Sleep) "
                    "and recent training load (Strava). "
                    "Examples: 'Idag har du fullt batteri (83), så kör ett hårt intervallpass!' or 'Du sov dåligt, ta en promenad.'. "
                    "Do not just summarize what I did previously, tell me what to do TODAY."
                ),
            )

            prompt = prompt_template.replace("{time}", current_time_str).replace("{context}", context)

            # Generate response
            from app.services.chat_service import shared_chat_service
            
            # Using Unified Chat Service for generation (includes MEM0 and proper config)
            # Use 'proactive_morning' as session_id for MEM0 context separation if needed, 
            # or use user_id to share context. Let's use a specific session ID.
            session_id = f"proactive_morning_{datetime.date.today()}"
            
            full_response = await shared_chat_service.run_proactive_task(session_id, prompt)

            # Send via Telegram (primary user only)
            if full_response:
                target_chat = telegram_service.primary_chat_id
                if target_chat:
                    await telegram_service.send_message(
                        f"🌅 **Morning Briefing**\n\n{full_response}", chat_id=target_chat
                    )
                    logger.info(f"Morning briefing sent to {target_chat}")
                else:
                    logger.warning("Morning briefing skipped: No primary chat ID found")

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
