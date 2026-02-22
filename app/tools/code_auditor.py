import sys
import subprocess
import os

# Standalone configuration (No external app dependencies)
# This allows the script to funtion inside a clean Docker container
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Default prompt if DB/Config is unreachable
CODE_AUDIT_PROMPT = """
Du är en expert och senior mjukvaruarkitekt.
Analysera den bifogade källkoden med avseende på:
1. Arkitektoniska mönster och eventuella överträdelser
2. Kodkvalitet, säkerhet och prestandaproblem
3. Förbättringar och förslag på refaktorisering
4. Potentiella buggar eller kantfall

Ge en detaljerad rapport i Markdown-format på SVENSKA.
"""

# Standard imports
try:
    from google import genai as google_genai
except ImportError:
    google_genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import anthropic
except ImportError:
    anthropic = None

# Configuration
OUTPUT_FILE = "../../DAA_CODE_REVIEW.md"
IGNORED_DIRS = {
    'venv', 'node_modules', '.git', '__pycache__', 'logs', 'dist', 'build', 
    'garmin_tokens', '.vscode', 'assets', 'site-packages', '__init__', 'frontend'
}
ALLOWED_EXTENSIONS = {'.py', '.js', '.jsx', '.html', '.css', '.bat', '.json', '.md'}
IGNORED_FILES = {'package-lock.json', 'service_account.json', 'daa_memory.db', 'DAA_CODE_REVIEW.md'}

def get_project_code(root_dir):
    """Reads all code recursively."""
    code_content = ""
    file_count = 0
    # Use provided root_dir (usually ".") which maps to /workspace in Docker
    actual_root = os.path.abspath(root_dir) 
    
    print(f"[AUDIT] Reading files from: {actual_root}")
    
    for subdir, dirs, files in os.walk(actual_root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in ALLOWED_EXTENSIONS and file not in IGNORED_FILES:
                file_path = os.path.join(subdir, file)
                rel_path = os.path.relpath(file_path, actual_root)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code_content += f"\n--- FIL: {rel_path} ---\n{f.read()}\n"
                        file_count += 1
                except Exception as e:
                    print(f"[SKIP] Could not read {rel_path}: {e}")
                    
    return code_content, file_count

def process_and_save_response(full_response_text, model_name):
    SEPARATOR = "---RAPPORT_START---"
    try:
        # Save to docs folder if possible, else root
        output_dir = os.path.join(os.getcwd(), "docs")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        timestamp = subprocess.check_output(['date', '+%Y%m%d_%H%M%S']).decode().strip()
        filename = f"code_audit_{timestamp}.md"
        abs_output = os.path.join(output_dir, filename)
        
        with open(abs_output, "w", encoding="utf-8") as f:
            f.write(full_response_text)
        file_saved_msg = f"\n\n📂 *Full report saved to: {abs_output}*"
    except Exception as e:
        file_saved_msg = f"\n\n⚠️ Could not save report file: {e}"

    if SEPARATOR in full_response_text:
        summary_for_chat = full_response_text.split(SEPARATOR)[0].strip()
    else:
        summary_for_chat = full_response_text[:1000] + "...\n(See file for rest)"

    return f"✅ **Analysis complete with {model_name}!**\n\n{summary_for_chat}{file_saved_msg}"

def run_code_audit(preferred_model=None):
    print("[AUDIT] Starting code collection...")
    full_code, count = get_project_code(".")
    
    if count == 0: 
        print("[AUDIT] No files found!")
        return "Found no files to analyze. Check paths."
    
    print(f"[AUDIT] Found {count} files. Sending to AI...")
    
    final_prompt = f"{CODE_AUDIT_PROMPT}\n\nSOURCE CODE ({count} files):\n{full_code}"

    # Lista modeller att testa (Prioritize updated/cheaper models)
    test_models = ['gemini-2.0-flash', 'gemini-1.5-pro', 'gpt-4o', 'gpt-3.5-turbo']

    for model_name in test_models:
        try:
            # --- GOOGLE (new google.genai SDK) ---
            if "gemini" in model_name.lower() and GOOGLE_API_KEY and google_genai:
                print(f"   - Testar Google: {model_name}")
                client = google_genai.Client(api_key=GOOGLE_API_KEY)
                response = client.models.generate_content(
                    model=model_name,
                    contents=final_prompt
                )
                text = response.text if response.text else ""
                return process_and_save_response(text, f"Google {model_name}")

            # --- OPENAI ---
            elif "gpt" in model_name.lower() and OPENAI_API_KEY:
                print(f"   - Testar OpenAI: {model_name}")
                client = OpenAI(api_key=OPENAI_API_KEY)
                res = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "system", "content": CODE_AUDIT_PROMPT},
                              {"role": "user", "content": f"KOD:\n{full_code}"}]
                )
                return process_and_save_response(res.choices[0].message.content, model_name)

        except Exception as e:
            # Just print the exception message without traceback so the loop continues
            print(f"   x {model_name} failed: {e}")
            continue

    return "⚠️ Could not analyze code. Check API keys and internet connection."

if __name__ == '__main__':
    print(run_code_audit())