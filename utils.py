def clean_image(image: Image.Image) -> Image.Image:
    """Remove the background from an image."""
    image = image.convert("RGBA")
    image = remove_background(image, bg_remover)
    image = foreground_crop(image, foreground_ratio)
    return image

def save_image(image: Image.Image, image_path: str) -> None:
    """Save an image to disk."""
    image.save(image_path, format="PNG")

def save_mesh(mesh: trimesh.Trimesh, mesh_path: str) -> None:
    """Save a mesh to disk."""
    mesh.export(mesh_path, include_normals=True)

def save_points(points: trimesh.PointCloud, points_path: str) -> None:
    """Save a point cloud to disk."""
    points.export(points_path)

def search(obj_desc: str) -> FileResponse:
    res = cache_search(obj_desc)
    if res:
        return res
    return vector_search(obj_desc)

def cache_search(obj_desc: str) -> FileResponse:
    # Check if folder with the object name exists
    if os.path.isdir(obj_dir):
        return FileResponse(
            f"{obj_dir}/model.glb",
            filename=f"model.glb",
        )
    return None

def vector_search(obj_desc: str) -> FileResponse:
    # TODO
    return None