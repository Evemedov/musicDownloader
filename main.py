#!/usr/bin/env python3
import sys
import subprocess
import os
import re
import logging
from mutagen.oggopus import OggOpus
import syncedlyrics
from ytmusicapi import YTMusic

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

ytmusic = YTMusic()


def get_lrc_ytmusic(musicId: str) -> tuple[str | None, bool]: # lyrics, is lyrics synced
    """Downloads synced lyrics with ytmusicapi"""
    try:
        browseId = ytmusic.get_watch_playlist(videoId=musicId)
        if not browseId.get("lyrics"):
            logger.warning("Can not get lyricsId from ytmusic")
            return None, False

        data = ytmusic.get_lyrics(browseId.get("lyrics"), timestamps=True)
        if not data:
            logger.warning("Can not get lyrics from ytmusic")
            return None, False

        if not data.get("hasTimestamps"):
            return data.get("lyrics"), False

        lines = []
        for line in data["lyrics"]:
            minutes, rest = divmod(line.start_time, 60_000)  # ms -> min + div
            seconds = rest / 1000
            lines.append(f"[{minutes:02d}:{seconds:05.2f}]{line.text}")
        return "\n".join(lines), True

    except Exception as e:
        logging.error(f"Error while executing ytmusicapi: {e}")
        return None, False


def get_lrc_another_source(track_name: str, artist_name: str) -> tuple[str | None, bool]: # lyrics, is lyrics synced
    """Downloads synced lyrics with syncedlyrics"""
    try:
        lrc = syncedlyrics.search(f"{artist_name} {track_name}", synced_only=True, providers=PROVIDERS)
        if lrc:
            return lrc, True
        lrc = syncedlyrics.search(f"{artist_name} {track_name}", plain_only=True, providers=PROVIDERS)
        if lrc:
            return lrc, False
        return lrc, False
    except Exception as e:
        logging.error(f"Error while executing syncedlyrics: {e}")
    return None, False


def download_yt_dlp(url: str, path: str) -> tuple[str, str, str, str]:
    """Downloads .opus from Youtube Music with yt-dlp"""
    cmd = [*CMD, "-P", path, url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"yt-dlp error: \n Stdout: {result.stdout} \n Stderr: {result.stderr}")
        sys.exit(result.returncode)

    output_lines = [line for line in result.stdout.strip().splitlines() if "|||" in line]
    if not output_lines:
        logging.error(f"Something wrong with --print in yt-dlp: {result.stdout}")
        sys.exit(1)

    filepath, title, uploader, musicId = output_lines[-1].split("|||")
    if not os.path.isfile(filepath):
        logging.error(f"File {filepath} was not found")
        sys.exit(1)

    logging.info(f"Downloaded file: {filepath}")
    return filepath, title, uploader, musicId


def clear_title(title: str) -> str:
    """Clear junk from the song name (Official Video), (Lyrics). thx gemini"""
    cleaned = title
    for pattern in CLEANUP_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    return ' '.join(cleaned.split()).strip()


def main():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

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

    filepath, title, uploader, musicId = download_yt_dlp(url, path)

    logger.info(f"Searching for lrc via ytmusicapi: {musicId}")
    lyrics, isSynced = get_lrc_ytmusic(musicId)
    if not lyrics or not isSynced:
        logging.warning("No synced lyrics in yt music, searching from another source")
        clean_title = clear_title(title)
        logging.info(f"Searching for lrc for: '{uploader} {clean_title}'...")
        lyrics_syncedlyrics, isSynced = get_lrc_another_source(clean_title, uploader)
        if lyrics_syncedlyrics and isSynced:
            lyrics = lyrics_syncedlyrics

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
