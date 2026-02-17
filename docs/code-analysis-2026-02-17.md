# Freja.io Deep Code Analysis and Optimization Proposal

Date: 2026-02-17
Scope: Backend (FastAPI/Socket.IO), skill system, tools, and React frontend integration points.

## Executive Summary

The current codebase has a strong product direction (multi-channel assistant + tool execution + skills), but it is currently blocked by severe merge corruption and environment reproducibility issues. Before optimization work, the highest-ROI action is to restore a stable baseline.

## Method Used

- Structural scan of repository layout.
- Static conflict marker detection.
- Python syntax compilation check.
- Test collection run to identify systemic reliability gaps.
- Targeted review of architectural hot paths (`main.py`, `chat_service`, `tool_registry`, `config`).

## Critical Findings (P0)

### 1) Unresolved merge conflicts across core runtime paths

The repository contains unresolved merge markers (`<<<<<<<`, `=======`, `>>>>>>>`) in critical backend and frontend files, including startup, chat orchestration, tool registry, settings pages, and requirements.

Impact:
- Production startup can fail immediately due to syntax errors.
- Tool execution path is not trustworthy.
- Dependency installation metadata is invalid.
- Frontend build is likely unstable where conflicts exist.

Recommendation:
1. Create a dedicated "conflict resolution" PR.
2. Resolve conflicts with explicit product decisions (not auto-merge).
3. Add CI guard: fail if conflict markers are detected.

### 2) Python compilation currently fails in multiple modules

Compilation check shows syntax failures in core modules (`main.py`, `app/core/*`, `app/services/*`, `app/tools/*`).

Impact:
- Any deployment/test run is blocked.
- Regression signal is masked because code does not import cleanly.

Recommendation:
- Add `python -m compileall -q app main.py` as a mandatory CI pre-test gate.

### 3) Dependency reproducibility is broken

Test collection failed with missing key packages (e.g., `fastapi`, `python-dotenv`, `loguru`, `httpx`) in addition to syntax issues.

Impact:
- Engineering cannot trust local or CI parity.
- False negatives/positives in tests.

Recommendation:
- Resolve `requirements.txt` conflicts.
- Add lock strategy (`pip-tools` or `uv lock`).
- Add bootstrap command in docs and CI (`pip install -r requirements.txt`).

## Architectural Analysis

### A) Startup and app assembly are over-concentrated

`main.py` currently mixes lifecycle boot logic, websocket setup, router mounting, static file serving, and event handlers.

Risk:
- Hard to test startup independently.
- Hard to reason about side effects (e.g., double initialization risk).
- Increased change blast radius.

Optimization proposal:
- Introduce app factory pattern:
  - `app/factory.py` for FastAPI creation.
  - `app/startup.py` for lifecycle wiring.
  - `app/socket/events.py` for Socket.IO handlers.
  - `app/web/static_routes.py` for frontend serving.

### B) Chat orchestration has too many responsibilities

`UnifiedChatService.process_message` handles:
- model selection,
- user memory extraction,
- prompt composition,
- mem0 retrieval,
- Gemini tool loop,
- fallback web retrieval,
- persistence.

Risk:
- Hard to unit test edge cases.
- Hard to optimize latency per stage.
- Failure in one stage affects all stages.

Optimization proposal:
- Split into composable services:
  - `PromptBuilder`
  - `ConversationMemoryService`
  - `ToolLoopExecutor`
  - `FallbackAnswerService`
- Add per-stage timing/metrics.

### C) Tool schema transformation is runtime-recursive and fragile

`ToolRegistry.get_gemini_function_declarations` recursively rewrites JSON schema at runtime.

Risk:
- Performance overhead per request if recalculated frequently.
- Higher risk of schema mismatch edge cases (`anyOf`, optional/null, nested definitions).

Optimization proposal:
- Cache transformed declaration per tool registration hash.
- Validate transformed schema in tests with fixtures.
- Add strict contract tests for optional arguments and nested objects.

## Performance and Optimization Proposals

### 1) Introduce cold-start and request-path caches

- Cache tool declarations once after skill discovery.
- Cache system prompt if it is static per process.
- Add short TTL cache for mem0 retrieval and web fallback where safe.

Expected effect:
- Lower median latency in chat path.
- Reduced repeated schema processing overhead.

### 2) Constrain and instrument tool loop

Current max loop turn strategy is static and may be increased dynamically on errors.

Optimization proposal:
- Keep strict max cap (no dynamic growth in same request).
- Track per-tool success/error rate.
- Short-circuit repeated identical failing tool calls.

Expected effect:
- Lower tail latency and reduced token/tool waste.

### 3) Improve async boundary handling

`run_in_executor` is used around synchronous model generation. Evaluate asynchronous SDK APIs where stable.

Optimization proposal:
- Prefer fully async path when available.
- Use bounded executor pools for blocking fallback paths.

Expected effect:
- Better throughput under concurrent sessions.

## Reliability and Security Improvements

1. Add pre-commit hooks:
   - conflict marker check
   - Ruff + formatting
   - basic compile check
2. Add CI pipeline stages:
   - install
   - compile
   - unit tests
   - optional integration tests
3. Narrow broad exception handlers and include structured context IDs.
4. Define timeout and retry policy centrally for all network integrations.

## Suggested Implementation Plan

### Phase 0 (Immediate Stabilization)
- Resolve merge conflicts in all affected files.
- Restore successful compile baseline.
- Restore deterministic dependency installation.

### Phase 1 (Testability)
- Refactor `main.py` into app factory modules.
- Split chat service responsibilities.
- Add unit tests for prompt build + tool loop.

### Phase 2 (Optimization)
- Cache tool declarations and prompt components.
- Add metrics (latency, token/tool usage, error rates).
- Tune retries/timeouts with data.

### Phase 3 (Hardening)
- Add rate limits and circuit breaker for external providers.
- Add synthetic health checks for major integrations.
- Add deployment smoke test workflow.

## Practical Quick Wins (This Week)

1. Add CI job to fail on conflict markers.
2. Add compile gate before pytest.
3. Split startup wiring from route declarations.
4. Add a single observability dashboard with:
   - request latency p50/p95
   - tool call success ratio
   - external provider timeout ratio

## Final Assessment

Freja.io has the right product architecture direction, but currently needs a stabilization pass before deeper optimization. Once the codebase is conflict-free and build-consistent, modularization of startup/chat orchestration plus targeted caching and telemetry will produce the largest near-term reliability and performance gains.
