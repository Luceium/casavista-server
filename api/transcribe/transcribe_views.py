import logging

from flask import jsonify, make_response, render_template
from werkzeug.exceptions import BadRequest

from api.utils import check_fields_in_request, handle_response_exception
import tempfile
from .transcribe import *
from flask import (
    Blueprint,
    request
)

bp_name = 'api-transcribe'
bp_url_prefix = '/api/transcribe'
bp = Blueprint(bp_name, __name__, url_prefix=bp_url_prefix, template_folder='templates', static_folder='static')

logger = logging.getLogger("myapp")

@bp.route("/test", methods=['POST'])
# @auth_guard
def test():
    logger.info("Received request to /api/transcribe/test")
    data = {"message": "transcribe works well"}
    return jsonify(data), 200

@bp.route("/openai", methods=['POST'])
# @auth_guard
def openai_transcribe():
    request_data = request.get_json()
    check_fields_in_request(request_data, ["filePath"])
    file_path = request_data.get("filePath").strip()

    try:
        # in the form of {'transcript': transcript, 'segments': transcript.segments}
        result = transcribe_large_audio(file_path=file_path)
        data = {"message": "transcription successful", "data": result}
        return jsonify(data), 200
    
    except Exception as e:
        return handle_response_exception(e)

# @bp.route("/whisper", methods=['POST'])
# # @auth_guard
# def whisper_transcribe():
#     request_data = request.get_json()
#     check_fields_in_request(request_data, ["filePath"])
#     file_path = request_data.get("filePath").strip()

#     try:
#         # in the form of {'transcript': transcript, 'segments': transcript.segments}
#         result = transcribe_with_local_whisper(file_path=file_path)
#         data = {"message": "transcription successful", "data": result}
#         return jsonify(data), 200
    
#     except Exception as e:
#         return handle_response_exception(e)
@bp.route("/faster-whisper", methods=['POST'])
# @auth_guard
def faster_whisper_transcribe():
    request_data = request.get_json()
    logger.info(f"Received request with data: {request_data}")

    file_path = request_data.get("filePath")
    logger.info(f"File path received: {file_path}")
    
    # Validate input
    if not file_path:
        logger.error("error: File path is missing")
        return jsonify({"error": "File path is missing"}), 400

    # Handle URL or local file
    if file_path.startswith("http://") or file_path.startswith("https://"):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_path)[1]) as temp_file:
                response = requests.get(file_path, stream=True)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
        except Exception as e:
            logger.error("error: Failed download is missing")
            return jsonify({"error": f"Failed to download file: {str(e)}"}), 400
    else:
        temp_file_path = file_path

    # Validate file exists
    if not os.path.exists(temp_file_path):
        logger.error("file not found")
        return jsonify({"error": f"File not found: {temp_file_path}"}), 400

    try:
        # Transcribe file
        result = transcribe_with_faster_whisper(file_path=temp_file_path, compute_type="default")
        
        # Ensure the result is properly returned in the response
        return jsonify({"message": "Transcription successful", "data": result}), 200
    except Exception as e:
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
    finally:
        if file_path.startswith("http://") or file_path.startswith("https://"):
            os.remove(temp_file_path)
