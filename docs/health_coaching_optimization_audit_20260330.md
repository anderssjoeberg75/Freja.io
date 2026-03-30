# Health Coaching Optimization Audit — 2026-03-30

## Scope
This audit focused on runtime paths that affect Freja's ability to deliver high-quality, personalized health coaching:

- `app/services/chat_service.py`
- `skills/garmin/tools.py` and `skills/garmin/core.py`
- `skills/fitbit/tools.py` and `skills/fitbit/core.py`
- `skills/withings/tools.py` and `skills/withings/core.py`
- `app/core/prompts.py`

## Key Findings

1. **Personalization was mostly reactive, not proactive.**
   The LLM could call health tools, but only after deciding to do so in the tool loop. This can miss coaching opportunities when users ask broad questions like "How should I train today?".

2. **No cross-source health context summary in system prompt.**
   Garmin/Fitbit/Withings data existed, but there was no compact "health snapshot" pre-injected into the prompt for coaching-oriented turns.

3. **Token usage risk from raw payloads.**
   Health payloads are often large. Returning full JSON repeatedly in a conversation can increase latency and reduce answer quality.

4. **Tool descriptions encourage use but do not guarantee execution.**
   Even with strong tool descriptions, LLM routing can still skip relevant tools, especially for vague user prompts.

## Optimization Implemented

### Proactive Health Context Injection
A new pre-tool optimization was added in `UnifiedChatService`:

- Detects health intent using multilingual keyword matching.
- Fetches Garmin, Withings, and Fitbit data concurrently with a timeout.
- Compresses each source into a compact metric line (steps, sleep, stress, heart rate, body battery, weight, etc.).
- Injects the snapshot into the system block before model generation.

### Why this improves outcomes

- **Higher coaching quality:** The model receives relevant biometric context before producing first-pass advice.
- **Lower hallucination risk:** Guidance can reference actual measurements rather than assumptions.
- **Lower latency variance:** Compact summaries reduce unnecessary prompt bloat compared to full payload replay.
- **Graceful degradation:** Missing integrations/timeouts are skipped silently; the chat flow continues.

## Next Recommended Optimizations

1. **Introduce trend deltas (7-day / 30-day):**
   Add moving averages and direction signals (e.g., sleep trend ↓, resting HR trend ↑) to improve guidance quality.

2. **Risk guardrails for coaching:**
   Add a rule layer that blocks unsafe advice patterns and enforces "consult a professional" language on red-flag vitals.

3. **Source freshness metadata:**
   Include `source_timestamp` and `age_minutes` for each provider so the model can explicitly handle stale data.

4. **Metric normalization layer:**
   Normalize naming/units across Garmin/Fitbit/Withings to simplify model reasoning and reduce prompt complexity.

5. **Health-coaching eval set:**
   Add scripted regression prompts and expected response properties (mentions sleep/stress/actionable plan) to prevent quality regressions.

## Validation Checklist

- [x] Health intent detection triggers only on relevant prompts.
- [x] Snapshot fetch is non-blocking with bounded timeout.
- [x] Empty/error provider responses do not break chat generation.
- [x] Prompt stays compact and coaching-focused.
