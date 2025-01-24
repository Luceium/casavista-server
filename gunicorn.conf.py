import gunicorn.http.wsgi
from functools import wraps

from common.utils import safe_get_env_var
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the port dynamically, falling back to 6060
myport = safe_get_env_var('PORT', default='6060')

# WSGI application path
wsgi_app = "api.wsgi:app"

# Bind Gunicorn to all IPs on the defined port
bind = f"0.0.0.0:{myport}"

# Number of worker processes (you might want to tune this based on the system's CPU cores)
workers = 1  # Adjust according to your CPU (e.g., multiprocessing.cpu_count() * 2 + 1)

# Timeout for workers (adjust based on your app's response times)
timeout = 120  # in seconds

loglevel = "debug"
errorlog = "-"  # Output errors to stderr

# Function to remove 'Server' header from responses for security reasons
def wrap_default_headers(func):
    @wraps(func)
    def default_headers(*args, **kwargs):
        return [header for header in func(*args, **kwargs) if not header.startswith('Server: ')]
    return default_headers

# Apply the header modification to Gunicorn's default headers
gunicorn.http.wsgi.Response.default_headers = wrap_default_headers(gunicorn.http.wsgi.Response.default_headers)
