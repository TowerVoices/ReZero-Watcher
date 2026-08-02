from extractors.youtube import youtube_analyzer
from extractors.tiktok import tiktok_analyzer
from extractors.tiktok_scan import scan_account

print("=" * 40)
print("Video Inspector v0.1")
print("=" * 40)

url = input("\nEnter URL: ").strip()

if "youtube.com" in url or "youtu.be" in url:
    youtube_analyzer(url)

elif "tiktok.com" in url:

    # إذا كان رابط فيديو
    if "/video/" in url:
        tiktok_analyzer(url)

    # إذا كان رابط حساب
    else:
        scan_account(url)

else:
    print("\nUnsupported platform.")