##########################################
# External Modules
##########################################

from flask import Flask, request
from flask_cors import CORS
from flask_talisman import Talisman
import logging.config
import os

# Specify the directory for log files within the container
# log_dir = "/app/logs"

# Specify the directory for log files within the container
log_dir = "/home/developer/app/logs"

# Ensure the log directory exists
os.makedirs(log_dir, exist_ok=True)

dict_config = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] {%(pathname)s:%(funcName)s:%(lineno)d} %(levelname)s - %(message)s',
        }
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'formatter': 'default',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(log_dir, "test.log"),
            'maxBytes': 5000000,
            'backupCount': 10
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'default',
        },
    },
    'loggers': {
        'myapp': {
            'handlers': ["console", "default"],  # Added the 'default' handler
            'level': 'DEBUG',
        },
    }
}

logger = logging.getLogger("myapp")
logging.config.dictConfig(dict_config)



from api import exception_views
from api.voice import voice_views
from api.generate import generate_views
from common.utils import safe_get_env_var


def create_app():
    ##########################################
    # Environment Variables
    ##########################################
    client_origin_url = safe_get_env_var("CLIENT_ORIGIN_URL")

    ##########################################
    # Flask App Instance
    ##########################################

    app = Flask(__name__, instance_relative_config=True)
    logger.info("Started Flask")



    ##########################################
    # HTTP Security Headers
    ##########################################

    csp = {
    'default-src': ['\'self\''],
    'frame-ancestors': ['\'none\''],
    # 'font-src': ['\'self\'', 'https://fonts.googleapis.com'],
   
    'font-src': ['\'self\'', ' https://fonts.gstatic.com'],
    'img-src': ['\'self\'', 'https://github-production-user-asset-6210df.s3.amazonaws.com'],
    'style-src': ['\'self\'', 'https://fonts.googleapis.com']
    }

    Talisman(
        app,
        force_https=False,
        frame_options='DENY',
        content_security_policy=csp,
        referrer_policy='no-referrer',
        x_xss_protection=False,
        x_content_type_options=True
    )


    @app.after_request
    def add_headers(response):
        client_origin_url = safe_get_env_var("CLIENT_ORIGIN_URL")
        if client_origin_url == "*":
            logger.debug(
                "Using wildcard for Access-Control-Allow-Origin - pretty dangerous, just for development purposes only")
            response.headers['Access-Control-Allow-Origin'] = "*"

        response.headers['X-XSS-Protection'] = '0'
        response.headers['Cache-Control'] = 'no-store, max-age=0, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Only set Content-Type to application/json if the response is JSON
        if response.content_type == 'application/json':
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
        
        # Set Content-Type for CSS files
        if request.path.endswith('.css'):
            response.headers['Content-Type'] = 'text/css'
        return response

    ##########################################
    # CORS
    ##########################################

    if client_origin_url == "*":
        logger.debug(
            "Using wildcard for CORS client_origin_url - pretty dangerous, just for development purposes only")
        CORS(app)
    else:
        logger.debug(
            f"Using {client_origin_url} for CORS client_origin_url")
        CORS(
            app,
            resources={r"/api/*": {"origins": client_origin_url}},
            allow_headers=["Authorization", "Content-Type"],
            methods=["GET", "POST", "PATCH", "DELETE"],
            max_age=86400
        )

    ##########################################
    # Blueprint Registration
    ##########################################
    app.register_blueprint(exception_views.bp)
    app.register_blueprint(voice_views.bp)
    app.register_blueprint(generate_views.bp)
    return app
