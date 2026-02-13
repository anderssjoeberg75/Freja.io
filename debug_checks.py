import asyncio
import logging
from app.core.prompts import get_system_prompt
from app.services.web_fallback_service import needs_web_fallback
from app.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)

def check_prompt():
    print("--- SYSTEM PROMPT CHECK ---")
    prompt = get_system_prompt()
    print(prompt)
    print("---------------------------")
    
    if "Freja.Io" in prompt:
        print("✅ Name 'Freja.Io' found.")
    else:
        print("❌ Name 'Freja.Io' NOT found.")
        
    if "2026" in prompt:
        print("✅ Year '2026' found.")
    else:
        print("❌ Year '2026' NOT found.")

def check_fallback():
    print("\n--- FALLBACK LOGIC CHECK ---")
    # Test case from user
    response = "Verkställer, Anders. Jag ser att du återigen frågar om vinnaren av Melodifestivalen 2025. Tyvärr finns den informationen inte i mina nuvarande databaser, och jag har inte möjlighet att hämta den just nu. Kan jag hjälpa dig med en annan fråga?"
    
    print(f"Testing response: '{response}'")
    
    triggers = needs_web_fallback(response)
    print(f"needs_web_fallback result: {triggers}")
    
    if triggers:
        print("✅ Fallback TRIGGERED correctly.")
    else:
        print("❌ Fallback FAILED to trigger.")

    # Check config
    print(f"WEB_FALLBACK_ENABLED setting: {settings.WEB_FALLBACK_ENABLED}")
    
    from app.core.config import get_credential
    serp_key = get_credential("SERPAPI_API_KEY")
    print(f"SERPAPI KEY Present: {bool(serp_key)}")
    
    if not serp_key:
        print("❌ CRITICAL: SerpAPI Key MISSING. Search will fail.")
        
    # DB Inspection
        
    # DB Inspection
    print("\n--- DB RAW INSPECTION ---")
    from app.core.config import DB_PATH
    from app.core.database import get_db_settings
    print(f"DB Path: {DB_PATH}")
    
    all_settings = get_db_settings()
    print("Keys in DB:")
    for k, v in all_settings.items():
        masked_val = "***" if len(v) > 5 else v
        if "WEB" in k or "TEST" in k or "SERP" in k:
            print(f"  {k}: {masked_val}")
            
    # Real Search Test
    print("\n--- REAL SEARCH TEST (SerpAPI) ---")
    try:
        from app.services.web_fallback_service import SerpAPIProvider
        import asyncio
        
        async def test_search():
            provider = SerpAPIProvider()
            print("Searching for 'Vem vann melodifestivalen 2025'...")
            results = await provider.search("Vem vann melodifestivalen 2025", 3)
            print(f"Results found: {len(results)}")
            for r in results:
                print(f" - {r.title}: {r.url}")
                
        asyncio.run(test_search())
    except Exception as e:
        print(f"❌ Search Test Failed: {e}")

if __name__ == "__main__":
    check_prompt()
    check_fallback()
