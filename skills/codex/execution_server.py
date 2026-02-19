import sys
import io
import contextlib
import traceback
from flask import Flask, request, jsonify

app = Flask(__name__)

# Global execution context
GLOBAL_CONTEXT = {}

@app.route('/execute', methods=['POST'])
def execute_code():
    data = request.get_json()
    code = data.get('code', '')
    
    if not code:
        return jsonify({"output": "", "error": "No code provided", "exit_code": 1}), 400

    # Capture stdout/stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    exit_code = 0
    error_msg = ""
    
    try:
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            exec(code, GLOBAL_CONTEXT)
    except Exception:
        exit_code = 1
        error_msg = traceback.format_exc()
        # Print error to stderr capture as well so it appears in logs
        print(error_msg, file=stderr_capture)
    
    output = stdout_capture.getvalue()
    errors = stderr_capture.getvalue()
    
    # Combine or separate?
    # Usually tool expects combined "output", but separating is better for structure.
    # For now, append errors to output for compatibility.
    full_output = output
    if errors:
        full_output += f"\n--- Errors ---\n{errors}"

    return jsonify({
        "output": full_output,
        "stdout": output,
        "stderr": errors,
        "exit_code": exit_code
    })

@app.route('/reset', methods=['POST'])
def reset_context():
    global GLOBAL_CONTEXT
    GLOBAL_CONTEXT = {}
    return jsonify({"status": "Context reset"})

if __name__ == '__main__':
    # Listen on localhost inside the container
    app.run(host='0.0.0.0', port=5000)
