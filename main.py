# main.py
# from cache_utils import CacheServer
from io import BytesIO
import random
import logging
import os
from contextlib import nullcontext
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

from utils import clean_image, save_image, save_mesh, save_points, search
# from dotenv import load_dotenv
# import boto3

# load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

app = FastAPI(title="3D Model Generation API")

# Initialize model service at startup
model_service = None

@app.on_event("startup")
async def startup_event():
    logging.info("Starting up...")
    global model_service
    model_service = ModelService()

@app.get("/generate/{obj_desc}")
async def get_or_generate_model(
    obj_desc: str,
    foreground_ratio: float = 1.3,
    texture_resolution: int = 1024,
    remesh_option: str = "none",
    target_count: int = 2000,
):
    logging.info("Request received for", obj_desc)
    output_dir = "output/"
    obj_dir = os.path.join(output_dir, obj_desc)

    res = search(obj_desc)
    if res:
        return res
    
    try:
        return voice_3d()
    except Exception as e:
        logging.error("Error during model generation: %s", str(e))
        
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/generate/new/{obj_desc}")
async def generate_model(
    obj_desc: str,
    foreground_ratio: float = 1.3,
    texture_resolution: int = 1024,
    remesh_option: str = "none",
    target_count: int = 2000,
):
    logging.info("Request received for", obj_desc)
    output_dir = "output/"
    obj_dir = os.path.join(output_dir, obj_desc)

    try:
        return voice_3d()
    except Exception as e:
        logging.error("Error during model generation: %s", str(e))
        
        raise HTTPException(status_code=500, detail=str(e))

    @app.get("test")
    async def test_model():
        return FileResponse("test_material/test.glb")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)