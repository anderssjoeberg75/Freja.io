from datetime import datetime
from app.core.database import get_db_prompts

"""
==============================================================================
FILE: app/core/prompts.py
DESCRIPTION: Combines static text from DB with dynamic time/date.
==============================================================================
"""

def get_prompts_data():
    """Helper function to fetch all data from DB."""
    return get_db_prompts()

def get_system_prompt():
    """
    Builds the system prompt:
    1. Fetches personality/rules from Database.
    2. Adds real-time info (Time/Date) via Python.
    """
    # 1. Fetch base text from database
    data = get_prompts_data()
    # If DB is empty, use a simple fallback
    base_prompt = data.get("SYSTEM_PROMPT", "Du är Freja.Io. Fyll i din prompt i inställningarna.")

    # 2. Create time data (Real-time data injection)
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    current_date = now.strftime("%Y-%m-%d")
    week_number = now.strftime("%V")
    
    # Day names in Swedish (for Swedish-speaking AI assistant)
    days_se = {
        "Monday": "måndag", "Tuesday": "tisdag", "Wednesday": "onsdag",
        "Thursday": "torsdag", "Friday": "fredag", "Saturday": "lördag", "Sunday": "söndag"
    }
    day_name = now.strftime("%A")
    swedish_day_name = days_se.get(day_name, day_name)
    
    # 3. Create context block
    time_context = (
        f"\n\n--- REAL-TIME INFORMATION (SYSTEM GENERATED) ---\n"
        f"CURRENT DATE: {current_date}\n"
        f"CURRENT TIME: {current_time}\n"
        f"DAY: {swedish_day_name} (Week {week_number})\n"
        f"IMPORTANT: You are living in {now.year}. If the user asks about past events (e.g. from 2024, 2025), ANSWER THEM as facts, do not say they haven't happened.\n"
        f"---------------------------------------------------\n"
    )
    
    # 4. Inject APP_NAME into prompt (replace "DAA" with configured name)
    from app.core.config import settings
    app_name = settings.APP_NAME
    
    # Replace all instances of "DAA" with the configured app name
    final_prompt = base_prompt.replace("DAA", app_name)
    
    # 5. Combine: Modified text + Time block + Self-Evolution
    self_evolution = data.get("SELF_EVOLUTION_PROMPT", "")
    
    # 6. Override Language Instruction (Hard rule)
    language_rule = (
        "\n\n--- LANGUAGE INSTRUCTION ---\n"
        "VIKTIGT: Du ska ALLTID svara på SVENSKA. "
        "Även om koden och system-meddelanden är på engelska, så ska dina svar till användaren vara på svenska.\n"
        "Code names, variables, and technical terms should remain in English/Code format.\n"
    )
    
    return final_prompt + time_context + self_evolution + language_rule

def get_audit_prompt():
    return get_prompts_data().get("CODE_AUDIT_PROMPT", "No code analysis prompt found.")

def get_audit_tool_desc():
    # Default description if missing from DB
    default = "Analyzes project source code to find errors and improvements."
    return get_prompts_data().get("TOOL_DESC_AUDIT", default)

# Variables for import to other files
CODE_AUDIT_PROMPT = get_audit_prompt()
ANALYZE_CODE_TOOL_DESC = get_audit_tool_desc()