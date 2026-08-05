import json
import os
import requests
import yt_dlp
import time
import sys
import random
from datetime import datetime, timedelta
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

# ==========================================
# إعدادات yt_dlp
# ==========================================
YTDLP_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "extract_flat": True,
    "logger": SilentLogger(), 
    "cookiefile": "cookies.txt",
    "sleep_interval_requests": 2, 
    "sleep_interval": 3,
    "max_sleep_interval": 7
}

# ==========================================
# الدوال الأساسية
# ==========================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def send_discord(message):
    # جلب روابط الويب هوك من ملف .env للسيرفرين
    webhooks = [
        os.getenv("DISCORD_WEBHOOK_URL"),
        os.getenv("DISCORD_WEBHOOK_URL_2")
    ]
    
    # فلترة القائمة للتأكد من وجود روابط صحيحة
    valid_webhooks = [w for w in webhooks if w and w.strip()]

    if not valid_webhooks:
        return
        
    # إرسال الرسالة إلى كل الروابط المتاحة
    for webhook in valid_webhooks:
        try:
            r = requests.post(webhook, json={"content": message}, timeout=15)
            if r.status_code >= 400:
                print(f"Discord Error ({webhook[:30]}...):", r.status_code)
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
        data = json.load(f)
        return [x for x in data if isinstance(x, dict) and "id" in x]

def save_database(name, data):
    os.makedirs(DATABASE, exist_ok=True)
    path = os.path.join(DATABASE, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def check_video_status(video_id):
    global cookies_alert_sent

    single_opts = YTDLP_OPTS.copy()
    single_opts["extract_flat"] = False

    try:
        with yt_dlp.YoutubeDL(single_opts) as ydl:
            ydl.extract_info(f"https://youtu.be/{video_id}", download=False)
        return "Public"

    except Exception as e:
        text = str(e).lower()

        if "sign in to confirm you're not a bot" in text or "cookie file is not in netscape format" in text or "cookies are no longer valid" in text:
            if not cookies_alert_sent:
                send_discord(
                    "@everyone 🚨 **YouTube Session Expired / Bot Detected**\n\n"
                    "The current session is blocked by CAPTCHA or expired.\n"
                    "Please update your YOUTUBE_COOKIES."
                )
                cookies_alert_sent = True
            return "Cookies Expired"

        if "private" in text: return "Private"
        elif "unavailable" in text or "copyright" in text or "country" in text or "age-restricted" in text or "login required" in text: return "Unavailable"
        elif "members" in text: return "Members"
        elif "429" in text or "too many requests" in text: return "Rate Limited"
        elif "network" in text or "timeout" in text or "urlopen error" in text: return "Network Error"

        return "Unknown Error"

def scan_playlist_fast(name, url):

    old = load_database(name)

    if not old:
        return True

    try:

        opts = YTDLP_OPTS.copy()
        opts["playlistend"] = 1

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        entries = info.get("entries", [])

        if not entries:
            return False

        latest_id = entries[0].get("id")

        if not latest_id:
            return False

        if latest_id == old[0]["id"]:

            print(
                f"{Color.BLUE}"
                f"✓ {name}: First video unchanged."
                f"{Color.RESET}"
            )

            return False

        print(
            f"{Color.YELLOW}"
            f"⚡ {name}: First video changed."
            f"{Color.RESET}"
        )

        return True

    except Exception as e:

        print(
            f"{Color.RED}"
            f"Fast Scan Failed ({name}): {e}"
            f"{Color.RESET}"
        )

        return True



def scan_playlist(name, url):
    print(f"{Color.CYAN}➤ Scanning Playlist:{Color.RESET} {Color.BOLD}{name}{Color.RESET} ... \n", end="", flush=True)

    old = load_database(name)
    old_ids = {x["id"] for x in old}
    current = []

    try:
        with yt_dlp.YoutubeDL(YTDLP_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)

        if "entries" not in info:
            raise Exception("Playlist has no entries.")

        total_videos = len(info["entries"])
        
        for index, entry in enumerate(info["entries"]):
            video_id = entry.get("id")
            if not video_id:
                continue

            title = entry.get("title")
            if not title or str(title).strip() == "":
                title = "Unknown Title"

            print(f" ⏳ Checking ({index+1}/{total_videos}): {video_id} ... ", end="", flush=True)

            old_video_data = next((x for x in old if x["id"] == video_id), None)

            # --- التخطي الذكي للفيديوهات العامة ---
            if old_video_data and old_video_data.get("status") == "Public":
                status = "Public"
                if old_video_data.get("title") and old_video_data.get("title") != "Unknown Title":
                    title = old_video_data.get("title")
                print(f"[{Color.GREEN}{status}{Color.RESET}] (Skipped - Already Public)")
            else:
                status = check_video_status(video_id)

                if status == "Cookies Expired":
                    print(f"{Color.RED}Bot Blocked! Scan aborted.{Color.RESET}")
                    return

                if status in ["Rate Limited", "Network Error", "Unknown Error"]:
                    if old_video_data:
                        status = old_video_data.get("status", status)
                    else:
                        status = "Unknown" 

                print(f"[{status}]")

                if index < total_videos - 1:
                    sleep_time = random.uniform(3, 6)
                    time.sleep(sleep_time)

            current.append({
                "id": video_id,
                "title": title,
                "status": status
            })

    except Exception as e:
        print(f"{Color.RED}Failed!{Color.RESET}")
        print(e)
        send_discord(f"❌ **Playlist Scan Failed**\n\n**Playlist:** {name}\n\n**Reason:**\n```{e}```")
        return

    print(f"\n{Color.GREEN}Done! ({len(current)} videos){Color.RESET}\n")

    new_ids = {x["id"] for x in current}
    changes = 0

    # 1. فيديوهات جديدة
    for video in current:
        if video["id"] not in old_ids:
            changes += 1
            safe_title = str(video.get('title') or 'Unknown Title')
            print(f"  {Color.GREEN}[+] NEW VIDEO:{Color.RESET} {safe_title[:50]}... ({video['status']})")
            send_discord(f"@everyone 🟢 **New Video**\n\n**Playlist:** {name}\n**Status:** {video['status']}\n\n**Title:**\n{safe_title}\n\n**ID:**\n{video['id']}\n\nhttps://youtu.be/{video['id']}")

    # 2. تغير الحالة (مثلاً من Private إلى Public أو العكس)
    for video in current:
        old_video = next((x for x in old if x["id"] == video["id"]), None)
        if not old_video: continue

        old_status = old_video.get("status", "Unknown")
        new_status = video["status"]

        if old_status != new_status:
            changes += 1
            safe_title = str(video.get('title') or 'Unknown Title')
            print(f"  {Color.YELLOW}[~] STATUS CHANGED:{Color.RESET} {safe_title[:50]}... [{old_status} ➜ {new_status}]")
            send_discord(f"@everyone 🟡 **Video Status Changed**\n\n**Playlist:** {name}\n\n**Title:**\n{safe_title}\n\n**ID:**\n{video['id']}\n\n**Status:**\n{old_status} ➜ {new_status}\n\nhttps://youtu.be/{video['id']}")

    # 3. فيديوهات محذوفة / مخفية تماماً من القائمة
    for video in old:
        if video["id"] not in new_ids:
            changes += 1
            safe_title = str(video.get('title') or 'Unknown Title')
            old_status = video.get('status', 'Unknown')
            
            print(f"  {Color.RED}[-] REMOVED:{Color.RESET} {safe_title[:50]}... (Was: {old_status})")
            send_discord(f"@everyone 🔴 **Video Removed**\n\n**Playlist:** {name}\n\n**Last Status:** {old_status}\n\n**Title:**\n{safe_title}\n\n**ID:**\n{video['id']}\n\nhttps://youtu.be/{video['id']}")

    if changes == 0:
        print(f"  {Color.BLUE}✓ No changes detected.{Color.RESET}")

    print("-" * 50)
    save_database(name, current)

def run():

    print(
        f"\n{Color.BOLD}{Color.CYAN}"
        "⚡ Starting Fast Playlist Inspection..."
        f"{Color.RESET}\n"
    )

    watchlist = load_watchlist()

    playlists = watchlist.get(
        "youtube_playlists",
        []
    )

    if not playlists:

        print(
            f"{Color.YELLOW}"
            "⚠ No playlists found in watchlist.json."
            f"{Color.RESET}"
        )

        return

    for playlist in playlists:

        playlist_id = playlist.get(
            "playlist_id"
        )

        if not playlist_id:
            continue

        url = (
            f"https://www.youtube.com/"
            f"playlist?list={playlist_id}"
        )

        # فحص سريع
        if scan_playlist_fast(
            playlist["name"],
            url
        ):

            print(
                f"{Color.YELLOW}"
                f"⚡ Change detected in {playlist['name']}."
                f"{Color.RESET}"
            )

            # إذا تغير أول فيديو نفذ الفحص الكامل
            scan_playlist(
                playlist["name"],
                url
            )

    print(
        f"\n{Color.GREEN}{Color.BOLD}"
        "✔ Fast scan completed!"
        f"{Color.RESET}\n"
    )

def run_full():

    print(
        f"\n{Color.BOLD}{Color.YELLOW}"
        "🔍 Starting Full Playlist Inspection..."
        f"{Color.RESET}\n"
    )

    watchlist = load_watchlist()

    playlists = watchlist.get(
        "youtube_playlists",
        []
    )

    if not playlists:

        print(
            f"{Color.YELLOW}"
            "⚠ No playlists found."
            f"{Color.RESET}"
        )

        return

    for playlist in playlists:

        playlist_id = playlist.get(
            "playlist_id"
        )

        if not playlist_id:
            continue

        url = (
            f"https://www.youtube.com/"
            f"playlist?list={playlist_id}"
        )

        scan_playlist(
            playlist["name"],
            url
        )

    print(
        f"\n{Color.GREEN}{Color.BOLD}"
        "✔ Full scan completed!"
        f"{Color.RESET}\n"
    )


def export_ids():
    watchlist = load_watchlist()
    playlists = watchlist.get("youtube_playlists", [])

    os.makedirs("output", exist_ok=True)
    filename = "output/all_ids.txt"

    print(f"\n{Color.CYAN}Exporting IDs to {filename} (Using Local Database)...{Color.RESET}\n")

    with open(filename, "w", encoding="utf-8") as out:
        for playlist in playlists:
            print(f"{Color.YELLOW}Exporting:{Color.RESET} {playlist['name']} ", end="", flush=True)
            
            out.write(f"{playlist['name']}\n")
            out.write("=" * 60 + "\n")

            local_data = load_database(playlist['name'])
            
            if local_data:
                for video in local_data:
                    status = video.get("status", "Unknown")
                    video_id = video.get("id")
                    
                    if status == "Public": icon = "🟢"
                    elif status == "Private": icon = "🔒"
                    elif status == "Unavailable": icon = "⚫"
                    elif status == "Members": icon = "👑"
                    else: icon = "❓"

                    line = f"{video_id:<15} {icon} {status}"
                    out.write(line + "\n")
            else:
                out.write("No videos scanned yet. Please run scanner first.\n")

            out.write("\n")
            print(f"{Color.GREEN}✔ Done!{Color.RESET}")

    print(f"\n{Color.GREEN}{Color.BOLD}✔ Export completed! File saved at: {filename}{Color.RESET}\n")

if __name__ == "__main__":

    # GitHub Actions
    if os.getenv("GITHUB_ACTIONS") == "true":

        run_full()

    # VPS Auto Mode
    elif "--auto" in sys.argv:
        
        # متغير لتسجيل وقت آخر فحص كامل (نضع وقت قديم جداً لكي يبدأ بفحص كامل فور التشغيل)
        last_full_scan_time = datetime.min 

        while True:
            now = datetime.now()

            # التحقق: هل مرت 5 دقائق (300 ثانية) على آخر فحص كامل؟
            if (now - last_full_scan_time).total_seconds() >= 300:
                print(
                    f"\n{Color.YELLOW}"
                    "🔍 Running Full Scan (Scheduled)..."
                    f"{Color.RESET}\n"
                )
                run_full()
                last_full_scan_time = datetime.now() # تحديث وقت آخر فحص كامل
            else:
                print(
                    f"\n{Color.CYAN}"
                    "⚡ Running Fast Scan..."
                    f"{Color.RESET}\n"
                )
                run()

            print(
                f"\n{Color.CYAN}"
                "Waiting 30 seconds..."
                f"{Color.RESET}\n"
            )
            time.sleep(30)

    # Interactive Mode
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

            choice = input(
                f"{Color.BOLD}Enter your choice (1-3): {Color.RESET}"
            ).strip()

            if choice == "1":

                run_full()

                input(
                    f"\n{Color.CYAN}Press Enter to return to main menu...{Color.RESET}"
                )

                clear_screen()

            elif choice == "2":

                export_ids()

                input(
                    f"\n{Color.CYAN}Press Enter to return to main menu...{Color.RESET}"
                )

                clear_screen()

            elif choice == "3":

                print(
                    f"\n{Color.GREEN}"
                    "Exiting... Goodbye! 👋"
                    f"{Color.RESET}"
                )

                break

            else:

                print(
                    f"{Color.RED}\n"
                    "✖ Invalid choice. Please try again.\n"
                    f"{Color.RESET}"
                )