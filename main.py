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

# dictionary of jobs
# ex. {job_id: {step, progress, model_path}}
jobs = {}

@app.on_event("startup")
async def startup_event():
    logging.info("Starting up...")
    if not os.path.exists("output"):
        os.mkdir("output")
    # global model_service
    # model_service = ModelService()

@app.get("/status/{job_id}")
async def status(job_id: str):
    return JSONResponse(content=jobs[job_id])


@app.get("/model/{job_id}")
async def download_model(job_id: str):
    pass

@app.post("/transcribe")
async def server_describe(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="file is required")

    temp_file_path = f"/tmp/{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(await file.read())

    print("transcribing voice data")
    obj_desc = get_transcript(temp_file_path)

    # delete tmp file
    os.remove(temp_file_path)

    print(f"completed transcription: {obj_desc}")
    return JSONResponse(content={"data" : obj_desc})

@app.put("/generate")
async def get_or_generate_model(request_body: dict = Body(...)):
    obj_desc = request_body.get("obj_desc")

    logging.info("Request received for"+ obj_desc)
    output_dir = "output/"
    obj_dir = os.path.join(output_dir, obj_desc)

    res = search(obj_desc)
    if res:
        return res
    
    try:
        # return txt_3d(obj_desc)
        return FileResponse("test_material/test.glb")
    except Exception as e:
        logging.error("Error during model generation: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/")
def test_remote():
    return JSONResponse(content={"hello":"world"})

@app.get("/test")
def test_remote():
    return JSONResponse(content={"hello":"world"})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)