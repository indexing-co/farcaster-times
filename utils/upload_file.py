import os
import requests
from pinatapy import PinataPy
import tempfile

api_key = os.getenv("PINATA_API_KEY")
secret_api_key = os.getenv("PINATA_SECRET")
pinata = PinataPy(api_key, secret_api_key)

def download_image(image_url: str) -> bytes:
    response = requests.get(image_url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to download image from URL: {image_url}")

def upload_to_pinata(image_url: str) -> str:
    image_content = download_image(image_url)

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(image_content)
        temp_file_path = temp_file.name

    try:
        response = pinata.pin_file_to_ipfs(
            path_to_file=temp_file_path,
            ipfs_destination_path="/",
            save_absolute_paths=False,
            options=None
        )
        if 'IpfsHash' in response:
            return response['IpfsHash']
        else:
            raise Exception(f"Failed to upload image to IPFS: {response}")
    finally:
        os.remove(temp_file_path)