
import logging
import datetime
from app.tools.garmin.client import GarminClient

# Configure logger
logger = logging.getLogger(__name__)

class GarminCoach:
    def __init__(self):
        self.client = None
        try:
            # Initialize client and try to load tokens
            self.client = GarminClient()
            if self.client.auth.load_tokens():
                logger.info("[GARMIN] Client initialized with saved tokens.")
            else:
                # If no tokens, try to login with credentials
                logger.info("[GARMIN] No valid tokens found, attempting login...")
                self.client.login()
                logger.info("[GARMIN] Client initialized with fresh login.")
        except Exception as e:
             logger.warning(f"[GARMIN] Failed to initialize client: {e}")

    def get_health_report(self):
        if not self.client or not self.client.is_authenticated:
            try:
                if self.client:
                    self.client.login()
                else:
                    self.client = GarminClient.from_credentials()
            except Exception as e:
                return {"error": f"Not logged in to Garmin. {e}"}

        try:
            today = datetime.date.today()
            logger.info(f"[GARMIN] Fetching ALL data for: {today}")
            
            # Fetch data using new extractors
            # 1. Daily Summary
            daily = self.client.get_daily_summary(today)
            
            # 2. Sleep (for last night)
            sleep = self.client.get_sleep(today)
            
            # 3. Stress & Body Battery
            stress = self.client.get_stress(today)
            
            # Body Battery details might need separate fetch if not fully in stress/daily
            # The ported stress extractor's get_for_date returns StressData which has body_battery_charged/drained
            # but specific low/high/now values are often in the daily summary or body battery specific report.
            # Let's try to get more body battery details.
            bb_data = self.client.get_body_battery(today)

            if not daily:
                 return {"error": "No data from Garmin today (sync your watch)."}

            # --- PROCESS DATA ---
            
            # Sleep Formatting
            sleep_str = "0h"
            rem_str = "0h"
            deep_str = "0h"
            light_str = "0h"
            awake_str = "0h"
            sleep_score = "N/A"
            start_time = "N/A"
            end_time = "N/A"
            
            if sleep:
                sleep_str = f"{int(sleep.total_sleep_hours)}h {int((sleep.total_sleep_hours % 1) * 60)}m"
                rem_str = f"{sleep.rem_sleep_hours:.1f}h"
                deep_str = f"{sleep.deep_sleep_hours:.1f}h"
                light_str = f"{sleep.light_sleep_hours:.1f}h"
                awake_str = f"{sleep.awake_sleep_hours:.1f}h"
                sleep_score = sleep.overall_score if sleep.overall_score is not None else "N/A"
                
                # Sleep Times
                start_time = sleep.sleep_start_timestamp.strftime("%H:%M") if sleep.sleep_start_timestamp else "N/A"
                end_time = sleep.sleep_end_timestamp.strftime("%H:%M") if sleep.sleep_end_timestamp else "N/A"
            
            # Body Battery Formatting
            bb_now = "N/A"
            bb_high = "N/A"
            bb_low = "N/A"
            
            if bb_data:
                 # bb_data is a dict (raw response from bodyBattery/reports/daily)
                 # It usually contains 'bodyBatteryValuesArray'
                 values = []
                 if 'bodyBatteryValuesArray' in bb_data and bb_data['bodyBatteryValuesArray']:
                     # Format: [[ts, value], ...]
                     values = [pair[1] for pair in bb_data['bodyBatteryValuesArray'] if pair and len(pair) > 1]
                 
                 if values:
                     bb_now = values[-1]
                     bb_high = max(values)
                     bb_low = min(values)

            # Fallback for BB from daily summary if available
            if bb_high == "N/A" and daily.body_battery_highest_value is not None:
                bb_high = daily.body_battery_highest_value
            if bb_low == "N/A" and daily.body_battery_lowest_value is not None:
                bb_low = daily.body_battery_lowest_value
            if bb_now == "N/A" and daily.body_battery_most_recent_value is not None:
                bb_now = daily.body_battery_most_recent_value


            # HRV
            hrv_status = daily.hrv_status if daily.hrv_status else "N/A"

            # Compilation
            data = {
                "date": str(today),
                "steps": daily.total_steps,
                "step_goal": daily.daily_step_goal,
                "distance_km": round((daily.total_distance_meters or 0) / 1000, 2),
                
                # Heart & Stress
                "resting_heart_rate": daily.resting_heart_rate if daily.resting_heart_rate else "N/A",
                "stress_avg": daily.avg_stress_level if daily.avg_stress_level else "N/A",
                "stress_max": daily.max_stress_level if daily.max_stress_level else "N/A",
                "hrv_status": hrv_status,
                
                # Energy (Body Battery)
                "body_battery_now": bb_now,
                "body_battery_high": bb_high,
                "body_battery_low": bb_low,
                
                # Sleep
                "sleep_hours": sleep_str,
                "sleep_score": sleep_score, 
                "rem_sleep": rem_str,
                "deep_sleep": deep_str,
                "light_sleep": light_str,
                "awake_time": awake_str,
                "sleep_start": start_time,
                "sleep_end": end_time,
                
                # Calories & Activity
                "total_calories": daily.total_kilocalories,
                "intensive_minutes": (daily.moderate_intensity_minutes or 0) + ((daily.vigorous_intensity_minutes or 0) * 2),
                "spo2_avg": daily.avg_spo2_value if daily.avg_spo2_value else "N/A",
            }
            
            return data

        except Exception as e:
            logger.error(f"[GARMIN] Fetch Error: {e}")
            return {"error": f"System error: {e}"}
