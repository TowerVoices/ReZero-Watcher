import yt_dlp
import json
import os

def scan_account(url):

    opts = {
        "quiet": True,
        "extract_flat": True,
        "playlistend": 5,
        "skip_download": True
    }

    try:

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        username = info.get("uploader") or info.get("id") or "unknown"

        videos = []

        for entry in info.get("entries", []):

            videos.append({
                "id": entry.get("id"),
                "title": entry.get("title"),
                "url": entry.get("url"),
                "status": "Public"
            })

        os.makedirs("output", exist_ok=True)

        filename = f"output/{username}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump({
                "platform": "TikTok",
                "username": username,
                "videos": videos
            }, f, indent=4, ensure_ascii=False)

        print()

        print("Platform :", "TikTok")
        print("Username :", username)
        print()

        for i, video in enumerate(videos, 1):

            print(f"{i}. {video['id']}")
            print(video["title"])
            print(video["status"])
            print()

        print("Saved:", filename)

    except Exception as e:

        print(e)