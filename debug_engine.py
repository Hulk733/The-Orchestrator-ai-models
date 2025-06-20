import traceback

def auto_fix(output):
    try:
        return output
    except Exception as e:
        log_error(e)
        return "[DebugEngine] Issue encountered and logged."

def log_error(error):
    with open("core/logs/debug_tracebacks.log", "a") as f:
        f.write(traceback.format_exc())
        f.write("\n---\n")
