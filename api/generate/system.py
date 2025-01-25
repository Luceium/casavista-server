from flask import Flask, jsonify, send_file, request, abort
from io import BytesIO
import logging
import os
from pathlib import Path
from PIL import Image
import torch
import rembg
import xatlas
from transparent_background import Remover
from spar3d.system import SPAR3D
from spar3d.utils import remove_background, foreground_crop

# Logging Configuration
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

app = Flask(__name__)

# Mock ModelService for example
class ModelService:
    def process_image(self, pil_image, object_name, foreground_ratio, texture_resolution, remesh_option, target_count):
        # Replace with actual logic
        output_dir = f"output/{object_name}"
        os.makedirs(output_dir, exist_ok=True)
        mesh_path = f"{output_dir}/{object_name}.glb"
        # Generate a dummy .glb file (replace with real logic)
        with open(mesh_path, "w") as f:
            f.write("Dummy 3D model content")
        return {"mesh_path": mesh_path}

# Initialize global service
model_service = ModelService()

@app.route("/generate/<string:object_name>", methods=["GET"])
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

if __name__ == "__main__":
    # Run the Flask app
    app.run(host="0.0.0.0", port=8000, debug=True)
