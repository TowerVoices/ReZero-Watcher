import yt_dlp
import json
import os
from rich import print


def youtube_analyzer(url):

    opts = {
        "quiet": True,
        "skip_download": True
    }

    try:

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        data = {
            "platform": "YouTube",
            "id": info.get("id"),
            "status": "Public",
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "channel_id": info.get("channel_id"),
            "channel_url": info.get("channel_url"),
            "description": info.get("description"),
            "upload_date": info.get("upload_date"),
            "duration": info.get("duration"),
            "view_count": info.get("view_count"),
            "like_count": info.get("like_count"),
            "comment_count": info.get("comment_count"),
            "thumbnail": info.get("thumbnail"),
            "tags": info.get("tags"),
            "categories": info.get("categories"),
            "availability": info.get("availability"),
            "live_status": info.get("live_status"),
            "language": info.get("language"),
            "webpage_url": info.get("webpage_url")
        }

        os.makedirs("output", exist_ok=True)

        filename = f"output/{data['id']}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print()
        print("[bold green]Platform[/bold green] :", data["platform"])
        print("[cyan]ID[/cyan]          :", data["id"])
        print("[cyan]Status[/cyan]      :", data["status"])
        print("[cyan]Title[/cyan]       :", data["title"])
        print("[cyan]Uploader[/cyan]    :", data["uploader"])
        print("[cyan]Upload Date[/cyan] :", data["upload_date"])
        print("[cyan]Duration[/cyan]    :", data["duration"])
        print("[cyan]Views[/cyan]       :", data["view_count"])
        print("[cyan]Likes[/cyan]       :", data["like_count"])
        print("[cyan]Comments[/cyan]    :", data["comment_count"])
        print("[cyan]Language[/cyan]    :", data["language"])
        print("[cyan]Saved[/cyan]       :", filename)

    except Exception as e:

        text = str(e)

        print()
        print("[bold green]Platform[/bold green] : YouTube")

        if "Private video" in text:

            print("[red]Status[/red] : Private")

        elif "Video unavailable" in text:

            print("[red]Status[/red] : Unavailable")

        elif "Members only" in text:

            print("[yellow]Status[/yellow] : Members Only")

        else:

            print("[red]Status[/red] : Unknown")

        print(text)