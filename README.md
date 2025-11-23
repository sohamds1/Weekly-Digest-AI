# 📺 LazyTube Digest: AI-Powered Weekly Newsletter

Curate a YouTube playlist. Get a summarized newsletter in your inbox every Monday. Zero cost. Zero servers.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-green)
![AI](https://img.shields.io/badge/AI-Gemini_1.5_Flash-orange)

## 🧐 What is this?

This is a "set it and forget it" hobby project for the lazy but curious mind.

Instead of watching hours of video content, you simply add interesting videos to a **Public YouTube Playlist**. Every Monday morning, this tool wakes up, fetches the transcripts of the latest videos, summarizes them into a poignant, high-signal newsletter using Google's Gemini 1.5 Pro/Flash, and emails it to you (via GitHub Issues).

### Why use this?

- **100% Free**: Uses GitHub Actions (free tier) and Google Gemini API (free tier).
- **No Servers**: No need to pay for hosting or set up a database.
- **Open Source**: Fork it, add your API key, and it works for you.
- **Privacy**: Your API keys are stored securely in GitHub Secrets.

## ⚙️ How to Use (3-Minute Setup)

### Step 1: Fork this Repository

Click the **Fork** button in the top-right corner of this page to create your own copy.

### Step 2: Get your Free Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Click **"Get API Key"**.
3. Copy the key string.

### Step 3: Add the Secret

1. In your forked repository, go to **Settings → Secrets and variables → Actions**.
2. Click **New repository secret**.
3. **Name**: `GEMINI_API_KEY`
4. **Secret**: (Paste the key you copied in Step 2).
5. Click **Add secret**.

### Step 4: Set Your Playlist

1. Open the file `.github/workflows/weekly_digest.yml`.
2. Click the **Pencil Icon** to edit.
3. Look for the line: `PLAYLIST_ID: 'YOUR_PLAYLIST_ID_HERE'`.
4. Replace `YOUR_PLAYLIST_ID_HERE` with the ID of your YouTube playlist.
   - (Note: The ID is the part of the URL after `&list=`. Example: `PLwXf5...`)
5. Commit changes.

### Step 5: Enable Permissions (Important!)

Since this script writes a "Github Issue" to send you the email, you must allow it.

1. Go to **Settings → Actions → General**.
2. Scroll down to **Workflow permissions**.
3. Select **"Read and write permissions"**.
4. Click **Save**.

## 🚀 Running it Manually (To Test)

You don't have to wait for Monday to see if it works!

1. Go to the **Actions** tab in your repo.
2. Click on **"Weekly Newsletter Digest"** on the left sidebar.
3. Click **"Run workflow"** (dropdown on the right) → **Run workflow**.
4. Wait ~1 minute.
5. Check your **Issues** tab (or your email inbox) for the summary!

## 🛠️ Customization

### Want to change the AI personality?

Open `main.py` and find the `summarize_with_gemini` function. Edit the `prompt` variable to change how the AI writes (e.g., "Roast these videos" or "Explain like I'm 5").

### Want to change the schedule?

Open `.github/workflows/weekly_digest.yml` and edit the cron schedule:

```yaml
- cron: '0 8 * * 1' # Currently: Every Monday at 8:00 AM UTC
```

## ⚠️ Troubleshooting

### "Resource not accessible by integration" Error:

This means you skipped **Step 5**. Go to Settings -> Actions -> General and enable "Read and write permissions", or ensure the `.yml` file has the permissions block included.

### "No videos found":

Ensure your YouTube Playlist is set to **Public** or **Unlisted**, not **Private**.

## 📜 License

MIT License. Feel free to fork, modify, and use as you wish!
