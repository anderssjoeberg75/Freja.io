import httpx
import logging
import json
import re
from typing import List, Dict, Optional, Any
from app.core.config import get_credential, settings
from app.services.tool_registry import registry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Per-process cache: remember which models need fallback mode
# (avoids a wasted round-trip on every message)
# ---------------------------------------------------------------------------
_FALLBACK_MODELS: set = set()

# Models known to NOT support native Ollama tool_calls → use JSON-prompt fallback
_KNOWN_NO_NATIVE_TOOLS = {
    "deepseek-r1", "deepseek-v2", "phi3", "gemma", "mistral-nemo",
    "qwen2.5", "qwen2", "qwen3", "qwen",          # Qwen outputs JSON in content
    "cipher64", "darkseek",                         # Custom/abliterated models
}
# NOTE: llama3.1, llama3.2, llama3.3, mistral, firefunction → native tool_calls ✓

# Models that support Ollama's `think: false` option (disables reasoning chain)
_SUPPORTS_THINK_OPTION = {
    "deepseek-r1", "deepseek-r2",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_think_tags(text: str) -> str:
    """Remove <think>...</think> reasoning blocks and orphaned </think> tags."""
    # Remove complete blocks first
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Remove any orphaned closing tags left by think=false mode
    text = re.sub(r"</think>", "", text)
    return text.strip()


def _extract_tool_call(content: str) -> Optional[Dict[str, Any]]:
    """
    Try to extract a tool call JSON object from the model's raw text output.

    Handles multiple formats that reasoning models like DeepSeek may produce:
    1. Markdown code block:  ```json { "name": ..., "arguments": {...} } ```
    2. Bare inline JSON:      { "name": ..., "arguments": {...} }
    3. Nested tool_call key:  { "tool_call": { "name": ..., "arguments": {...} } }
    4. Array of calls:        [{ "name": ..., "arguments": {...} }]
    5. "parameters" instead of "arguments" variant
    6. {"function": ..., "args": {...}} variant (some Ollama models)
    """
    clean = _strip_think_tags(content)

    patterns = [
        r"```(?:json)?\s*(\{.*?\})\s*```",
        r"(\[\s*\{.*?\}\s*\])",
        r'(\{[^{}]*?"name"\s*:.*?(?:"arguments"|"parameters")\s*:.*?\})',
        r'(\{"tool_call"\s*:\s*\{.*?\}\s*\})',
        # {"function": "name", "args": {...}} variant
        r'(\{[^{}]*?"function"\s*:.*?"args"\s*:.*?\})',
    ]

    for pat in patterns:
        match = re.search(pat, clean, re.DOTALL)
        if not match:
            continue
        candidate = match.group(1).strip()
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue

        if isinstance(parsed, list):
            parsed = parsed[0] if parsed else None
        if not isinstance(parsed, dict):
            continue

        if "tool_call" in parsed and isinstance(parsed["tool_call"], dict):
            parsed = parsed["tool_call"]

        # Normalise {"function": ..., "args": ...} → {"name": ..., "arguments": ...}
        if "function" in parsed and "name" not in parsed:
            parsed["name"] = parsed.pop("function")
        if "args" in parsed and "arguments" not in parsed:
            parsed["arguments"] = parsed.pop("args")

        if "parameters" in parsed and "arguments" not in parsed:
            parsed["arguments"] = parsed.pop("parameters")

        if "name" in parsed and "arguments" in parsed:
            return parsed

    return None


def _resolve_tool_name(name: str) -> str:
    """
    Fuzzy-match a model-produced tool name to a registered tool name.
    Handles edge cases like:
      - "getknowledgebase"  → "query_knowledge_base"
      - "queryknowledgebase" → "query_knowledge_base"
      - exact matches pass through unchanged
    """
    registered = list(registry._tools.keys())

    # 1. Exact match
    if name in registered:
        return name

    # 2. Case-insensitive exact
    name_lower = name.lower()
    for r in registered:
        if r.lower() == name_lower:
            return r

    # 3. Strip underscores/dashes and compare
    name_stripped = re.sub(r"[_\-]", "", name_lower)
    for r in registered:
        if re.sub(r"[_\-]", "", r.lower()) == name_stripped:
            return r

    # 4. Substring: registered name contains all words from the model name
    name_words = set(re.split(r"[_\-]", name_lower))
    for r in registered:
        r_words = set(re.split(r"[_\-]", r.lower()))
        if name_words and name_words.issubset(r_words):
            return r

    # No match — return as-is (will produce a clear "Tool not found" error)
    return name




def _build_tool_system_addendum(tools: List[Dict[str, Any]]) -> str:
    """
    Build a compact tool-calling instruction block for models without native
    tool_calls support. Includes parameter names and types so the model knows
    exactly what JSON to produce.
    """
    tool_lines = []
    for t in tools:
        fn = t.get("function", t)
        name = fn.get("name", "")
        desc = fn.get("description", "")
        short_desc = desc.split(".")[0].split("\n")[0][:100]
        props = fn.get("parameters", {}).get("properties", {})
        required = fn.get("parameters", {}).get("required", [])

        # Build compact param list: param(type, required/optional)
        param_parts = []
        for pname, pmeta in props.items():
            ptype = pmeta.get("type", "string")
            req = "required" if pname in required else "optional"
            param_parts.append(f'{pname}:{ptype}({req})')
        params_str = ", ".join(param_parts) if param_parts else "no params"
        tool_lines.append(f'- {name}({params_str}): {short_desc}')

    tools_list = "\n".join(tool_lines)

    return (
        "\n\n[TOOL CALLING]\n"
        "Available tools:\n"
        f"{tools_list}\n\n"
        "To call a tool respond ONLY with valid JSON (no other text, no markdown):\n"
        '{"name": "tool_name", "arguments": {"param": "value"}}\n'
        "Omit optional params you don\'t know the value for. "
        "After receiving [Result of tool ...] answer the user in Swedish."
    )


def _model_base(model_id: str) -> str:
    """
    Return the meaningful base name from a model ID.
    Handles formats like:
      - 'deepseek-r1:14b'              → 'deepseek-r1'
      - 'hf.co/DavidAU/Qwen3-...:tag' → 'qwen3'
      - 'cipher64/darkseek:latest'     → 'darkseek'
    """
    # Strip tag first
    name = model_id.split(":")[0].lower()
    # For hf.co/ or namespace/model patterns, take the last path component
    if "/" in name:
        name = name.split("/")[-1]
    # Further strip to first dash-segment (e.g. 'qwen3-the-...' → 'qwen3')
    # but only if the result is meaningful (longer than 2 chars)
    first_segment = name.split("-")[0]
    if len(first_segment) > 2:
        name = first_segment
    return name


def _should_use_think(model_id: str) -> bool:
    """Return True if the model supports and benefits from think: false."""
    base = _model_base(model_id)
    return any(base.startswith(k) for k in _SUPPORTS_THINK_OPTION)


def _should_skip_native_tools(model_id: str) -> bool:
    """Return True if we already know this model doesn't support native tool_calls."""
    if model_id in _FALLBACK_MODELS or model_id.lower() in _KNOWN_NO_NATIVE_TOOLS:
        return True
    base = _model_base(model_id)
    return any(base.startswith(k) for k in _KNOWN_NO_NATIVE_TOOLS)


def _build_tool_header(tools: List[Dict[str, Any]]) -> str:
    """
    Returns a concise tool-header to prepend to the SYSTEM message.
    Placed at the TOP so the model sees it before any personality text.
    """
    tool_lines = []
    for t in tools:
        fn = t.get("function", t)
        name = fn.get("name", "")
        desc = fn.get("description", "")
        short_desc = desc.split(".")[0].split("\n")[0][:100]
        props = fn.get("parameters", {}).get("properties", {})
        required = fn.get("parameters", {}).get("required", [])
        param_parts = []
        for pname, pmeta in props.items():
            ptype = pmeta.get("type", "string")
            req = "required" if pname in required else "optional"
            param_parts.append(f"{pname}:{ptype}({req})")
        params_str = ", ".join(param_parts) if param_parts else "no params"
        tool_lines.append(f"- {name}({params_str}): {short_desc}")

    tools_list = "\n".join(tool_lines)
    return (
        "[TOOL CALLING — READ FIRST]\n"
        "LANGUAGE RULE: You MUST respond ONLY in Swedish. NEVER use Chinese, Arabic, or any other language. "
        "Every single word in your final answer must be Swedish.\n"
        "FORMAT RULE: Never use ### or ## markdown headers. Use emojis to organize sections instead "
        "(e.g. 🏃 Aktivitet, 💤 Sömn, 💓 Hjärta, ⚡ Kroppsbatteri, 😌 Stress).\n"
        "CRITICAL: If no tool is needed (e.g. greetings, simple questions), just reply naturally in Swedish. "
        "NEVER output phrases like 'No JSON function call required' or any internal reasoning. "
        "Only output JSON when calling a tool, otherwise just answer normally.\n"
        "You have access to tools. When the user asks about health, Garmin, weather, "
        "energy, calendar, Strava, Withings, or smart home — you MUST call the relevant tool. "
        "NEVER answer from memory when a tool exists for that topic.\n"
        "TOOL ROUTING RULES (follow exactly):\n"
        "  - 'självanalys', 'själv analys', 'analysera koden', 'self-analysis', 'self analysis', 'granska koden' → call: codex_audit_codebase (no arguments needed)\n"
        "  - 'spring', 'löpning', 'aktiviteter', 'strava' → call: get_strava_activities\n"
        "  - 'garmin', 'hälsa', 'sömn', 'hjärtfrekvens', 'steg' → call: get_garmin_health (DO NOT use for code analysis/självanalys)\n"
        "  - 'väder', 'temperatur', 'regn' → call: get_weather\n"
        "  - 'hem', 'lampor', 'home assistant' → call: homeassistant_control or homeassistant_service\n"
        "  - questions about documents, CV, personal letter, files, work history, or any uploaded content → call: query_knowledge_base with query=<exact user question>\n"
        "To call a tool respond with ONLY valid JSON (no other text, no markdown):\n"
        '{"name": "tool_name", "arguments": {"param": "value"}}\n'
        "IMPORTANT: The 'query' argument for query_knowledge_base must ALWAYS be the user's actual question verbatim. NEVER leave it empty.\n"
        "Example: user asks 'vad har jag jobbat med?' → respond with:\n"
        '{"name": "query_knowledge_base", "arguments": {"query": "vad har jag jobbat med?"}}\n'
        "Omit optional params you don't know. After [Result of tool ...] answer in Swedish.\n"
        "Available tools:\n"
        f"{tools_list}\n"
        "--- END TOOL INSTRUCTIONS ---\n\n"
    )

async def generate_ollama_response(
    model_id: str,
    system_prompt: str,
    history: List[Dict[str, Any]],
    user_msg: str,
    image_data: Optional[str] = None,
) -> str:
    """
    Generates a response using the Ollama /api/chat endpoint.
    Supports native tool_calls and a robust JSON-fallback for models like DeepSeek-R1.
    """
    ollama_url = get_credential("OLLAMA_URL") or settings.OLLAMA_URL
    base_url = ollama_url.rstrip("/")

    all_tools = registry.get_ollama_function_declarations()

    # Decide upfront whether to use fallback (skip wasted native-tools round-trip)
    use_fallback = _should_skip_native_tools(model_id)
    if use_fallback:
        logger.info(f"[Ollama] Skipping native tools for {model_id} (known incompatible).")

    # Build system prompts
    # Fallback: prepend tool header at top (most prominent position for LLM)
    tool_header = _build_tool_header(all_tools)
    native_system_prompt = system_prompt
    fallback_system_prompt = tool_header + system_prompt

    def _build_messages(fb: bool) -> List[Dict[str, Any]]:
        msgs: List[Dict[str, Any]] = []
        msgs.append({"role": "system", "content": fallback_system_prompt if fb else native_system_prompt})
        for msg in history:
            role = "user" if msg["role"] == "user" else "assistant"
            content = ""
            for part in msg.get("parts", []):
                if isinstance(part, str):
                    content += part
                elif hasattr(part, "text"):
                    content += part.text
                elif isinstance(part, dict) and "text" in part:
                    content += part["text"]
            if content:
                msgs.append({"role": role, "content": content})
        current: Dict[str, Any] = {"role": "user", "content": user_msg}
        if image_data:
            b64 = image_data.split(",", 1)[1] if "," in image_data else image_data
            current["images"] = [b64]
        msgs.append(current)
        return msgs

    messages = _build_messages(use_fallback)
    tools = all_tools[:]

    # Ollama model options — disable thinking chain if supported to save time
    # num_predict caps output tokens → faster responses for normal chat
    model_options: Dict[str, Any] = {"num_predict": 1000}
    if _should_use_think(model_id):
        model_options["think"] = False
        logger.info(f"[Ollama] Disabling think chain for {model_id} (think=false).")

    max_turns = 6
    final_text_response = ""

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            for turn in range(max_turns):
                payload: Dict[str, Any] = {
                    "model": model_id,
                    "messages": messages,
                    "stream": False,
                }
                if model_options:
                    payload["options"] = model_options
                if tools and not use_fallback:
                    payload["tools"] = tools

                logger.info(f"[Ollama] → {model_id} turn={turn + 1} fallback={use_fallback}")
                resp = await client.post(f"{base_url}/api/chat", json=payload)

                # --- Handle HTTP errors ---
                if resp.status_code != 200:
                    err_txt = resp.text
                    if tools and not use_fallback and (
                        "does not support tools" in err_txt
                        or "tool" in err_txt.lower()
                    ):
                        logger.warning(
                            f"[Ollama] {model_id} rejected tools — switching to JSON-fallback."
                        )
                        _FALLBACK_MODELS.add(model_id)  # cache so future calls skip this
                        tools = []
                        use_fallback = True
                        messages = _build_messages(use_fallback)
                        continue
                    return f"Ollama Error: {resp.status_code} - {err_txt}"

                data = resp.json()
                message = data.get("message", {})
                content_raw = message.get("content", "") or ""

                # ----------------------------------------------------------------
                # 1. Native tool_calls
                # ----------------------------------------------------------------
                native_tool_calls = message.get("tool_calls", [])

                # ----------------------------------------------------------------
                # 2. JSON fallback from content
                # ----------------------------------------------------------------
                parsed_tool_call = None
                if not native_tool_calls:
                    parsed_tool_call = _extract_tool_call(content_raw)
                    if parsed_tool_call:
                        logger.info(f"[Ollama] Parsed implicit tool call: {parsed_tool_call['name']}")

                # ----------------------------------------------------------------
                # 3. Execute tools
                # ----------------------------------------------------------------
                if native_tool_calls or parsed_tool_call:
                    messages.append({
                        "role": "assistant",
                        "content": "" if parsed_tool_call else content_raw,
                        **({"tool_calls": native_tool_calls} if native_tool_calls else {}),
                    })

                    calls_to_run = []
                    if native_tool_calls:
                        for tc in native_tool_calls:
                            fn = tc.get("function", {})
                            calls_to_run.append((fn.get("name"), fn.get("arguments", {})))
                    else:
                        calls_to_run.append((parsed_tool_call["name"], parsed_tool_call["arguments"]))

                    for fname, fargs in calls_to_run:
                        if not fname:
                            continue
                        # Resolve fuzzy/abbreviated tool names before execution
                        fname = _resolve_tool_name(fname)
                        # Strip null/None values — let registry defaults apply
                        if isinstance(fargs, dict):
                            fargs = {k: v for k, v in fargs.items() if v is not None}

                        # Safety net: if a tool requires 'query' but it's missing/empty,
                        # fall back to the user's original message so the tool can still run.
                        if isinstance(fargs, dict) and not fargs.get("query"):
                            tool_def = registry._tools.get(fname)
                            if tool_def and "query" in tool_def.args_schema.model_fields:
                                fargs["query"] = user_msg
                                logger.info(f"[Ollama] Injected user_msg as query for {fname}")

                        logger.info(f"[Ollama] Executing tool: {fname}({fargs})")
                        result_text = await registry.execute(fname, fargs)
                        result_str = str(result_text)

                        if "Error" in result_str or "Fel" in result_str or "not found" in result_str.lower():
                            result_str += "\n\n[SYSTEM HINT]: Tool error. Explain to the user in Swedish what went wrong."
                            if turn == max_turns - 1:
                                max_turns += 1

                        if native_tool_calls:
                            # Native tool_calls path (llama3.1, mistral, etc.)
                            # Ollama expects role:'tool' with bare result text — NOT role:'user'
                            messages.append({
                                "role": "tool",
                                "content": result_str,
                            })
                        else:
                            # JSON-fallback path (qwen, deepseek, etc.)
                            messages.append({
                                "role": "user",
                                "content": (
                                    f"[Result of tool '{fname}']: {result_str}\n\n"
                                    "Answer the user in Swedish based on this result."
                                ),
                            })

                    continue

                # ----------------------------------------------------------------
                # 4. Final response — strip think tags before returning
                # ----------------------------------------------------------------
                final_text_response = _strip_think_tags(content_raw)
                break

            if not final_text_response:
                final_text_response = "Error: Maximum tool turns exceeded or no response."

            return str(final_text_response)

    except Exception as e:
        err_msg = str(e) or repr(e)
        logger.error(f"[Ollama] Generation error: {err_msg}")
        return f"Error connecting to Ollama: {err_msg}"
