from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.responses import FileResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Optional, List
from io import BytesIO
import random
import logging
import os
from contextlib import nullcontext
from pathlib import Path
import torch
import numpy as np
import requests
import rembg
import uvicorn
import io
from PIL import Image
from transparent_background import Remover
from generate.voice_txt import get_transcript

# from generate.img_3d.spar3d.system import SPAR3D
from generate.img_3d.spar3d.utils import remove_background, foreground_crop
# from generate.img_3d.img_3d import ModelService
from generate.voice_3d import txt_3d

from utils import clean_image, save_image, save_mesh, save_points, search
from dotenv import load_dotenv
# import boto3

load_dotenv()

app = FastAPI(title="3D Model Generation API")

# Initialize model service at startup
# model_service = None

@app.on_event("startup")
async def startup_event():
    logging.info("Starting up...")
    # global model_service
    # model_service = ModelService()

@app.get("/generate/{obj_desc}")
async def get_or_generate_model_txt_to_gbl(
    obj_desc: str #,
    # foreground_ratio: float = 1.3,
    # texture_resolution: int = 1024,
    # remesh_option: str = "none",
    # target_count: int = 2000,
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

@app.post("/test")
def test():
    return JSONResponse(content={"message": "Hello, World!"})

@app.post("/generate")
async def get_or_generate_model(request_body: dict = Body(...)):
    file_path = request_body.get("filePath")
    if not file_path:
        raise HTTPException(status_code=400, detail="filePath is required")

    print("transcribing voice data")
    obj_desc = get_transcript(file_path)  # TODO: voice-to-text

    print("completed transcription")

    logging.info("Request received for", obj_desc)
    output_dir = "output/"
    obj_dir = os.path.join(output_dir, obj_desc)

    res = search(obj_desc)
    if res:
        return res
    
    try:
        return txt_3d(obj_desc)
    except Exception as e:
        logging.error("Error during model generation: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/generate/new/{obj_desc}")
async def generate_model(
    obj_desc: str #,
    # foreground_ratio: float = 1.3,
    # texture_resolution: int = 1024,
    # remesh_option: str = "none",
    # target_count: int = 2000,
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