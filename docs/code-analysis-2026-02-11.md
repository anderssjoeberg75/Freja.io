# Code Analysis of Freja.io

Date: 2026-02-11

## Overview
The project has a solid base structure (FastAPI + Socket.IO backend and React client), but there are several risk areas affecting reliability, security, and maintainability.

## Prioritized Improvements

### P0 — Critical Issues (address immediately)

1. **`base_system_prompt` was used before initialization** in `stream_response`, which risked runtime errors.
   - File: `app/services/llm_handler.py`.
   - Recommendation: initialize prompt at function start via `get_system_prompt()` and use a local immutable flow.

2. **Overly permissive CORS settings in production defaults** (`"*"` previously allowed with credentials).
   - File: `main.py` + `app/core/config.py`.
   - Recommendation: drive allowed origins from config (`ALLOWED_ORIGINS`) and avoid wildcards in production.

3. **Safety filters configured with permissive thresholds** (`BLOCK_NONE`) in model flows.
   - Files: `app/services/llm_handler.py`, `app/routers/chat.py`.
   - Recommendation: set stricter production thresholds and gate relaxed behavior behind env flags.

### P1 — High Priority (stability and observability)

4. **Broad exception handling (`except:` / generic swallowing)** hides root causes.
   - Files: multiple modules including service and router layers.
   - Recommendation: catch explicit exception types where possible and log contextual diagnostics.

5. **Mutable default argument (`history=[]`)** in LLM service API.
   - File: `app/services/llm_service.py`.
   - Recommendation: use `history: list | None = None` and initialize locally.

6. **Global Socket.IO session state without a dedicated manager** can create race/lifecycle edge cases.
   - File: `main.py`.
   - Recommendation: move to a session manager abstraction with cleanup/TTL/reconnect handling.

### P2 — Medium Priority (architecture and quality)

7. **`main.py` is too monolithic** (startup, middleware, routes, static serving, socket handlers in one file).
   - Recommendation: split into `app_factory`, `socket_handlers`, and static route modules.

8. **Hardcoded project sync path in Docker executor** (`/opt/mainframe`) reduces portability.
   - File: `app/tools/code_executor.py`.
   - Recommendation: resolve from runtime base path/config.

9. **Known technical debt markers (`TODO`) in core flows** (tool schema introspection, voice handshake, proactive logic).
   - Recommendation: create a tracked implementation roadmap with owners and acceptance criteria.

## Suggested 4-Sprint Plan

### Sprint 1 — Stability/Security
- Ensure prompt initialization across all LLM entry points.
- Harden CORS and environment-specific defaults.
- Replace fragile exception handling in critical paths.
- Add centralized error handling + correlation IDs in logs.

### Sprint 2 — Architecture
- Break down `main.py` into focused modules.
- Introduce a `SessionManager` for chat/voice lifecycle.
- Define and validate tool contracts (Pydantic schemas).

### Sprint 3 — Test Coverage
- Add unit tests for:
  - prompt composition
  - tool payload parsing
  - socket session lifecycle
- Add integration tests for `/health`, chat route, and socket handshake.

### Sprint 4 — Operations/Observability
- Add metrics (latency per model/tool, failure rate, cost visibility).
- Introduce structured logs and dashboards.
- Add rate limiting and stricter input validation for external calls.

## Quick Wins
- Keep prompt initialization explicit at entry points.
- Keep mutable defaults out of public APIs.
- Keep CORS origin list explicit and environment-driven.
- Replace top bare exception handlers with actionable logging.

## Summary
The codebase is promising and functional, but a few concentrated fixes deliver high value quickly: robust prompt handling, safer defaults, stronger error observability, and cleaner application modularization.
