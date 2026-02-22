from app.core.database import save_user_state

async def update_user_profile_impl(session_id: str, age: str = None, max_hr: str = None, weight_kg: str = None) -> str:
    """
    Updates the user's profile information based on AI extraction from the chat.
    Valid fields are 'age', 'max_hr', and 'weight'.
    """
    updates = {}
    if age:
        updates["age"] = age
    if max_hr:
        updates["max_hr"] = max_hr
    if weight_kg:
        updates["weight"] = weight_kg

    if updates:
        success = await save_user_state(session_id, updates)
        if success:
            return f"Uppdaterade profil med {updates}"
        else:
            return "Kunde inte uppdatera profilen i databasen."
    return "Ingen ändring begärdes."
