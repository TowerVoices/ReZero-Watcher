## 🚀 Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/TowerVoices/ReZero-Watcher.git
cd ReZero-Watcher
```

---

### 2. Create a virtual environment (recommended)

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS**

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

> 💡 This file is only required for the YouTube watcher.

---

## 6. Run the YouTube Watcher (Local)

Open **Windows PowerShell** and navigate to the project directory.

```bash
cd ReZero-Watcher
```

Start the YouTube watcher by running:

```bash
python watcher.py
```

The application will display the following menu:

```text
=============================================
        📺 YOUTUBE VIDEO INSPECTOR
=============================================

1. Scan Playlists & Check Changes
2. Export All IDs to Text File
3. Exit
```

### Menu Options

**1. Scan Playlists & Check Changes**

Scans all configured YouTube playlists, checks for newly uploaded videos, compares them with the local database, and sends Discord notifications whenever new content is detected.

**2. Export All IDs to Text File**

Exports all discovered YouTube video IDs into a text file.

**3. Exit**

Closes the application.

---

## 7. Run the Re:Zero Website Watcher (Local)

Open **Windows PowerShell** and navigate to the project directory.

```bash
cd ReZero-Watcher
```

Start the Re:Zero Website Watcher by running:

```bash
python rezero_site_watcher.py
```

The application will display the following menu:

```text
=============================================
          RE:ZERO SITE WATCHER
=============================================

1. Scan Story
2. Scan News
3. Scan Everything
4. Exit
```

### Menu Options

**1. Scan Story**

Checks the official Re:Zero website for newly published Story episodes and sends a Discord notification whenever a new episode is detected.

**2. Scan News**

Monitors the official News section for announcements, collaborations, event information, and other official updates, then sends a Discord notification whenever new content is published.

**3. Scan Everything**

Runs both the **Story** and **News** scanners in a single operation.

**4. Exit**

Closes the application.

---

## 8. 🗄️ Databases

The watcher automatically creates and updates the following database files:

- `database/videos.json`
- `database/story.json`
- `database/news.json`

These files store previously detected content to prevent duplicate Discord notifications.

> ⚠️ Do not delete these files unless you intentionally want the watcher to perform a fresh scan and treat all existing content as new.

---

## 9. 📁 Downloads

Downloaded images are automatically saved to:

- `downloads/`

Temporary images used for Discord uploads are stored in:

- `output/temp/`

---

## 10. ☁️ GitHub Actions

The project also supports automatic cloud monitoring through GitHub Actions.

### Required Repository Secrets

- `DISCORD_WEBHOOK_URL`
- `YOUTUBE_COOKIES`

Once these secrets have been added, no additional configuration is required.

---

## 11. 👨‍💻 Author

**TowerVoices**

Developer of Re:Zero automation and monitoring tools.

**X (Twitter):**
https://x.com/TowerVoices

Thank you for checking out this project!
