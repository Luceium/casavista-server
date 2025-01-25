import logging
from pathlib import Path
import torch
from PIL import Image
from PIL import Image
from transparent_background import Remover
import os
import sys

# from spar3d.system
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spar3d.system import SPAR3D
from spar3d.utils import remove_background, foreground_crop

logger = logging.getLogger("myapp")

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
