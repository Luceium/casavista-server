import os
from api.generate.generate import ModelService
from flask import  Flask, send_file, abort, jsonify, g

import logging
from flask import (
    Blueprint
)

import logging
import os
from PIL import Image




bp_name = 'api-generate'
bp_url_prefix = '/api/generate'
bp = Blueprint(bp_name, __name__, url_prefix=bp_url_prefix)

logger = logging.getLogger("myapp")


# Initialize global service
model_service = ModelService()

@bp.route("/generate/<string:object_name>", methods=["GET"])
def generate_model(
    object_name,
    foreground_ratio=0.85,
    texture_resolution=1024,
    remesh_option="none",
    target_count=2000,
):
    logging.info(f"Request received: {object_name}")
    output_dir = "output/"
    object_dir = os.path.join(output_dir, object_name)
    object_file_path = f"{object_dir}/{object_name}.glb"

    # Check if the object file already exists
    if os.path.isdir(object_dir) and os.path.isfile(object_file_path):
        return send_file(
            object_file_path,
            as_attachment=True,
            download_name=f"{object_name}.glb",
        )

    try:
        # Read and convert image
        image_path = "castle.png"  # Replace with the actual image input
        pil_image = Image.open(image_path).convert("RGBA")

        os.makedirs(object_dir, exist_ok=True)
        temp_image_path = f"{object_dir}/{object_name}.png"
        pil_image.save(temp_image_path, format="PNG")

        # Process the image and generate the model
        result = model_service.process_image(
            pil_image,
            object_name,
            foreground_ratio,
            texture_resolution,
            remesh_option,
            target_count,
        )

        logging.info("3D model generated!")

        # Return the generated 3D model file
        return send_file(
            result["mesh_path"],
            as_attachment=True,
            download_name=f"{object_name}.glb",
        )

    except Exception as e:
        logging.error(f"Error during model generation: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
