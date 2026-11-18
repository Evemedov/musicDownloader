#!/usr/bin/env python3
import sys
import os
import re
import logging
from mutagen.oggopus import OggOpus
from YTMusicDlp import *
from tempfile import TemporaryDirectory


CMD = [
        "yt-dlp",
        "-f", "ba[acodec^=opus]/ba",
        "-x",
        "--audio-format", "opus",
        "--embed-metadata",
        "--embed-thumbnail",
        "--convert-thumbnails", "jpg",
        "--ppa", "ThumbnailsConvertor+ffmpeg:-c:v mjpeg -vf crop=ih:ih",
        "--cookies", "cookies.txt",
        "--print", "after_move:%(filepath)s|||%(title)s|||%(uploader)s|||%(id)s"
    ]

CLEANUP_PATTERNS = [
    r'[\(\[\{].*?[\)\]\}]',
    r'\b(official|audio|video|lyric|lyrics|music|hd|4k|remastered|remaster|topic|full|album)\b',
    r'\b(nightcore|slowed|reverb)\b',
    r'[-_]+',
]

PROVIDERS = ["NetEase", "Musixmatch", "LrcLib", "QQMusic", "Megalobiz"]

logger = logging.getLogger(__name__)


def clear_title(title: str) -> str:
    """Clear junk from the song name (Official Video), (Lyrics). thx gemini"""
    cleaned = title
    for pattern in CLEANUP_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    return ' '.join(cleaned.split()).strip()


def main():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    # Checks
    if len(sys.argv) < 2:
        logging.error("Usage: python main.py <URL> [PATH]")
        sys.exit(1)

    url = sys.argv[1]
    if len(sys.argv) > 2 and os.path.isdir(sys.argv[2]):
        path = sys.argv[2]
    else:
        path = "."
        logging.info(f"The path is not provided, the file will be downloaded into {os.path.abspath(path)}")

    if not os.path.isfile("cookies.txt"):
        logging.warning("For correct work you may pass your cookies to cookies.txt file")

    # Yt-dlp
    with TemporaryDirectory() as tmpdirname:
        cmd = [*CMD, "-P", f"temp:{tmpdirname}"]
        cmd = [*cmd, "-P", path, url]
        filepath, title, uploader, musicId = download_yt_dlp(cmd)

    # Search for lyrics
    logger.info(f"Searching for lrc via ytmusicapi: {musicId}")
    lyrics, isSynced = get_lrc_ytmusic(musicId)
    if not lyrics or not isSynced:
        logging.warning("No synced lyrics in yt music, searching from another source")
        clean_title = clear_title(title)
        logging.info(f"Searching for lrc for: '{uploader} {clean_title}'...")
        lyrics_syncedlyrics, isSynced = get_lrc_another_source(clean_title, uploader)
        if lyrics_syncedlyrics and isSynced:
            lyrics = lyrics_syncedlyrics

    # Write lyrics to file
    if lyrics:
        audio = OggOpus(filepath)
        # audio["lyrics" if isSynced else "unsyncedlyrics"] = lyrics
        audio["lyrics"] = lyrics
        audio.save()
        if isSynced:
            logging.info("Success, go check for a new file with lyrics.")
        else:
            logging.info("The unsynced lyrics was written to the file.")
    else:
        logging.warning(f"Cant find the lyrics for \"{uploader} {clean_title}\" :(")


if __name__ == "__main__":
    main()
