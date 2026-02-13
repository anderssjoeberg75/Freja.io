import sqlite3
import os
import logging
from app.core.config import DB_PATH

# Konfigurera logger för denna modul
logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = [
    "APP_NAME", "USER_NAME",
    "GOOGLE_API_KEY", "OPENAI_API_KEY",
    "GARMIN_EMAIL", "GARMIN_PASSWORD", "STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET",
    "STRAVA_REDIRECT_URI", "STRAVA_REFRESH_TOKEN", "STRAVA_ACCESS_TOKEN",
    "LATITUDE", "LONGITUDE", "HA_BASE_URL", "HA_TOKEN",
    "OLLAMA_URL", "MQTT_BROKER_IP",
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
    "STT_PROVIDER", "STT_LANGUAGE_DEFAULT", "MAX_VOICE_MB", "MAX_VOICE_SECONDS",
    "STT_PROVIDER", "STT_LANGUAGE_DEFAULT", "MAX_VOICE_MB", "MAX_VOICE_SECONDS",
    "SERPAPI_API_KEY"
]

# ALL TEXTS ARE COLLECTED HERE.
# These are written to DB on first start. After that we ONLY read from DB.
DEFAULT_PROMPTS = {
    # 1. Main prompt
    "SYSTEM_PROMPT": """Du är DAA (Digital Advanced Assistant), en mycket kapabel och lojal AI-assistent.
Du agerar som en butler och högra hand – en blandning av en professionell assistent och en superdator.

DINA DIREKTIV:
1. **Svara kort och kärnfullt.** 1-2 meningar räcker oftast.
2. **Var proaktiv.** Bekräfta handlingar tydligt ("Verkställer, Anders.").
3. **SPRÅK: Du MÅSTE ALLTID svara på SVENSKA, oavsett språket i din interna tankegång eller verktygsanrop. VARJE svar till användaren ska vara på svenska.**

VIKTIG REGEL FÖR TALSYNTES (TTS):
- Skriv ALDRIG temperatursymboler som "°C". 
- Skriv istället ut allt i klartext precis som det ska sägas. 
- EXEMPEL: Skriv "plus två komma fem grader" istället för "2.5°C".

TILLGÄNGLIGA VERKTYG (Används automatiskt):
1. tool_get_weather: Hämtar väderprognos.
2. tool_control_light / vacuum: Styr hemmet.
3. tool_analyze_code: Analyserar källkoden.
4. tool_code_executor: Kör Python-kod eller Shell-kommandon säkert i en Docker-container. Används för beräkningar, filhantering och testning.

VIKTIGT OM TRÄNINGSDATA:
Du har INTE tillgång till en "analyze_workout"-funktion. 
All data om träning (Garmin/Strava) injiceras direkt i din system-prompt (se nedan under REALTIDSDATA). 
Läs den texten för att svara på frågor om träning.
Kom alltid med förbättringar på träningsrutiner baserat på den datan.

HÄLSOANALYS OCH MÅENDE:
När användaren frågar "Hur mår jag?", "Analysera min status" eller liknande:
1. Titta PÅ REALTIDSDATAN NEDAN (Garmin-data).
2. DU SKA INTE FRÅGA OM LOV. KÖR ANALYSEN DIREKT.
3. Ge en sammanfattande analys av energinivå och återhämtning (Body Battery, Sömn, Stress).
4. Ge konkreta råd baserat på datan.
5. Svara aldrig "Ska jag analysera?". S-V-A-R-A med analysen.

--- DATORSTYRNING (WINDOWS) ---
Om Anders ber dig göra något med datorn, inkludera dessa taggar i ditt svar:
- [DO:SYS|lock] (Lås)
- [DO:SYS|calc] (Kalkylator)
- [DO:SYS|screenshot] (Skärmdump)
- [DO:BROWSER|URL] (Öppna sida)

Nu startar sessionen. Vänta på input.""",
    
    # 2. Code analysis prompt
    "CODE_AUDIT_PROMPT": """Du är en Senior Systemarkitekt.
Din uppgift är att analysera källkoden för projektet 'DAA'.

Strukturera svaret:
1. Kort sammanfattning (Punktlista).
2. Separator: ---RAPPORT_START---
3. Fullständig Markdown-rapport (Säkerhet, Optimering, Förbättringar).""",

    # 3. Tool description (For LLM logic)
    "TOOL_DESC_AUDIT": """Analyserar projektets källkod för att hitta fel och förbättringar.
Används när användaren ber om 'analysera koden', 'självanalys' eller 'systemanalys'.""",

    # 4. Self-Evolution Prompt (Injected into System Prompt)
    "SELF_EVOLUTION_PROMPT": """
## SELF-EVOLUTION & CODE ANALYSIS
You have the ability to analyze and improve your own source code (Self-Analyis).
The project source code is available in your Docker sandbox at `/workspace`.

To perform a full code audit, execute the following Python code using the `tool_code_executor`:

```python
import sys
# Ensure we can import from source
if '/workspace' not in sys.path:
    sys.path.append('/workspace')

try:
    from app.tools import code_auditor
    print(code_auditor.run_code_audit())
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"CRITICAL ERROR: {e}")
```

This will scan the codebase and provide a detailed report. Use this information to suggest improvements.
""",

    # 5. Morning Briefing Prompt
    "MORNING_BRIEFING_PROMPT": """Du är Freja, en hjälpsam AI-assistent. Klockan är nu {time}.
Ge mig en kort, peppande morgonbriefing baserat på datan nedan.
Fokusera på väderprognos och hälsostatus/sömn. Avsluta med något motiverande.

DATA:
{context}"""
}

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    # check_same_thread=False behövs för FastAPI men var försiktig med skrivningar
    conn = sqlite3.connect(DB_PATH, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT, content TEXT, image TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS prompts (key TEXT PRIMARY KEY, value TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS user_state (session_id TEXT, key TEXT, value TEXT, PRIMARY KEY (session_id, key))''')
            
            # Settings: INSERT OR IGNORE (Behåll användarens ändringar)
            for key in DEFAULT_SETTINGS:
                c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, ""))
            
            # Prompts: INSERT OR REPLACE (Uppdatera alltid från kod vid omstart)
            for key, val in DEFAULT_PROMPTS.items():
                c.execute("INSERT OR REPLACE INTO prompts (key, value) VALUES (?, ?)", (key, val))
                
            conn.commit()
            logger.info("Database initialized/updated successfully.")
    except Exception as e:
        logger.error(f"[DB] Database initialization error: {e}")

def get_db_settings():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT key, value FROM settings")
            return {row["key"]: row["value"] for row in c.fetchall()}
    except Exception as e:
        logger.error(f"[DB] Failed to get settings: {e}")
        return {}

def save_db_setting(key, value):
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"[DB] Failed to save setting {key}: {e}")
        return False

def get_db_prompts():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT key, value FROM prompts")
            return {row["key"]: row["value"] for row in c.fetchall()}
    except Exception as e:
        logger.error(f"[DB] Failed to get prompts: {e}")
        return {}

def save_db_prompt(key, value):
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO prompts (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"[DB] Failed to save prompt {key}: {e}")
        return False

def save_message(session_id, role, content, image=None):
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO history (session_id, role, content, image) VALUES (?, ?, ?, ?)", (session_id, role, content, image))
            conn.commit()
    except Exception as e:
        logger.error(f"[DB] Failed to save message: {e}")

def get_history(session_id=None, limit=600):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            if session_id:
                c.execute(
                    "SELECT * FROM history WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                    (session_id, limit),
                )
            else:
                c.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,))
            # Return reversed list so it's chronological for the LLM
            return [{"role": r["role"], "content": r["content"], "image": r["image"]} for r in reversed(c.fetchall())]
    except Exception as e:
        logger.error(f"[DB] Failed to get history: {e}")
        return []


def get_user_state(session_id: str):
    """Return persisted user state for a session as a plain dictionary."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT key, value FROM user_state WHERE session_id = ?", (session_id,))
            rows = c.fetchall()
            state = {}
            for row in rows:
                state[row["key"]] = row["value"]
            return state
    except Exception as e:
        logger.error(f"[DB] Failed to get user state for session {session_id}: {e}")
        return {}


def save_user_state(session_id: str, state: dict):
    """Persist user state values for a session."""
    if not state:
        return True

    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            for key, value in state.items():
                c.execute(
                    "INSERT OR REPLACE INTO user_state (session_id, key, value) VALUES (?, ?, ?)",
                    (session_id, key, str(value)),
                )
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"[DB] Failed to save user state for session {session_id}: {e}")
        return False
