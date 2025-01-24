from flask import jsonify
from functools import wraps
 # for secure random generation

def handle_api_error(f):
    """Decorator to handle API errors consistently."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": "Internal server error", "details": str(e)}), 500
    return decorated_function