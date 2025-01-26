from .voice_txt import get_transcript
# from .txt_img import generate_image
# from img_3d.img_3d import ModelService
# from PIL import Image
from fastapi.responses import FileResponse  # Fix import

from .img_3d.meshy import txt_glb

def txt_3d(obj_desc): #model_service: ModelService):
    txt_glb(obj_desc)

    # image = Image.open("./test.jpg")  # TEST
    # # image = generate_image(obj_desc)  # TODO: text-to-image
    # image = clean_image(image)
    # save_image(image, f"{obj_dir}/img.png")

    # # mesh, point_cloud = await model_service.process_image(
    # #     pil_image,
    # #     obj_desc,
    # #     foreground_ratio,
    # #     texture_resolution,
    # #     remesh_option,
    # #     target_count,
    # # )
    # #
    # # save_mesh(mesh, f"{obj_dir}/model.glb")
    # # # upload_mesh()
    # #     # upload_to_blob()
    # #     # upload_to_vector_db()
    # #         # embed_description()
    # # save_points(point_cloud, f"{obj_dir}/cloud.ply")

    # logging.info("3D model generated!!!")
    obj_dir = f"output/{obj_desc}"

    return FileResponse(
        f"{obj_dir}/model.glb",
        filename=f"model.glb",
    )