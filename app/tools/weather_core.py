import httpx
import asyncio
from app.core.config import get_credential

# SMHI Wsymb2 Mapping (1-27)
SMHI_CODES = {
    1: "Clear sky", 2: "Light clouds", 3: "Partly cloudy", 4: "Cloudy", 5: "Mostly cloudy", 
    6: "Overcast", 7: "Fog", 8: "Light rain shower", 9: "Rain shower", 10: "Heavy rain shower",
    11: "Thunder shower", 12: "Light sleet shower", 13: "Sleet shower", 
    14: "Heavy sleet shower", 15: "Light snow shower", 16: "Snow shower", 17: "Heavy snow shower",
    18: "Light rain", 19: "Rain", 20: "Heavy rain", 21: "Thunder", 22: "Light sleet",
    23: "Sleet", 24: "Heavy sleet", 25: "Light snowfall", 
    26: "Snowfall", 27: "Heavy snowfall"
}

async def get_weather():
    """
    Fetch weather from the SMHI Open API (PMP3g).
    """
    lat = get_credential("LATITUDE")
    lon = get_credential("LONGITUDE")

    if not lat or not lon:
        return "⚠️ Missing GPS coordinates. Set LATITUDE and LONGITUDE in settings."

    # SMHI requires 6 decimal precision
    try:
        lat_formatted = f"{float(lat):.6f}"
        lon_formatted = f"{float(lon):.6f}"
    except ValueError:
        return "⚠️ Invalid GPS coordinates."

    url = f"https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point/lon/{lon_formatted}/lat/{lat_formatted}/data.json"

    try:
        # User-Agent is good practice/required sometimes
        headers = {"User-Agent": "DAA-Assistant/1.0"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0, headers=headers)
            
            if response.status_code != 200:
                print(f"[SMHI] Error {response.status_code}: {response.text}")
                return f"Could not fetch weather from SMHI (HTTP {response.status_code})."

            data = response.json()
            time_series = data.get("timeSeries", [])
            
            if not time_series:
                return "No weather data available from SMHI."

            # --- Current Weather (First data point) ---
            current = time_series[0]
            params = {p["name"]: p["values"][0] for p in current["parameters"]}
            
            # Wsymb2 = Weather Symbol
            wsymb = int(params.get("Wsymb2", 0))
            desc = SMHI_CODES.get(wsymb, f"Unknown weather ({wsymb})")
            
            # t = Temp C
            temp = params.get("t", "N/A")
            
            # ws = Wind Speed m/s
            wind = params.get("ws", "N/A")

            # --- Forecast (Next 3 Days) ---
            forecast_msg = ""
            days = ["Today", "Tomorrow", "Day after tomorrow"]
            
            # Simple assumption: 24h per day blocks roughly (since data is hourly for first days)
            # Better: Group by date string (validTime)
            
            daily_stats = {}
            for entry in time_series:
                vt = entry.get("validTime", "")[:10] # YYYY-MM-DD
                if vt not in daily_stats: daily_stats[vt] = []
                
                p = {x["name"]: x["values"][0] for x in entry["parameters"]}
                if "t" in p: daily_stats[vt].append(p["t"])
            
            # Sort dates and take first 3
            sorted_dates = sorted(daily_stats.keys())[:3]
            
            for i, date in enumerate(sorted_dates):
                if i < len(days):
                    temps = daily_stats[date]
                    if temps:
                        d_max = max(temps)
                        d_min = min(temps)
                        forecast_msg += f"{days[i]}: Max {d_max}°C, Min {d_min}°C. "

            report = (
                f"SMHI currently reports {desc} and {temp}°C, wind {wind} m/s. "
                f"Forecast: {forecast_msg}"
            )
                
            return report

    except Exception as e:
        print(f"[WEATHER] Error: {e}")
        return "System error while fetching weather data from SMHI."

if __name__ == "__main__":
    import sys
    import os
    # Allow importing config when running directly
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    print(asyncio.run(get_weather()))