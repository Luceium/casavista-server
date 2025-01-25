from pathlib import Path
from typing import Optional
import io
import logging
from PIL import Image
from httpx import HTTPException, AsyncClient

async def flux_query(payload: dict) -> bytes:
    """Make an async request to the Hugging Face API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.content
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred: {str(e)}")
        raise HTTPException(status_code=502, detail="Failed to generate image")
    except Exception as e:
        logger.error(f"Error during API query: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def generate_image(obj_desc: str) -> None:
    """Process the image generation and 3D conversion pipeline."""
    try:
        # Generate image
        prompt = f"{obj_desc}, plain white background, slight angle, 3d"
        image_bytes = await flux_query({"inputs": prompt})
        
        # Save initial image
        image = Image.open(io.BytesIO(image_bytes))
        image_path = OUTPUT_DIR / f"{obj_desc}.png"
        image.save(image_path, format="PNG")
        logger.info(f"Saved initial image to {image_path}")

        return image
    
    except Exception as e:
        logger.error(f"Error processing image for {obj_desc}: {str(e)}")
        raise