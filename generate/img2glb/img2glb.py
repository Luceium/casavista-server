class ModelService:
    def __init__(
        self,
        device: str = "cuda:0",
        model_path: str = "stabilityai/stable-point-aware-3d",
        chunk_size: int = 8192,
        output_dir: str = "output/",
    ):
        self.device = "cpu" if not (torch.cuda.is_available() or torch.backends.mps) else device
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize model
        logging.info("Initializing model...")
        self.model = SPAR3D.from_pretrained(
            model_path,
            config_name="config.yaml",
            weight_name="model.safetensors",
            low_vram_mode=False
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
        foreground_ratio: float = 1.3,
        texture_resolution: int = 1024,
        remesh_option: str = "none",
        target_count: int = 2000,
    ) -> dict:
        print("Generating 3D model...")
        with torch.no_grad():
            with (
                torch.autocast(device_type=self.device, dtype=torch.bfloat16)
                if "cuda" in self.device
                else nullcontext()
            ):
                mesh, glob_dict = self.model.run_image(
                    image,
                    bake_resolution=texture_resolution,
                    remesh=remesh_option,
                    vertex_count=target_count,
                    return_points=True,
                )

        return mesh, glob_dict