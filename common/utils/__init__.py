from os import getenv
from dotenv import load_dotenv

# add logger
import logging

import json

load_dotenv()
logger = logging.getLogger(__name__)
# set logger to standard out
logger.addHandler(logging.StreamHandler())
# set log level
logger.setLevel(logging.INFO)

def safe_get_env_var(key, default=None):
    try:
        return getenv(key, default)
    except KeyError:
        logger.warning(f"Missing {key} environment variable. Setting default to CHANGEMEPLS")
        # return "CHANGEMEPLS"
        # ^^ Do this so any ENVs not set in production won't crash the server
        #     
        raise NameError(f"Missing {key} environment variable.")
# Example usage
def load_cert_config():
    raw_config = safe_get_env_var("FIREBASE_CERT_CONFIG")
    if raw_config == "CHANGEMEPLS":
        raise ValueError("FIREBASE_CERT_CONFIG is not set properly")
    
    # Replace single quotes with double quotes if necessary (as a temporary fix)
    # if raw_config.startswith('{') and '"' in raw_config:
    #     raw_config = raw_config.replace('"', "'")

    try:
        cert_env = json.loads(raw_config)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing FIREBASE_CERT_CONFIG: {e}")
        raise

    return cert_env
