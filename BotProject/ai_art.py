import aiohttp
import base64
import os
import asyncio

async def generate_image(prompt):
    url = "http://127.0.0.1:7860/sdapi/v1/txt2img"

    payload = {
        "prompt": prompt,
        "negative_prompt": "blurry, bad quality",
        "steps": 50,
        "cfg_scale": 7,
        "width": 512,
        "height": 512
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                image_data = result['images'][0]

                image_bytes = base64.b64decode(image_data)

                image_path = "generated_image.png"
                with open(image_path, "wb") as image_file:
                    image_file.write(image_bytes)

                return image_path
            else:
                print("Error:", response.status, await response.text())
                return None
