import json
import os
import requests
import yt_dlp
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

WATCHLIST = "watchlist.json"
DATABASE = "database"


def send_discord(message):
    webhook = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook:
        print("Discord webhook not found.")
        return

    try:
        requests.post(
            webhook,
            json={"content": message},
            timeout=15
        )
    except Exception as e:
        print(f"Failed to send Discord message: {e}")


def load_watchlist():
    if not os.path.exists(WATCHLIST):
        print(f"Error: {WATCHLIST} not found. Please create it.")
        return {}
    
    with open(WATCHLIST, "r", encoding="utf-8") as f:
        return json.load(f)


def load_database(name):
    os.makedirs(DATABASE, exist_ok=True)
    path = os.path.join(DATABASE, f"{name}.json")

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_database(name, data):
    os.makedirs(DATABASE, exist_ok=True)
    path = os.path.join(DATABASE, f"{name}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def check_video_status(video_id):
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
            ydl.extract_info(f"https://youtu.be/{video_id}", download=False)
        return "Public"

    except Exception as e:
        text = str(e)
        if "Private video" in text:
            return "Private"
        elif "Video unavailable" in text:
            return "Unavailable"
        elif "Members only" in text:
            return "Members"
        return "Unknown"


def scan_playlist(name, url):
    print(f"\nScanning Playlist: {name}")
    
    # 1. جلب البيانات القديمة
    old = load_database(name)
    old_ids = {x["id"] for x in old}

    # 2. جلب البيانات الحالية من اليوتيوب
    opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True
    }
    
    current = []
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if "entries" in info:
                for entry in info["entries"]:
                    video_id = entry.get("id")
                    if not video_id:
                        continue
                    
                    title = entry.get("title", "Unknown Title")
                    status = check_video_status(video_id)
                    
                    current.append({
                        "id": video_id,
                        "title": title,
                        "status": status
                    })
    except Exception as e:
        print(f"Error fetching playlist {name}: {e}")
        return

    new_ids = {x["id"] for x in current}
    changes = 0

    # 3. التحقق من الفيديوهات الجديدة
    for video in current:
        if video["id"] not in old_ids:
            changes += 1
            print(f"[NEW] {video['id']}")
            print(video["title"])
            print("Status :", video["status"])
            print()

            send_discord(
                f"🟢 **New Video**\n\n"
                f"**Playlist:** {name}\n"
                f"**Status:** {video['status']}\n\n"
                f"**Title:**\n{video['title']}\n\n"
                f"**ID:**\n{video['id']}\n\n"
                f"https://youtu.be/{video['id']}"
            )

    # 4. التحقق من تغير حالة الفيديو (مثل تحوله من عام إلى خاص)
    for video in current:
        old_video = next((x for x in old if x["id"] == video["id"]), None)
        
        if old_video is None:
            continue

        old_status = old_video.get("status", "Unknown")
        new_status = video["status"]

        if old_status != new_status:
            changes += 1
            print(f"[STATUS CHANGED] {video['id']}")
            print(video["title"])
            print(f"{old_status} -> {new_status}")
            print()

            send_discord(
                f"🟡 **Video Status Changed**\n\n"
                f"**Playlist:** {name}\n\n"
                f"**Title:**\n{video['title']}\n\n"
                f"**ID:**\n{video['id']}\n\n"
                f"**Status:**\n{old_status} ➜ {new_status}\n\n"
                f"https://youtu.be/{video['id']}"
            )

    # 5. التحقق من الفيديوهات المحذوفة من القائمة
    for video in old:
        if video["id"] not in new_ids:
            changes += 1
            print(f"[REMOVED] {video['id']}")
            print(video["title"])
            print("Status :", video.get("status", "Unknown"))
            print()

            send_discord(
                f"🔴 **Video Removed**\n\n"
                f"**Playlist:** {name}\n\n"
                f"**Last Status:** {video.get('status', 'Unknown')}\n\n"
                f"**Title:**\n{video['title']}\n\n"
                f"**ID:**\n{video['id']}"
            )

    if changes == 0:
        print("✓ No changes found.")

    print(f"Total Videos : {len(current)}\n")
    
    # حفظ البيانات الجديدة
    save_database(name, current)


def run():
    send_discord("✅ Discord Webhook works successfully.")
    watchlist = load_watchlist()
    playlists = watchlist.get("youtube_playlists", [])

    if not playlists:
        print("No playlists found in watchlist.json.")
        return

    for playlist in playlists:
        playlist_id = playlist.get("playlist_id")
        if not playlist_id:
            continue
            
        url = f"https://www.youtube.com/playlist?list={playlist_id}"
        scan_playlist(playlist["name"], url)

    print("Finished scanning all playlists.\n")


def export_ids():
    watchlist = load_watchlist()
    playlists = watchlist.get("youtube_playlists", [])

    os.makedirs("output", exist_ok=True)
    filename = "output/all_ids.txt"

    with open(filename, "w", encoding="utf-8") as out:
        for playlist in playlists:
            print(f"\nExporting : {playlist['name']}")
            
            playlist_id = playlist["playlist_id"]
            url = f"https://www.youtube.com/playlist?list={playlist_id}"

            opts = {
                "quiet": True,
                "extract_flat": True,
                "skip_download": True
            }

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

            out.write(f"{playlist['name']}\n")
            out.write("=" * 60 + "\n")

            if "entries" in info:
                for video in info["entries"]:
                    video_id = video.get("id")
                    if not video_id:
                        continue
                        
                    status = check_video_status(video_id)

                    if status == "Public":
                        icon = "🟢"
                    elif status == "Private":
                        icon = "🔒"
                    elif status == "Unavailable":
                        icon = "⚫"
                    elif status == "Members":
                        icon = "👑"
                    else:
                        icon = "❓"

                    line = f"{video_id:<15} {icon} {status}"
                    print(line)
                    out.write(line + "\n")

            out.write("\n")

    print(f"\nSaved : {filename}\n")


if __name__ == "__main__":
    if os.getenv("GITHUB_ACTIONS") == "true":
        run()
    else:
        while True:
            print("=" * 40)
            print("Video Inspector")
            print("=" * 40)
            print("1. Watch Playlists")
            print("2. Export All IDs")
            print("3. Exit")
            print()

            choice = input("Choice : ").strip()

            if choice == "1":
                run()
            elif choice == "2":
                export_ids()
            elif choice == "3":
                break
            else:
                print("Invalid choice. Try again.\n")