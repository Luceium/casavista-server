import requests
import os
import time

def txt_glb(prompt: str):
    headers = {
        "Authorization": f"Bearer {os.getenv('MESHY_API_KEY')}"
    }

    # 1. Generate a preview model and get the task ID

    generate_preview_request = {
        "mode": "preview",
        "prompt": prompt,
        "negative_prompt": "low quality, low resolution, low poly, ugly",
        "art_style": "realistic",
        "should_remesh": True,
    }

    generate_preview_response = requests.post(
        "https://api.meshy.ai/openapi/v2/text-to-3d",
        headers=headers,
        json=generate_preview_request,
    )

    generate_preview_response.raise_for_status()

    preview_task_id = generate_preview_response.json()["result"]

    print("Preview task created. Task ID:", preview_task_id)

    # 2. Poll the preview task status until it's finished

    preview_task = None

    while True:
        preview_task_response = requests.get(
            f"https://api.meshy.ai/openapi/v2/text-to-3d/{preview_task_id}",
            headers=headers,
        )

        preview_task_response.raise_for_status()

        preview_task = preview_task_response.json()

        if preview_task["status"] == "SUCCEEDED":
            print("Preview task finished.")
            break

        print("Preview task status:", preview_task["status"], "| Progress:", preview_task["progress"], "| Retrying in 5 seconds...")
        time.sleep(5)

    # 3. Download the preview model in glb format

    preview_model_url = preview_task["model_urls"]["glb"]

    preview_model_response = requests.get(preview_model_url)
    preview_model_response.raise_for_status()


    print(f'Make `output/{"".join(prompt.split(" "))}`')
    os.mkdir(f'output/{"".join(prompt.split(" "))}')
    with open(f'output/{"".join(prompt.split(" "))}/preview_model.glb', "wb") as f:
        f.write(preview_model_response.content)

    print("Preview model downloaded.")

    # 4. Generate a refined model and get the task ID

    generate_refined_request = {
        "mode": "refine",
        "preview_task_id": preview_task_id,
    }

    generate_refined_response = requests.post(
        "https://api.meshy.ai/openapi/v2/text-to-3d",
        headers=headers,
        json=generate_refined_request,
    )

    generate_refined_response.raise_for_status()

    refined_task_id = generate_refined_response.json()["result"]

    print("Refined task created. Task ID:", refined_task_id)

    # 5. Poll the refined task status until it's finished

    refined_task = None

    while True:
        refined_task_response = requests.get(
            f"https://api.meshy.ai/openapi/v2/text-to-3d/{refined_task_id}",
            headers=headers,
        )

        refined_task_response.raise_for_status()

        refined_task = refined_task_response.json()

        if refined_task["status"] == "SUCCEEDED":
            print("Refined task finished.")
            break

        print("Refined task status:", refined_task["status"], "| Progress:", refined_task["progress"], "| Retrying in 5 seconds...")
        time.sleep(5)

    # 6. Download the refined model in glb format

    refined_model_url = refined_task["model_urls"]["glb"]

    refined_model_response = requests.get(refined_model_url)
    refined_model_response.raise_for_status()

    os.mkdir(f'output/{"".join(prompt.split(" "))}')
    with open(f'output/{"".join(prompt.split(" "))}/model.glb', "wb") as f:
        f.write(refined_model_response.content)

    print("Refined model downloaded.")

