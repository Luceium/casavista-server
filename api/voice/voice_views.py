from flask import  jsonify

import logging
from flask import (
    Blueprint,
    request
)

from api.utils import  handle_api_error


bp_name = 'api-voice'
bp_url_prefix = '/api/voice'
bp = Blueprint(bp_name, __name__, url_prefix=bp_url_prefix)

logger = logging.getLogger("myapp")


