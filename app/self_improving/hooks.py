"""Hook handlers for UserPromptSubmit and PostToolUse self-improvement automation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.self_improving.memory_logger import MemoryEntry, SelfImprovingMemoryLogger


def _contains_any(text: str, markers: list[str]) -> bool:
    """Return True when at least one marker phrase appears in the lowercase text."""
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def handle_user_prompt_submit(user_prompt: str, project_root: str = ".") -> list[str]:
    """Inspect user prompts for learning/feature signals and log matching entries."""
    logger = SelfImprovingMemoryLogger(project_root=project_root)
    created_ids: list[str] = []

    learning_markers = [
        "you are wrong",
        "that is wrong",
        "incorrect",
        "du har fel",
        "det är fel",
        "wrong answer",
        "not correct",
    ]
    feature_markers = [
        "feature request",
        "missing feature",
        "should support",
        "please add",
        "saknar",
        "lägg till",
    ]

    if _contains_any(user_prompt, learning_markers):
        created_ids.append(
            logger.log_entry(
                MemoryEntry(
                    entry_type="learning",
                    title="User reported incorrect assistant behavior",
                    summary="The user indicated the assistant response was incorrect.",
                    details=f"Original prompt/feedback: {user_prompt}",
                    source="UserPromptSubmit",
                    area="assistant-quality",
                    priority="high",
                )
            )
        )

    if _contains_any(user_prompt, feature_markers):
        created_ids.append(
            logger.log_entry(
                MemoryEntry(
                    entry_type="feature",
                    title="User requested missing capability",
                    summary="The user asked for a capability not currently available.",
                    details=f"Feature request context: {user_prompt}",
                    source="UserPromptSubmit",
                    area="product-gap",
                    priority="medium",
                )
            )
        )

    return created_ids




def _safe_json_loads(raw: str) -> dict[str, Any]:
    """Parse JSON payloads defensively and fall back to a raw envelope on invalid input."""
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
        return {"value": parsed}
    except json.JSONDecodeError:
        cleaned = raw.strip()
        if cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
            return {"value": parsed}
        except json.JSONDecodeError:
            return {"raw": raw}


def handle_post_tool_use(
    tool_name: str,
    tool_args: dict[str, Any],
    result: dict[str, Any],
    project_root: str = ".",
) -> str | None:
    """Log ERROR entries when tool execution result indicates a failure state."""
    logger = SelfImprovingMemoryLogger(project_root=project_root)
    ok = bool(result.get("ok", False))
    if ok:
        return None

    text_output = str(result.get("text") or result.get("error") or "Unknown tool failure")
    return logger.log_entry(
        MemoryEntry(
            entry_type="error",
            title=f"Tool execution failure: {tool_name}",
            summary="A tool call finished in a failed state.",
            details=(
                f"Tool: {tool_name}\n"
                f"Arguments: {json.dumps(tool_args, ensure_ascii=False)}\n"
                f"Output/Error: {text_output}"
            ),
            source="PostToolUse",
            area="tooling",
            priority="high",
        )
    )


def _main() -> int:
    """CLI entrypoint for shell wrappers to activate hooks without duplicating logic."""
    parser = argparse.ArgumentParser(description="Self-improving hook runner")
    subparsers = parser.add_subparsers(dest="event", required=True)

    user_parser = subparsers.add_parser("UserPromptSubmit")
    user_parser.add_argument("--prompt", required=True)
    user_parser.add_argument("--project-root", default=".")

    tool_parser = subparsers.add_parser("PostToolUse")
    tool_parser.add_argument("--tool-name", required=True)
    tool_parser.add_argument("--tool-args", default="{}")
    tool_parser.add_argument("--result", required=True)
    tool_parser.add_argument("--project-root", default=".")

    pending_parser = subparsers.add_parser("ListPending")
    pending_parser.add_argument("--project-root", default=".")

    promote_parser = subparsers.add_parser("PromoteLearning")
    promote_parser.add_argument("--learning-id", required=True)
    promote_parser.add_argument("--rationale", default="")
    promote_parser.add_argument("--project-root", default=".")

    args = parser.parse_args()

    if args.event == "UserPromptSubmit":
        created = handle_user_prompt_submit(args.prompt, project_root=args.project_root)
        print(json.dumps({"created": created}, ensure_ascii=False))
        return 0

    if args.event == "PostToolUse":
        tool_args = _safe_json_loads(args.tool_args)
        result = _safe_json_loads(args.result)
        created_id = handle_post_tool_use(args.tool_name, tool_args, result, project_root=args.project_root)
        print(json.dumps({"created": created_id}, ensure_ascii=False))
        return 0

    if args.event == "ListPending":
        logger = SelfImprovingMemoryLogger(project_root=args.project_root)
        print(json.dumps(logger.list_pending(), ensure_ascii=False, indent=2))
        return 0

    if args.event == "PromoteLearning":
        logger = SelfImprovingMemoryLogger(project_root=args.project_root)
        promoted = logger.promote_learning(args.learning_id, rationale=args.rationale)
        print(json.dumps({"promoted": promoted}, ensure_ascii=False))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(_main())
