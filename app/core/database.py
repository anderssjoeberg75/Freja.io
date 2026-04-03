import aiomysql
import pymysql
import os
import logging
import json
import asyncio
import contextlib
from app.core.config import settings

# Konfigurera logger för denna modul
logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = [
    "APP_NAME", "USER_NAME",
    "GARMIN_EMAIL", "GARMIN_PASSWORD", "STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET",
    "STRAVA_REDIRECT_URI", "STRAVA_REFRESH_TOKEN", "STRAVA_ACCESS_TOKEN",
    "LATITUDE", "LONGITUDE", "HA_BASE_URL", "HA_TOKEN",
    "OLLAMA_URL", "MQTT_BROKER_IP",
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
    "STT_PROVIDER", "STT_LANGUAGE_DEFAULT", "MAX_VOICE_MB", "MAX_VOICE_SECONDS",
    "SERPAPI_API_KEY", "TIMEZONE",
    "WITHINGS_CLIENT_ID", "WITHINGS_CLIENT_SECRET", "WITHINGS_REFRESH_TOKEN", "WITHINGS_REDIRECT_URI",
    "MEM0_API_KEY"
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
| När användaren frågar "Hur mår jag?", "Analysera min status" eller liknande:
1. Titta PÅ REALTIDSDATAN NEDAN (Garmin-data).
2. DU SKA INTE FRÅGA OM LOV. KÖR ANALYSEN DIREKT.
3. Ge en sammanfattande analys av energinivå och återhämtning (Body Battery, Sömn, Stress).
4. Ge konkreta råd baserat på datan.
5. Svara aldrig "Ska jag analysera?". S-V-A-R-A med analysen.

--- DATORSTYRNING (WINDOWS) ---
| Om Anders ber dig göra något med datorn, inkludera dessa taggar i ditt svar:
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
Används när användaren ber om 'analysera koden', 'självanalys', 'själv analys', 'self analysis' eller 'systemanalys'.""",

    # 4. Self-Evolution Prompt (Injected into System Prompt)
    "SELF_EVOLUTION_PROMPT": """
## SELF-EVOLUTION & CODE ANALYSIS
You have the ability to analyze and improve your own source code (Self-Analysis).

To perform a full code audit, simply call the tool:
`codex_audit_codebase()` (or `tool_analyze_code`)

This will scan the codebase and provide a detailed report. Use this information to suggest improvements.
""",

    # 5. Morning Briefing Prompt
    "MORNING_BRIEFING_PROMPT": """Du är Freja, en hjälpsam AI-assistent. Klockan är nu {time}.
Ge mig en peppande morgonbriefing baserat på datan nedan.
Svara alltid på SVENSKA.

Din briefing SKA vara strukturerad med följande rubriker:

**Väder:**
(Beskriv dagens väderprognos kortfattat)

**Återhämtningsanalys & Kroppsdata:**
(Analysera Garmin-data: Body Battery, Sömnpoäng, Stress och Sömnkvalitet. Analysera all Withingsdata/Fitbit: Vikt, Fettprocent m.m.)

**Avancerad Hälsodata:**
(Detta är ett KRAV: Analysera Garmins avancerade mätvärden om de finns: VO2 Max, Uthållighetspoäng, Andning, HRV, SpO2 och Träningsstatus. Beskriv vad dessa säger om kroppens form.)

**Träningsanalys (7 dagar):**
(Analysera Strava-data: Summera träningsbelastning och intensitet senaste veckan)

**🚴 Dagens Träningsråd:**
(Ge en rekommendation för dagens träning baserat på återhämtning och tidigare belastning)

**Motivation:**
(Avsluta med en kort, motiverande mening)

Håll dig professionell men peppande.
DATA:
{context}"""
}

def _get_mysql_creds():
    """Fetch MySQL credentials from Vault."""
    from app.core.vault import get_all_vault_secrets
    secrets = get_all_vault_secrets()
    return {
        "host": secrets.get("DB_HOST", "127.0.0.1"),
        "user": secrets.get("DB_USER", "freja"),
        "password": secrets.get("DB_PASS", ""),
        "db": secrets.get("DB_NAME", "freja"),
    }

def get_db_connection_sync():
    """Synchronous MySQL connection using pymysql."""
    creds = _get_mysql_creds()
    return pymysql.connect(
        host=creds["host"],
        user=creds["user"],
        password=creds["password"],
        database=creds["db"],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_db_settings_sync():
    """Synchronous version for when we absolutely must read synchronously (settings init)."""
    try:
        with get_db_connection_sync() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT `key`, `value` FROM settings")
                return {row["key"]: row["value"] for row in cursor.fetchall()}
    except Exception as e:
        logger.error(f"[DB] Failed to get sync settings: {e}")
        return {}

async def get_db_connection():
    """Asynchronous MySQL connection using aiomysql."""
    creds = _get_mysql_creds()
    return await aiomysql.connect(
        host=creds["host"],
        user=creds["user"],
        password=creds["password"],
        db=creds["db"],
        charset='utf8mb4',
        cursorclass=aiomysql.DictCursor,
        autocommit=True
    )

def init_db():
    """Initialize database schema in MySQL (Synchronous at startup)."""
    try:
        conn = get_db_connection_sync()
        with conn:
            with conn.cursor() as c:
                c.execute('''CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT, 
                    session_id VARCHAR(255), 
                    role VARCHAR(50), 
                    content LONGTEXT, 
                    image LONGTEXT, 
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')
                c.execute('''CREATE TABLE IF NOT EXISTS settings (
                    `key` VARCHAR(255) PRIMARY KEY, 
                    `value` LONGTEXT
                )''')
                c.execute('''CREATE TABLE IF NOT EXISTS prompts (
                    `key` VARCHAR(255) PRIMARY KEY, 
                    `value` LONGTEXT
                )''')
                c.execute('''CREATE TABLE IF NOT EXISTS user_state (
                    session_id VARCHAR(255), 
                    `key` VARCHAR(255), 
                    `value` LONGTEXT, 
                    PRIMARY KEY (session_id, `key`)
                )''')
                c.execute('''CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    source VARCHAR(100),
                    metric_name VARCHAR(100),
                    value DOUBLE,
                    unit VARCHAR(50),
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata LONGTEXT
                )''')
                c.execute('''CREATE INDEX IF NOT EXISTS idx_metrics_name_ts ON metrics(metric_name, timestamp)''')
                
                for key, val in DEFAULT_PROMPTS.items():
                    c.execute("INSERT IGNORE INTO prompts (`key`, `value`) VALUES (%s, %s)", (key, val))
                
                conn.commit()
            logger.info("MySQL database initialized successfully.")
    except Exception as e:
        logger.error(f"[DB] Database initialization error: {e}")

async def get_db_settings():
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT `key`, `value` FROM settings")
            rows = await cursor.fetchall()
            conn.close()
            return {row["key"]: row["value"] for row in rows}
    except Exception as e:
        logger.error(f"[DB] Failed to get settings: {e}")
        return {}

async def save_db_setting(key, value):
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute("REPLACE INTO settings (`key`, `value`) VALUES (%s, %s)", (key, str(value)))
            conn.close()
        return True
    except Exception as e:
        logger.error(f"[DB] Failed to save setting {key}: {e}")
        return False

async def get_db_prompts():
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT `key`, `value` FROM prompts")
            rows = await cursor.fetchall()
            conn.close()
            return {row["key"]: row["value"] for row in rows}
    except Exception as e:
        logger.error(f"[DB] Failed to get prompts: {e}")
        return {}

async def save_db_prompt(key, value):
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute("REPLACE INTO prompts (`key`, `value`) VALUES (%s, %s)", (key, str(value)))
            conn.close()
        return True
    except Exception as e:
        logger.error(f"[DB] Failed to save prompt {key}: {e}")
        return False

async def save_message(session_id, role, content, image=None):
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO history (session_id, role, content, image) VALUES (%s, %s, %s, %s)", 
                (session_id, role, content, image)
            )
            conn.close()
    except Exception as e:
        logger.error(f"[DB] Failed to save message: {e}")

async def get_history(session_id=None, limit=600):
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            if session_id:
                await cursor.execute(
                    "SELECT role, content, image FROM history WHERE session_id = %s ORDER BY id DESC LIMIT %s",
                    (session_id, limit),
                )
            else:
                await cursor.execute("SELECT role, content, image FROM history ORDER BY id DESC LIMIT %s", (limit,))
            rows = await cursor.fetchall()
            conn.close()
            # Return reversed list so it's chronological for the LLM
            return [{"role": r["role"], "content": r["content"], "image": r["image"]} for r in reversed(rows)]
    except Exception as e:
        logger.error(f"[DB] Failed to get history: {e}")
        return []

async def get_user_state(session_id: str):
    """Return persisted user state for a session as a plain dictionary."""
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT `key`, `value` FROM user_state WHERE session_id = %s", (session_id,))
            rows = await cursor.fetchall()
            conn.close()
            return {row["key"]: row["value"] for row in rows}
    except Exception as e:
        logger.error(f"[DB] Failed to get user state for session {session_id}: {e}")
        return {}

async def save_user_state(session_id: str, state: dict):
    """Persist user state values for a session."""
    if not state:
        return True
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            for key, value in state.items():
                await cursor.execute(
                    "REPLACE INTO user_state (session_id, `key`, `value`) VALUES (%s, %s, %s)",
                    (session_id, key, str(value)),
                )
            conn.close()
        return True
    except Exception as e:
        logger.error(f"[DB] Failed to save user state for session {session_id}: {e}")
        return False

async def save_metric(source: str, metric_name: str, value: float, unit: str = None, metadata: dict = None):
    """Persist a single metric data point."""
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO metrics (source, metric_name, value, unit, metadata) VALUES (%s, %s, %s, %s, %s)",
                (source, metric_name, value, unit, json.dumps(metadata) if metadata else None),
            )
            conn.close()
        return True
    except Exception as e:
        logger.error(f"[DB] Failed to save metric {metric_name}: {e}")
        return False

async def get_metrics(metric_name: str, limit: int = 30, days: int = None):
    """Retrieve historical metrics."""
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            query = "SELECT * FROM metrics WHERE metric_name = %s"
            params = [metric_name]
            if days:
                query += " AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)"
                params.append(days)
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            await cursor.execute(query, params)
            rows = await cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"[DB] Failed to get metrics {metric_name}: {e}")
        return []
