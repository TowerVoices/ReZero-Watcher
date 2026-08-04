## 🚀 Running Locally

### 1. Clone the repository
```bash
git clone https://github.com/TowerVoices/ReZero-Watcher.git
cd ReZero-Watcher
```

---

### 2. Create a virtual environment (recommended)

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

### 4. Create a Discord Webhook
Create a `.env` file in the project root.
```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxxxxxxxxxxxxx
```

---

### 5. YouTube Watcher Setup
Export your YouTube cookies into:
```text
cookies.txt
```
> 💡 *This file is only required for the YouTube watcher.*

---

### 6. Run the YouTube Watcher
```bash
python watcher.py
```
**Menu:**
1. Scan Watch List 01
2. Scan Watch List 02
3. Scan Everything
4. Exit

---

### 7. Run the Re:Zero Website Watcher
```bash
python rezero_site_watcher.py
```
**Menu:**
1. Scan Story
2. Scan News
3. Scan Everything
4. Exit

---

## 🗄️ Databases

The watcher automatically creates and updates:
* `database/videos.json`
* `database/story.json`
* `database/news.json`

These files store previously detected content to prevent duplicate Discord notifications.

---

## 📁 Downloads

Downloaded images are automatically saved to:
* `downloads/`

Temporary images used for Discord uploads are stored in:
* `output/temp/`

---

## ☁️ GitHub Actions

The project also supports automatic cloud monitoring through GitHub Actions.

**Required repository secrets:**

---
* `DISCORD_WEBHOOK_URL`
* `YOUTUBE_COOKIES`

## 👨‍💻 Author

**TowerVoices**

Developer of Re:Zero automation tools and monitoring utilities.

- **X (Twitter):** https://x.com/TowerVoices

Thank you for checking out this project!

No additional configuration is required after adding the secrets.
