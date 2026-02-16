# Freja Skills Guide

Detta är en översikt över alla tillgängliga färdigheter (skills) och verktyg i Freja-systemet.

## 🛠️ Core Skills (Kärnfunktioner)

### 💻 Codex (Programmering & Analys)
Ger Freja förmågan att skriva kod, exekvera den i en säker sandbox och analysera sig själv.

*   **Verktyg:**
    *   `tool_code_executor` / `execute_python`: Kör Python-kod i en Docker-container (`freja-codex-sandbox`). Har tillgång till filsystemet via bind-mount.
    *   `tool_analyze_code` / `codex_audit_codebase`: Utför en fullständig självanalys av källkoden och genererar en rapport i `docs/`.
    *   `git_clone`, `git_checkout`, `git_status`: Hanterar Git-operationer för versionshantering.

*   **Användning:**
    *   "Skriv ett script som listar alla filer i katalogen."
    *   "Kör en självanalys av projektet."
    *   "Klona repot https://github.com/..."

### 📅 Google Calendar (Kalender)
Hanterar din Google-kalender.

*   **Verktyg:**
    *   `calendar_list_events(count)`: Listar kommande händelser.
    *   `calendar_create_event(summary, start, end...)`: Skapar nya möten.
    *   `calendar_update_event(...)`: Uppdaterar befintliga händelser.
    *   `calendar_delete_event(event_id)`: Tar bort händelser.

*   **Användning:**
    *   "Vad har jag inbokat idag?"
    *   "Boka ett möte med teamet imorgon kl 14."

---

## 🏃 Fitness & Hälsa

### ⌚ Garmin
Hämtar hälsodata från Garmin Connect.

*   **Verktyg:**
    *   `get_garmin_health(date)`: Hämtar steg, sömn, body battery och vilopuls.

*   **Användning:**
    *   "Hur sov jag inatt?"
    *   "Vad är min Body Battery nivå?"

### 🚲 Strava
Hämtar träningsaktiviteter från Strava.

*   **Verktyg:**
    *   `get_strava_activities(limit)`: Hämtar dina senaste träningspass (löpning, cykling, etc.).

*   **Användning:**
    *   "Visa mina senaste löprundor."
    *   "Hur långt cyklade jag i helgen?"

### ⚖️ Withings
Hämtar kroppsdata från Withings (vågar etc.).

*   **Verktyg:**
    *   `get_withings_health`: Hämtar vikt, fettprocent och muskelmassa.

*   **Användning:**
    *   "Vad väger jag?"
    *   "Visa min kroppssammansättning."

---

## 🏠 Smarta Hem & Vardag

### 🏠 Home Assistant
Styr ditt smarta hem via Home Assistant.

*   **Kommandon (Chatt):**
    Denna skill lyssnar på direktkommandon i chatten (börjar med `/ha` eller `ha`).
    *   `ha list [domain]`: Listar enheter (t.ex. `ha list light`).
    *   `ha get <entity_id>`: Hämtar status för en enhet.
    *   `ha on <entity_id>`: Slår på en enhet.
    *   `ha off <entity_id>`: Slår av en enhet.
    *   `ha scene <scene_id>`: Aktiverar en scen.

*   **Användning:**
    *   `ha on light.vardagsrum`
    *   `ha list switch`

### ☀️ Väder
Hämtar väderprognoser.

*   **Verktyg:**
    *   `get_weather`: Hämtar aktuell prognos för konfigurerad plats (via SMHI/API).

*   **Användning:**
    *   "Hur blir vädret imorgon?"
    *   "Behöver jag paraply?"

---

## 🌐 Övrigt

### I/O & System
*   `web_search`: Söker på nätet (använd ej för kodanalys).
*   `get_system_status`: Visar systemets hälsa (CPU/Minne).

---

## ⚙️ Installation & Konfiguration
För att aktivera nya skills, se till att nödvändiga API-nycklar finns i `.env` eller `credentials.json`.
Se respektive skill-katalog för specifik README (t.ex. `skills/codex/README.md`).
