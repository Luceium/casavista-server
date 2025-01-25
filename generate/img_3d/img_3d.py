from contextlib import nullcontext
from pathlib import Path
import logging
import torch
from PIL import Image
from .spar3d.system import SPAR3D
from transparent_background import Remover
import requests
import base64
import os

# class ModelService:
#     def __init__(
#         self,
#         device: str = "cuda:0",
#         model_path: str = "stabilityai/stable-point-aware-3d",
#         chunk_size: int = 8192,
#         output_dir: str = "output/",
#     ):
#         self.device = "cpu" if not (torch.cuda.is_available() or torch.backends.mps) else device
#         self.output_dir = Path(output_dir)
#         self.output_dir.mkdir(exist_ok=True)

#         # Initialize model
#         logging.info("Initializing model...")
#         self.model = SPAR3D.from_pretrained(
#             model_path,
#             config_name="config.yaml",
#             weight_name="model.safetensors",
#             low_vram_mode=False
#         )
#         self.model.to(self.device)
#         self.model.eval()

#         # Initialize background remover
#         self.bg_remover = Remover(device=self.device)
#         logging.info("Model service initialized successfully")

#     async def process_image(
#         self,
#         image: Image.Image,
#         object_name: str,
#         foreground_ratio: float = 1.3,
#         texture_resolution: int = 1024,
#         remesh_option: str = "none",
#         target_count: int = 2000,
#     ) -> dict:
#         print("Generating 3D model...")
#         with torch.no_grad():
#             with (
#                 torch.autocast(device_type=self.device, dtype=torch.bfloat16)
#                 if "cuda" in self.device
#                 else nullcontext()
#             ):
#                 mesh, glob_dict = self.model.run_image(
#                     image,
#                     bake_resolution=texture_resolution,
#                     remesh=remesh_option,
#                     vertex_count=target_count,
#                     return_points=True,
#                 )

#         return mesh, glob_dict

# Alternative to local running
def api_generation(image: PIL.Image):
    encoded_image = base64.b64encode(image.tobytes()).decode("utf-8")
    api_key = os.getenv("MESHY_API_KEY")

    payload = {
        # Using data URI example
        image_url: f'data:image/png;base64,{encoded_image}',
        "enable_pbr": True,
        "should_remesh": True,
        "should_texture": True

    }
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    response = requests.post(
        "https://api.meshy.ai/openapi/v1/image-to-3d",
        headers=headers,
        json=payload,
    )
    response.raise_for_status()
    print(response.json())
    