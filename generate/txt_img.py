from pathlib import Path
from typing import Optional
import io
import logging
from PIL import Image
from httpx import HTTPException, AsyncClient
from huggingface_hub import InferenceClient
import os  # Add this import

API_URL = "https://api-inference.huggingface.co/"

async def flux_query(payload: str) -> PIL.Image:
    """Make an async request to the Hugging Face API."""
    try:
        client = InferenceClient(
            provider="hf-inference",
            api_key=os.getenv("HF_API_KEY")  # Replace hardcoded API key
        )

        # output is a PIL.Image object
        return client.text_to_image(
            payload,
            model="black-forest-labs/FLUX.1-schnell"
        )
    except Exception as e:
        logger.error(f"Error during API query: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def generate_image(obj_desc: str) -> None:
    """Process the image generation and 3D conversion pipeline."""
    try:
        # Generate image
        prompt = f"{obj_desc}, plain white background, slight angle, 3d"
        image_bytes = await flux_query(prompt)
        
        # Save initial image
        image_path = OUTPUT_DIR / f"{obj_desc}.png"
        image.save(image_path, format="PNG")
        logger.info(f"Saved initial image to {image_path}")

        return image
    
    except Exception as e:
        logger.error(f"Error processing image for {obj_desc}: {str(e)}")
        raise