import requests
import json
import os

def download_image():
    # Get the path of the directory above me
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

    # Load the file settings.json from that path
    json_file = open(os.path.join(path, "config/settings.json"))

    # Load the json data from the file
    settings_data = json.load(json_file)

    # Get the frame value from settings_data
    frame = settings_data.get("frame")

    # Get the base_url value
    base_url = settings_data.get("base_url")

    index_url = f"{base_url}/{frame}/index.json"

    # Fetch the JSON file at index_url
    response = requests.get(index_url)
    index_json = response.json()

    # Get the url value from index_json
    image_url = index_json.get("url")

    # Fetch the image at image_url
    image_response = requests.get(image_url)
    
    # Save the image to the img directory
    with open(os.path.join(path, "img", "image.png"), "wb") as image_file:
        image_file.write(image_response.content)


