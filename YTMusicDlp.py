import subprocess
import syncedlyrics
from ytmusicapi import YTMusic
import logging
import sys
import os

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


def download_yt_dlp(cmd: str) -> tuple[str, str, str, str]:
    """Downloads .opus from Youtube Music with yt-dlp"""
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


if __name__ == "__main__":
    print("Its the library file, go away! (launch the main.py)")
    exit()
