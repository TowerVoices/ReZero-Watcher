import json
import os
import requests
import yt_dlp
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

WATCHLIST = "watchlist.json"
DATABASE = "database"

cookies_alert_sent = False

# ==========================================
# 1. إعدادات الألوان لتجميل الشاشة (Console)
# ==========================================
class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# ==========================================
# 2. كتم تحذيرات وأخطاء yt_dlp المزعجة
# ==========================================
class SilentLogger(object):
    def debug(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        pass

# الإعدادات العامة لـ yt_dlp لمنع أي نصوص غير مرغوب فيها
YTDLP_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "extract_flat": True,
    "logger": SilentLogger(), 
    "cookiefile": "cookies.txt"
}

# ==========================================
# الدوال الأساسية
# ==========================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def send_discord(message):
    webhook = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook:
        return

    try:
        r = requests.post(
            webhook,
            json={"content": message},
            timeout=15
        )

        if r.status_code >= 400:
            print("Discord Error:", r.status_code)
            print(r.text)

    except Exception as e:
        print("Discord Exception:", e)

def load_watchlist():
    if not os.path.exists(WATCHLIST):
        print(f"{Color.RED}✖ Error: {WATCHLIST} not found.{Color.RESET}")
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
    global cookies_alert_sent
    # نستخدم إعدادات صامتة مخصصة لفحص فيديو واحد
    single_opts = YTDLP_OPTS.copy()
    single_opts["extract_flat"] = False 

    try:
        with yt_dlp.YoutubeDL(single_opts) as ydl:
            ydl.extract_info(f"https://youtu.be/{video_id}", download=False)
        return "Public"
    except Exception as e:
        text = str(e)
       
    text = str(e)
    print(text)

    if (
        "Sign in to confirm you're not a bot" in text
        or "cookies" in text.lower()
    ):

        if not cookies_alert_sent:
            send_discord(
                "🚨 **YouTube Session Expired**\n\n"
                "The cookies.txt session is no longer valid.\n"
                "Please export a new cookies.txt and update the YOUTUBE_COOKIES GitHub Secret."
            )
            cookies_alert_sent = True

        return "Cookies Expired"

    if "Private video" in text or "private" in text.lower():
        return "Private"

    elif "Video unavailable" in text or "unavailable" in text.lower():
        return "Unavailable"

    elif "Members only" in text or "members" in text.lower():
        return "Members"

    return "Unknown"
     


def scan_playlist(name, url):
    print(f"{Color.CYAN}➤ Scanning Playlist:{Color.RESET} {Color.BOLD}{name}{Color.RESET} ... ", end="", flush=True)
    
    old = load_database(name)
    old_ids = {x["id"] for x in old}

    current = []
    try:
        with yt_dlp.YoutubeDL(YTDLP_OPTS) as ydl:
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
        print(f"{Color.RED}Failed!{Color.RESET}")
        return

    print(f"{Color.GREEN}Done! ({len(current)} videos){Color.RESET}")

    new_ids = {x["id"] for x in current}
    changes = 0

    # 1. فيديوهات جديدة
    for video in current:
        if video["id"] not in old_ids:
            changes += 1
            print(f"  {Color.GREEN}[+] NEW VIDEO:{Color.RESET} {video['title'][:50]}... ({video['status']})")
            send_discord(
                f"🟢 **New Video**\n"
                f"**Playlist:** {name}\n"
                f"**Status:** {video['status']}\n\n"
                f"**Title:**\n{video['title']}\n\n"
                f"**ID:**\n{video['id']}\n\n"
                f"https://youtu.be/{video['id']}"
            )

    # 2. تغير الحالة
    for video in current:
        old_video = next((x for x in old if x["id"] == video["id"]), None)
        if old_video is None:
            continue

        old_status = old_video.get("status", "Unknown")
        new_status = video["status"]

        if old_status != new_status:
            changes += 1
            print(f"  {Color.YELLOW}[~] STATUS CHANGED:{Color.RESET} {video['title'][:50]}... [{old_status} ➔ {new_status}]")
            send_discord(
                f"🟡 **Video Status Changed**\n"
                f"**Playlist:** {name}\n\n"
                f"**Title:**\n{video['title']}\n\n"
                f"**ID:**\n{video['id']}\n\n"
                f"**Status:**\n{old_status} ➜ {new_status}\n\n"
                f"https://youtu.be/{video['id']}"
            )

    # 3. فيديوهات محذوفة
    for video in old:
        if video["id"] not in new_ids:
            changes += 1
            print(f"  {Color.RED}[-] REMOVED:{Color.RESET} {video['title'][:50]}... (Was: {video.get('status', 'Unknown')})")
            send_discord(
                f"🔴 **Video Removed**\n"
                f"**Playlist:** {name}\n\n"
                f"**Last Status:** {video.get('status', 'Unknown')}\n\n"
                f"**Title:**\n{video['title']}\n\n"
                f"**ID:**\n{video['id']}\n\n"
                f"https://youtu.be/{video['id']}"
            )

    if changes == 0:
        print(f"  {Color.BLUE}✓ No changes detected.{Color.RESET}")
    print("-" * 50)
    
    save_database(name, current)


def run():
    print(f"\n{Color.BOLD}Starting Playlist Inspection...{Color.RESET}\n")
    send_discord("✅ Video Inspector Started Successfully.")
    
    watchlist = load_watchlist()
    playlists = watchlist.get("youtube_playlists", [])

    if not playlists:
        print(f"{Color.YELLOW}⚠ No playlists found in watchlist.json.{Color.RESET}")
        return

    for playlist in playlists:
        playlist_id = playlist.get("playlist_id")
        if not playlist_id:
            continue
        url = f"https://www.youtube.com/playlist?list={playlist_id}"
        scan_playlist(playlist["name"], url)

    print(f"\n{Color.GREEN}{Color.BOLD}✔ All playlists scanned successfully!{Color.RESET}\n")


def export_ids():
    watchlist = load_watchlist()
    playlists = watchlist.get("youtube_playlists", [])

    os.makedirs("output", exist_ok=True)
    filename = "output/all_ids.txt"

    print(f"\n{Color.CYAN}Exporting IDs to {filename}...{Color.RESET}\n")

    with open(filename, "w", encoding="utf-8") as out:
        for playlist in playlists:
            print(f"{Color.YELLOW}Exporting:{Color.RESET} {playlist['name']} ", end="", flush=True)
            
            playlist_id = playlist["playlist_id"]
            url = f"https://www.youtube.com/playlist?list={playlist_id}"

            with yt_dlp.YoutubeDL(YTDLP_OPTS) as ydl:
                info = ydl.extract_info(url, download=False)

            out.write(f"{playlist['name']}\n")
            out.write("=" * 60 + "\n")

            if "entries" in info:
                for video in info["entries"]:
                    video_id = video.get("id")
                    if not video_id:
                        continue
                        
                    status = check_video_status(video_id)

                    if status == "Public": icon = "🟢"
                    elif status == "Private": icon = "🔒"
                    elif status == "Unavailable": icon = "⚫"
                    elif status == "Members": icon = "👑"
                    else: icon = "❓"

                    line = f"{video_id:<15} {icon} {status}"
                    out.write(line + "\n")
            
            out.write("\n")
            print(f"{Color.GREEN}✔ Done!{Color.RESET}")

    print(f"\n{Color.GREEN}{Color.BOLD}✔ Export completed! File saved at: {filename}{Color.RESET}\n")


# ==========================================
# واجهة المستخدم (القائمة الرئيسية)
# ==========================================
if __name__ == "__main__":
    if os.getenv("GITHUB_ACTIONS") == "true":
        run()
    else:
        clear_screen()
        while True:
            print(f"{Color.CYAN}{Color.BOLD}" + "=" * 45)
            print("         🎬 YOUTUBE VIDEO INSPECTOR")
            print("=" * 45 + f"{Color.RESET}")
            print(f" {Color.GREEN}1.{Color.RESET} Scan Playlists & Check Changes")
            print(f" {Color.YELLOW}2.{Color.RESET} Export All IDs to Text File")
            print(f" {Color.RED}3.{Color.RESET} Exit")
            print(f"{Color.CYAN}" + "-" * 45 + f"{Color.RESET}")

            choice = input(f"{Color.BOLD}Enter your choice (1-3): {Color.RESET}").strip()

            if choice == "1":
                run()
                input(f"\n{Color.CYAN}Press Enter to return to main menu...{Color.RESET}")
                clear_screen()
            elif choice == "2":
                export_ids()
                input(f"\n{Color.CYAN}Press Enter to return to main menu...{Color.RESET}")
                clear_screen()
            elif choice == "3":
                print(f"\n{Color.GREEN}Exiting... Goodbye! 👋{Color.RESET}")
                break
            else:
                print(f"{Color.RED}\n✖ Invalid choice. Please try again.\n{Color.RESET}")