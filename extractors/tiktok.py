import yt_dlp
from rich import print

def tiktok_analyzer(url):

    opts = {
        "quiet": True,
        "skip_download": True
    }

    try:

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        print("\n[bold green]Platform[/bold green] : TikTok")
        print(f"[cyan]ID[/cyan]       : {info.get('id')}")
        print(f"[cyan]Status[/cyan]   : Public")
        print(f"[cyan]Author[/cyan]   : {info.get('uploader')}")
        print(f"[cyan]Title[/cyan]    : {info.get('title')}")

    except Exception as e:

        print("\n[bold green]Platform[/bold green] : TikTok")
        print("[red]Status[/red] : Not Public")
        print(e)