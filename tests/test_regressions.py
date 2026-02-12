import ast
from pathlib import Path


def _parse(path: str) -> ast.AST:
    return ast.parse(Path(path).read_text())


def test_llm_service_generate_response_has_no_mutable_default():
    tree = _parse("app/services/llm_service.py")

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "generate_response":
            defaults = node.args.defaults
            assert defaults, "Expected defaults for optional parameters"
            assert not any(isinstance(default, ast.List) for default in defaults)
            return

    raise AssertionError("generate_response function was not found")


def test_socketio_server_uses_configured_allowed_origins():
    tree = _parse("main.py")

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if not any(isinstance(t, ast.Name) and t.id == "sio" for t in node.targets):
                continue
            if not isinstance(node.value, ast.Call):
                continue

            call = node.value
            if not (isinstance(call.func, ast.Attribute) and call.func.attr == "AsyncServer"):
                continue

            cors_kw = next((kw for kw in call.keywords if kw.arg == "cors_allowed_origins"), None)
            assert cors_kw is not None, "Expected cors_allowed_origins keyword"
            assert isinstance(cors_kw.value, ast.Call), "Expected get_allowed_origins() call"
            assert isinstance(cors_kw.value.func, ast.Name), "Expected direct function call"
            assert cors_kw.value.func.id == "get_allowed_origins"
            return

    raise AssertionError("sio AsyncServer assignment was not found")
