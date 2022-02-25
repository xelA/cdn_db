import requests

from random import randint
from PIL import Image
from io import BytesIO


def create_dumb_image():
    img = Image.new(
        "RGB", (100, 100),
        color=(randint(0, 255), randint(0, 255), randint(0, 255))
    )
    bio = BytesIO()
    img.save(bio, "jpeg")
    bio.seek(0)
    return bio


r = requests.post(
    "http://localhost:8080/test?overwrite=true",
    headers={"user_id": "1337"},
    files={"test.jpg": create_dumb_image()}
)

print("\n".join([str(r), str(r.content)]))
