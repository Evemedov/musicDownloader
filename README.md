# YTM Opus Downloader & Auto-Lyrics Embedder

A Python script designed to download tracks from **YouTube / YouTube Music** in high-quality **Opus** format, metadata embedding, and synced lyrics (`.lrc`) fetching.

## Key Features

- **Native Opus Stream:** Extracts the best original audio stream (`itag 251`) directly from YouTube servers without lossy re-encoding.
- **Square Album Art:** Automatically crops standard 16:9 video thumbnails to a clean 1:1 square centered image, removing side blur and bars.
- **Synced Karaoke Lyrics:** Fetches `.lrc` synced lyrics using `syncedlyrics` (supporting NetEase, Musixmatch, LrcLib, QQMusic, Megalobiz, Genius) and embeds them directly into the `.opus` file tags (`LYRICS` and `UNSYNCEDLYRICS`).

---

## Prerequisites

This script requires **`ffmpeg`** installed on your system, along with the following Python packages:

```bash
pip install -r requirements.txt
```
## Usage

```bash
python main.py <URL> [PATH]
```
If PATH is not provided, it will download the music to scripts folder. 
