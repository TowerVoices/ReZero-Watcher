import json
import os
import yt_dlp

WATCHLIST = "watchlist.json"
DATABASE = "database"


def load_watchlist():
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

        with yt_dlp.YoutubeDL({
            "quiet": True,
            "skip_download": True
        }) as ydl:

            ydl.extract_info(
                f"https://youtu.be/{video_id}",
                download=False
            )

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

    print("=" * 60)
    print(f"Checking : {name}")
    print("=" * 60)

    opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    old = load_database(name)
    old_ids = {x["id"] for x in old}

    current = []

    for video in info["entries"]:

        video_id = video.get("id")
        title = video.get("title")

        if video_id in old_ids:

            status = next(
                (
                    x.get("status", "Unknown")
                    for x in old
                    if x["id"] == video_id
                ),
                "Unknown"
            )

        else:

            status = check_video_status(video_id)

        current.append({
            "id": video_id,
            "title": title,
            "status": status
        })

    new_ids = {x["id"] for x in current}

    changes = 0

    for video in current:

        if video["id"] not in old_ids:

            changes += 1

            print(f"[NEW] {video['id']}")
            print(video["title"])
            print("Status :", video["status"])
            print()

    for video in old:

        if video["id"] not in new_ids:

            changes += 1

            print(f"[REMOVED] {video['id']}")
            print(video["title"])
            print("Status :", video.get("status", "Unknown"))
            print()

    if changes == 0:
        print("✓ No changes found.\n")

    print(f"Videos : {len(current)}")
    print()

    save_database(name, current)


def run():

    watchlist = load_watchlist()

    playlists = watchlist.get("youtube_playlists", [])

    if not playlists:
        print("No playlists found.")
        return

    for playlist in playlists:

        playlist_id = playlist["playlist_id"]

        url = f"https://www.youtube.com/playlist?list={playlist_id}"

        scan_playlist(
            playlist["name"],
            url
        )

        print("Finished.\n")


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

            for video in info["entries"]:

                video_id = video.get("id")

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

    print()
    print("Saved :", filename)
    print()

if __name__ == "__main__":

    print("=" * 40)
    print("Video Inspector")
    print("=" * 40)
    print("1. Watch Playlists")
    print("2. Export All IDs")
    print()

    choice = input("Choice : ").strip()

    if choice == "1":
        run()

    elif choice == "2":
        export_ids()

    else:
        print("Invalid choice.")