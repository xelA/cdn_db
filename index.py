import json
import os

from PIL import Image
from utils import sqlite
from quart import Quart, send_from_directory, request

with open("config.json", "r") as f:
    config = json.load(f)

app = Quart(__name__)
db = sqlite.Database()
db.create_tables()  # Attempt to make tables

db_foldername = config.get("database_folder", "database")


def standard_json(message: str, code: int = 200):
    return {"message": message, "code": code}, code


@app.route("/")
async def index():
    return {
        "POST /<folder>": "Upload file to storage",
        "DELETE /<folder>/<filename>": "Delete file from storage",
        "GET /<folder>/<filename>": "Get file from storage",
        "GET /<folder>/<filename>/stats": "Get file stats from storage",
    }


@app.route("/<folder>/<filename>", methods=["GET"])
async def get_image(folder: str, filename: str):
    try:
        img = await send_from_directory(f"./{db_foldername}/{folder}", filename)
        db.execute("UPDATE image SET views = views + 1 WHERE name = ?", (filename,))
        return img
    except FileNotFoundError:
        return standard_json("Image not found", 404)


@app.route("/<folder>/<filename>/stats", methods=["GET"])
async def head_image_stats(folder: str, filename: str):
    if not os.path.exists(f"./{db_foldername}/{folder}"):
        return standard_json("Folder not found", 404)
    if not os.path.exists(f"./{db_foldername}/{folder}/{filename}"):
        return standard_json("Image not found", 404)

    data = db.fetchrow("SELECT * FROM image WHERE name=?", (filename,))
    return {
        "code": 200,
        "name": data["name"],
        "created_at": str(data["created_at"]),
        "user_id": data["user_id"],
        "channel_id": data["channel_id"],
        "guild_id": data["guild_id"]
    }


@app.route("/<folder>/<filename>", methods=["DELETE"])
async def delete_image(folder: str, filename: str):
    if not os.path.exists(f"./{db_foldername}/{folder}"):
        return standard_json("Folder not found", 404)
    if not os.path.exists(f"./{db_foldername}/{folder}/{filename}"):
        return standard_json("Image not found", 404)

    os.remove(f"./{db_foldername}/{folder}/{filename}")
    db.execute("DELETE FROM image WHERE name=?", (filename,))
    return standard_json("Image deleted")


@app.route("/<folder>", methods=["POST"])
async def post_image(folder: str):
    if not os.path.exists(f"./{db_foldername}/{folder}"):
        return standard_json("DB folder not found", 404)

    user_id = request.headers.get("user_id", None)
    channel_id = request.headers.get("channel_id", None)
    guild_id = request.headers.get("guild_id", None)
    if not user_id:
        return standard_json("Missing user_id header", 400)

    files = await request.files
    if not files:
        return standard_json("No file found", 400)

    duplicate = []
    for g in files:
        image = files[g]

        filename = image.filename.split(".")[:-1]
        file_ext = image.filename.split(".")[-1].lower()

        full_filename = f"{''.join(filename)}.{file_ext}"

        if len(image.filename.split(".")) < 1:
            return standard_json(
                "The file(s) sent must must have the following format: "
                "{\"filename.ext\": \"image-bytes\"}",
                400
            )
        if file_ext not in ("png", "jpg", "jpeg", "gif"):
            return standard_json(f"Invalid file type '{file_ext}'", 400)

        try:
            img = Image.open(image)
        except OSError:
            return standard_json(f"The image '{full_filename}' is not a real image...", 400)

        if os.path.exists(f"./{db_foldername}/{folder}/{full_filename}"):
            duplicate.append(full_filename)
            continue

        img.save(f"./{db_foldername}/{folder}/{full_filename}")
        db.execute(
            "INSERT INTO image (name, user_id, channel_id, guild_id) VALUES (?, ?, ?, ?)",
            (full_filename, user_id, channel_id, guild_id)
        )

    if duplicate and len(duplicate) == len(files):
        return standard_json("All images you attempted to upload already exist", 400)
    elif duplicate:
        return standard_json(
            "Image(s) uploaded, however the following "
            f"files were not uploaded: {duplicate}",
            206
        )
    else:
        return standard_json("Image(s) uploaded")


app.run(port=config["port"], debug=config["debug"])
