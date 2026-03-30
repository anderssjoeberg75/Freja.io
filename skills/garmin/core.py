
import logging
import datetime
import time
from skills.garmin.client import GarminClient
from app.core.config import get_credential

# Configure logger
logger = logging.getLogger(__name__)


def _seconds_to_hhmmss(total_seconds):
    if total_seconds is None:
        return None
    try:
        total_seconds = int(total_seconds)
    except (TypeError, ValueError):
        return None
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

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

    def _check_fetch_limit(self):
        """Check if we have fetched data in the last 30 minutes."""
        # Use a setting for cross-instance persistence (if possible)
        # fallback to in-memory if DB is busy or not available
        last_fetch = get_credential("LAST_GARMIN_FETCH_TIMESTAMP", 0)
        try:
            last_fetch = float(last_fetch)
        except (ValueError, TypeError):
            last_fetch = 0

        now = time.time()
        elapsed = now - last_fetch
        if elapsed < 1800: # 30 minutes
            remaining = int((1800 - elapsed) / 60)
            return False, f"Garmin-data hämtades nyligen ({int(elapsed/60)} min sen). Vänta {remaining} minuter till för att undvika blockering."
        return True, None

    def _update_fetch_limit(self):
        """Update the last fetch timestamp in the database."""
        from app.core.database import save_db_setting_sync
        now = time.time()
        try:
            # We use sync version if called from executor, but since we are in a skill
            # and may be called from various places, we try to be safe.
            save_db_setting_sync("LAST_GARMIN_FETCH_TIMESTAMP", str(now))
        except Exception as e:
            logger.warning(f"[GARMIN] Could not save fetch timestamp: {e}")

    def get_health_report(self, target_date=None, enforce_fetch_limit: bool = True):
        # Enforce 30 minute limit
        if enforce_fetch_limit:
            is_ok, limit_msg = self._check_fetch_limit()
            if not is_ok:
                return {"error": limit_msg}

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
                "avg_heart_rate": daily.avg_heart_rate if daily.avg_heart_rate else "N/A",
                "min_heart_rate": daily.min_heart_rate if daily.min_heart_rate else "N/A",
                "max_heart_rate": daily.max_heart_rate if daily.max_heart_rate else "N/A",
                "stress_avg": daily.avg_stress_level if daily.avg_stress_level else "N/A",
                "stress_max": daily.max_stress_level if daily.max_stress_level else "N/A",
                "stress_duration_minutes": round((daily.stress_duration or 0) / 60),
                "rest_stress_duration_minutes": round((daily.rest_stress_duration or 0) / 60),
                "hrv_status": hrv_status,
                
                # Energy (Body Battery)
                "body_battery_now": bb_now,
                "body_battery_high": bb_high,
                "body_battery_low": bb_low,
                "body_battery_delta": (
                    (bb_high - bb_low)
                    if isinstance(bb_high, (int, float)) and isinstance(bb_low, (int, float))
                    else "N/A"
                ),
                
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
                "moderate_minutes": daily.moderate_intensity_minutes or 0,
                "vigorous_minutes": daily.vigorous_intensity_minutes or 0,
                "floors_ascended": daily.floors_ascended,
                "floors_goal": daily.floors_ascended_goal,
                "active_minutes": round((daily.active_seconds or 0) / 60),
                "highly_active_minutes": round((daily.highly_active_seconds or 0) / 60),
                "sedentary_minutes": round((daily.sedentary_seconds or 0) / 60),
                "sleeping_minutes": round((daily.sleeping_seconds or 0) / 60),
                "spo2_avg": daily.avg_spo2_value if daily.avg_spo2_value else "N/A",
                "spo2_low": daily.lowest_spo2_value if daily.lowest_spo2_value else "N/A",
                "spo2_latest": daily.latest_spo2_value if daily.latest_spo2_value else "N/A",
            }

            # Final Fallback check: If steps=0 and sleep=0, we might want yesterday's data anyway
            # only if we are currently looking at today
            # Final Fallback check: If steps=0 and sleep=0, we might want yesterday's data anyway
            # only if we are currently looking at today
            if not target_date and data["steps"] == 0 and data["sleep_hours"] == "0h 0m":
                 yesterday = today - datetime.timedelta(days=1)
                 logger.info(f"[GARMIN] Today's data is empty, falling back to yesterday: {yesterday}")
                 return self.get_health_report(target_date=yesterday)
            
            # Success! Update the limit
            if enforce_fetch_limit:
                self._update_fetch_limit()
            return data

        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                return {"error": "Garmin har tillfälligt blockerat anrop (Rate Limit). Prova igen om 15 minuter."}
            if "cooldown" in err_str:
                return {"error": "Garmin-anslutningen vilar pga tidigare blockeringsförsök. Prova igen om en stund."}
            logger.error(f"[GARMIN] Fetch Error: {e}")
            return {"error": f"Garmin-fel: {e}"}

    def get_advanced_report(self, target_date=None, enforce_fetch_limit: bool = True) -> dict:
        """
        Fetch all advanced metrics for a given date.
        Formats the raw API data into simpler, LLM-friendly dicts.
        """
        # Enforce 30 minute limit (shared with health report)
        if enforce_fetch_limit:
            is_ok, limit_msg = self._check_fetch_limit()
            if not is_ok:
                return {"error": limit_msg}

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
                    "5k_formatted": _seconds_to_hhmmss(rp_raw.get("time5K")),
                    "10k_seconds": rp_raw.get("time10K"),
                    "10k_formatted": _seconds_to_hhmmss(rp_raw.get("time10K")),
                    "half_marathon_seconds": rp_raw.get("timeHalfMarathon"),
                    "half_marathon_formatted": _seconds_to_hhmmss(rp_raw.get("timeHalfMarathon")),
                    "marathon_seconds": rp_raw.get("timeMarathon"),
                    "marathon_formatted": _seconds_to_hhmmss(rp_raw.get("timeMarathon")),
                }
        except Exception as e:
            logger.warning(f"[GARMIN] race_predictions failed: {e}")

        # VO2 Max
        try:
            vo2_raw = self.client.get_vo2_max(today)
            if vo2_raw and isinstance(vo2_raw, dict):
                report["vo2_max"] = {
                    "running": vo2_raw.get("vo2max_running"),
                    "cycling": vo2_raw.get("vo2max_cycling")
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
            if spo2_raw and isinstance(spo2_raw, dict):
                values = spo2_raw.get("spo2Values") or spo2_raw.get("spO2Readings") or []
                numeric_values = []
                for item in values:
                    if isinstance(item, list) and len(item) > 1 and isinstance(item[1], (int, float)):
                        numeric_values.append(item[1])
                    elif isinstance(item, dict):
                        val = item.get("value") or item.get("spo2")
                        if isinstance(val, (int, float)):
                            numeric_values.append(val)

                report["spo2"] = {
                    "data_present": bool(values),
                    "avg": round(sum(numeric_values) / len(numeric_values), 1) if numeric_values else None,
                    "low": min(numeric_values) if numeric_values else None,
                    "high": max(numeric_values) if numeric_values else None,
                    "samples": len(numeric_values),
                }
        except Exception as e:
            logger.warning(f"[GARMIN] spo2 failed: {e}")

        # Respiration (This was the problematic one)
        try:
            resp_raw = self.client.get_respiration(today)
            if resp_raw and isinstance(resp_raw, dict):
                arrays = resp_raw.get("respirationAveragesArray") or resp_raw.get("respirationAveragesValuesArray")
                if arrays:
                    # Array format: [timestamp, average_value, high_value, low_value]
                    valid_rows = [item for item in arrays if isinstance(item, list) and len(item) > 1 and item[1] is not None]
                    if valid_rows:
                        avg_values = [row[1] for row in valid_rows if isinstance(row[1], (int, float))]
                        high_values = [row[2] for row in valid_rows if len(row) > 2 and isinstance(row[2], (int, float))]
                        low_values = [row[3] for row in valid_rows if len(row) > 3 and isinstance(row[3], (int, float))]
                        report["respiration"] = {
                            "avg_bpm": round(sum(avg_values) / len(avg_values), 1) if avg_values else None,
                            "high_bpm": max(high_values) if high_values else None,
                            "low_bpm": min(low_values) if low_values else None,
                            "samples": len(valid_rows),
                        }
                    else:
                        report["respiration"] = None
                else:
                    report["respiration"] = None
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
        if enforce_fetch_limit:
            self._update_fetch_limit()
        return report
