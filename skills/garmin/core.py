
import logging
import datetime
from skills.garmin.client import GarminClient

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

    def get_health_report(self, target_date=None):
        if not self.client or not self.client.is_authenticated:
            try:
                if self.client:
                    self.client.login()
                else:
                    self.client = GarminClient.from_credentials()
            except Exception as e:
                return {"error": f"Not logged in to Garmin. {e}"}

        try:
            today = target_date or datetime.date.today()
            logger.info(f"[GARMIN] Fetching ALL data for: {today}")
            
            # Fetch data using new extractors
            # 1. Daily Summary
            daily = self.client.get_daily_summary(today)
            
            # 2. Sleep (for last night)
            sleep = self.client.get_sleep(today)
            
            # 3. Stress & Body Battery
            stress = self.client.get_stress(today)
            
            # 4. Body Battery
            bb_data = self.client.get_body_battery(today)

            if not daily:
                 # If no data and we haven't tried yesterday, try yesterday
                 if not target_date:
                     yesterday = today - datetime.timedelta(days=1)
                     logger.info(f"[GARMIN] No data for today, falling back to yesterday: {yesterday}")
                     return self.get_health_report(target_date=yesterday)
                 return {"error": "No data from Garmin (sync your watch)."}

            # --- PROCESS DATA ---
            
            # Sleep Formatting
            sleep_str = "0h 0m"
            rem_str = "0.0h"
            deep_str = "0h"
            light_str = "0h"
            awake_str = "0h"
            sleep_score = "N/A"
            start_time = "N/A"
            end_time = "N/A"
            
            if sleep:
                total_hours = sleep.total_sleep_hours or 0
                sleep_str = f"{int(total_hours)}h {int((total_hours % 1) * 60)}m"
                rem_str = f"{sleep.rem_sleep_hours or 0:.1f}h"
                deep_str = f"{sleep.deep_sleep_hours or 0:.1f}h"
                light_str = f"{sleep.light_sleep_hours or 0:.1f}h"
                awake_str = f"{sleep.awake_sleep_hours or 0:.1f}h"
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
                     values = [pair[1] for pair in bb_data['bodyBatteryValuesArray'] if pair and len(pair) > 1 and pair[1] is not None]
                 
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
                "is_today": today == datetime.date.today(),
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

            # Final Fallback check: If steps=0 and sleep=0, we might want yesterday's data anyway
            # only if we are currently looking at today
            if not target_date and data["steps"] == 0 and data["sleep_hours"] == "0h 0m":
                 yesterday = today - datetime.timedelta(days=1)
                 logger.info(f"[GARMIN] Today's data is empty, falling back to yesterday: {yesterday}")
                 return self.get_health_report(target_date=yesterday)
            
            return data

        except Exception as e:
            logger.error(f"[GARMIN] Fetch Error: {e}")
            return {"error": f"System error: {e}"}

    def get_advanced_report(self, target_date=None) -> dict:
        """
        Fetch all advanced metrics for a given date.
        Formats the raw API data into simpler, LLM-friendly dicts.
        """
        if not self.client or not self.client.is_authenticated:
            try:
                if self.client:
                    self.client.login()
                else:
                    self.client = GarminClient.from_credentials()
            except Exception as e:
                return {"error": f"Not logged in to Garmin. {e}"}

        today = target_date or datetime.date.today()
        logger.info(f"[GARMIN] Fetching advanced metrics for: {today}")

        report = {"date": str(today)}

        # Training Readiness
        try:
            tr_raw = self.client.get_training_readiness(today)
            if tr_raw:
                report["training_readiness"] = {
                    "score": tr_raw.get("trainingReadinessScore"),
                    "level": tr_raw.get("trainingReadinessText", {}).get("text")
                }
        except Exception as e:
            logger.warning(f"[GARMIN] training_readiness failed: {e}")

        # Training Status
        try:
            ts_raw = self.client.get_training_status(today)
            if ts_raw:
                report["training_status"] = {
                    "status": ts_raw.get("trainingStatus"),
                    "weekly_load": ts_raw.get("weeklyTrainingLoad"),
                    "acwr_percent": ts_raw.get("acwrPercent")
                }
        except Exception as e:
            logger.warning(f"[GARMIN] training_status failed: {e}")

        # Race Predictions
        try:
            rp_raw = self.client.get_race_predictions(today)
            if rp_raw:
                report["race_predictions"] = {
                    "5k_seconds": rp_raw.get("time5K"),
                    "10k_seconds": rp_raw.get("time10K"),
                    "half_marathon_seconds": rp_raw.get("timeHalfMarathon"),
                    "marathon_seconds": rp_raw.get("timeMarathon")
                }
        except Exception as e:
            logger.warning(f"[GARMIN] race_predictions failed: {e}")

        # VO2 Max
        try:
            vo2_raw = self.client.get_vo2_max(today)
            if vo2_raw and isinstance(vo2_raw, list) and len(vo2_raw) > 0:
                vo2_data = vo2_raw[0]
                report["vo2_max"] = {
                    "running": vo2_data.get("vo2MaxCategory", {}).get("generic", {}).get("vo2Max"),
                    "cycling": vo2_data.get("vo2MaxCategory", {}).get("cycling", {}).get("vo2Max")
                }
        except Exception as e:
            logger.warning(f"[GARMIN] vo2_max failed: {e}")

        # Endurance Score
        try:
            end_raw = self.client.get_endurance_score(today)
            if end_raw:
                report["endurance_score"] = end_raw.get("overallScore")
        except Exception as e:
            logger.warning(f"[GARMIN] endurance_score failed: {e}")

        # Hill Score
        try:
            hill_raw = self.client.get_hill_score(today)
            if hill_raw:
                report["hill_score"] = {
                    "overall": hill_raw.get("overallScore"),
                    "strength": hill_raw.get("strengthScore"),
                    "endurance": hill_raw.get("enduranceScore")
                }
        except Exception as e:
            logger.warning(f"[GARMIN] hill_score failed: {e}")

        # Fitness Age
        try:
            fa_raw = self.client.get_fitness_age(today)
            if fa_raw:
                report["fitness_age"] = {
                    "fitness_age": fa_raw.get("fitnessAge"),
                    "chronological_age": fa_raw.get("chronologicalAge"),
                    "achievable_fitness_age": fa_raw.get("achievableFitnessAge")
                }
        except Exception as e:
            logger.warning(f"[GARMIN] fitness_age failed: {e}")

        # HRV
        try:
            hrv_raw = self.client.get_hrv_data(today)
            if hrv_raw:
                report["hrv"] = {
                    "last_night_ms": hrv_raw.get("lastNightAvg"),
                    "weekly_avg_ms": hrv_raw.get("weeklyAvg"),
                    "status": hrv_raw.get("status")
                }
        except Exception as e:
            logger.warning(f"[GARMIN] hrv_data failed: {e}")

        # Hydration
        try:
            hyd_raw = self.client.get_hydration(today)
            if hyd_raw:
                report["hydration"] = {
                    "ml_consumed": hyd_raw.get("valueInML"),
                    "ml_goal": hyd_raw.get("goalInML")
                }
        except Exception as e:
            logger.warning(f"[GARMIN] hydration failed: {e}")

        # SpO2
        try:
            spo2_raw = self.client.get_spo2(today)
            if spo2_raw:
                report["spo2"] = {"data_present": True}  # Often complex list, simplify for LLM
        except Exception as e:
            logger.warning(f"[GARMIN] spo2 failed: {e}")

        # Respiration (This was the problematic one)
        try:
            resp_raw = self.client.get_respiration(today)
            if resp_raw and isinstance(resp_raw, dict):
                arrays = resp_raw.get("respirationAveragesArray") or resp_raw.get("respirationAveragesValuesArray")
                if arrays:
                    # Array format: [timestamp, average_value, high_value, low_value]
                    total_avg = sum(item[1] for item in arrays if len(item) > 1 and item[1]) / len(arrays)
                    report["respiration"] = f"Genomsnittlig andningsfrekvens: {total_avg:.1f} andetag/minut"
                else:
                    # Still dump out the dict structure so it doesn't fail, but keep it small
                    report["respiration"] = "Andningsdata tillgänglig men snittvärdet saknas i Garmins data"
            else:
                report["respiration"] = None
        except Exception as e:
            logger.warning(f"[GARMIN] respiration failed: {e}")
            report["respiration"] = None

        # Personal Records
        try:
            pr_raw = self.client.get_personal_records()
            if pr_raw:
                 report["personal_records_count"] = len(pr_raw) if isinstance(pr_raw, list) else 1
        except Exception as e:
            logger.warning(f"[GARMIN] personal_records failed: {e}")

        logger.info(f"[GARMIN] Advanced report complete for {today}")
        return report

