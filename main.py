# main.py
# from cache_utils import CacheServer
from io import BytesIO
import random
import logging
import os
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import torch
import numpy as np
import requests
from PIL import Image
import rembg
import xatlas
import uvicorn
import io
from PIL import Image
from transparent_background import Remover

from spar3d.system import SPAR3D
from spar3d.utils import remove_background, foreground_crop
# from dotenv import load_dotenv
# import boto3

# load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

app = FastAPI(title="3D Model Generation API")

class ModelService:
    def __init__(
        self,
        device: str = "cuda:0",
        model_path: str = "stabilityai/stable-point-aware-3d",
        chunk_size: int = 8192,
        output_dir: str = "output/",
    ):
        self.device = "cpu" if not torch.cuda.is_available() else device
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize model
        logging.info("Initializing model...")
        self.model = SPAR3D.from_pretrained(
            model_path, config_name="config.yaml", weight_name="model.safetensors"
        )
        self.model.to(self.device)
        self.model.eval()

        # Initialize background remover
        self.bg_remover = Remover(device=self.device)
        logging.info("Model service initialized successfully")

    async def process_image(
        self,
        image: Image.Image,
        object_name: str,
        foreground_ratio: float = 0.85,
        texture_resolution: int = 1024,
        remesh_option: str = "none",
        target_count: int = 2000,
    ) -> dict:
        # Create output directory for this job
        job_dir = self.output_dir / object_name
        job_dir.mkdir(exist_ok=True)

        # Process image
        image = remove_background(image, self.bg_remover)
        image = foreground_crop(image, foreground_ratio)
        image.save(job_dir / f"{object_name}.png")

        # Generate 3D model
        with torch.no_grad():
            with torch.autocast(device_type=self.device, dtype=torch.bfloat16):
                mesh, glob_dict = self.model.run_image(
                    [image],
                    bake_resolution=texture_resolution,
                    remesh=remesh_option,
                    vertex_count=target_count,
                    return_points=True,
                )

        # Save mesh and point cloud
        mesh_path = job_dir / f"{object_name}.glb"
        mesh.export(mesh_path, include_normals=True)
        points_path = job_dir / f"{object_name}.ply"
        glob_dict["point_clouds"][0].export(points_path)

        return {
            "mesh_path": str(mesh_path),
            "points_path": str(points_path),
        }

# Initialize model service at startup
model_service = None

@app.on_event("startup")
async def startup_event():
    print("")
    global model_service
    model_service = ModelService()

@app.get("/generate/{object_name}")
async def generate_model(
    object_name: str,
    foreground_ratio: float = 0.85,
    texture_resolution: int = 1024,
    remesh_option: str = "none",
    target_count: int = 2000,
):

    print(f"request received: {object_name}")
    output_dir = "output/"
    object_dir = os.path.join(output_dir, object_name)

    # Check if folder with the object name exists
    if os.path.isdir(object_dir):
        return FileResponse(
            f"{object_dir}/{object_name}.glb",
            filename=f"{object_name}.glb",
        )
    try:
        # Read and convert image
        image_path = "castle.png"
        pil_image = Image.open(image_path).convert("RGBA")

        os.makedirs(f"output/{object_name}", exist_ok=True)
        temp_image_path = f"output/{object_name}/{object_name}.png"
        pil_image.save(temp_image_path, format="PNG")

        # Process image and generate model
        result = await model_service.process_image(
            pil_image,
            object_name,
            foreground_ratio,
            texture_resolution,
            remesh_option,
            target_count,
        )

        logging.info("3D model generated!!!")

        return FileResponse(
            result["mesh_path"],
            filename=f"{object_name}.glb",
        )

    except Exception as e:
        logging.error("Error during model generation: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)