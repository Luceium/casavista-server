import os
from flask import  Flask, send_file, abort, jsonify, g

import logging
from flask import (
    Blueprint,
    request
)

from io import BytesIO
import logging
import os
from PIL import Image
from PIL import Image



bp_name = 'api-generate'
bp_url_prefix = '/api/generate'
bp = Blueprint(bp_name, __name__, url_prefix=bp_url_prefix)

logger = logging.getLogger("myapp")



@bp.route("/<object_name>", methods=["GET"])
def generate_model():
    return True