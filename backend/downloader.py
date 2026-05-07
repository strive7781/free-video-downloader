import json
import re
import subprocess
import time
import threading
from pathlib import Path
from urllib.parse import urlparse

from yt_dlp import YoutubeDL

DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Max age for temp files (1 hour)
_CLEANUP_MAX_AGE = 3600


def _sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def _vcodec_compat_rank(vcodec: str | None) -> int:
    """Lower = works in more players (prefer H.264 over AV1/HEVC)."""
    if not vcodec or vcodec == "none":
        return 99
    v = vcodec.lower()
    if v.startswith("avc1") or "h264" in v:
        return 0
    if v.startswith("hev1") or v.startswith("hev") or "h265" in v or "hevc" in v:
        return 1
    if "av01" in v or "av1" in v:
        return 2
    return 3


# Prefer H.264 merges first; fall back when site has no AVC.
_FORMAT_BEST_COMPAT = (
    "bv*[vcodec^=avc1]+ba/"
    "bestvideo[vcodec^=avc1]+bestaudio/"
    "bv*+ba/"
    "bestvideo+bestaudio/"
    "best"
)


def parse_video(url: str) -> dict:
    """Extract video metadata without downloading."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    formats_raw = info.get("formats") or []
    seen = set()
    formats = []
    video_only_heights = {}

    for f in formats_raw:
        height = f.get("height")
        vcodec = f.get("vcodec", "none")
        acodec = f.get("acodec", "none")
        has_video = vcodec and vcodec != "none"
        has_audio = acodec and acodec != "none"

        if has_video and has_audio and height:
            label = f"{height}p"
            if label not in seen:
                seen.add(label)
                formats.append({
                    "format_id": f["format_id"],
                    "ext": f.get("ext", "mp4"),
                    "resolution": label,
                    "filesize": f.get("filesize") or f.get("filesize_approx"),
                    "quality_note": f.get("format_note", ""),
                })
        elif has_video and not has_audio and height:
            cur = video_only_heights.get(height)
            if cur is None:
                video_only_heights[height] = f
            else:
                r_new = _vcodec_compat_rank(f.get("vcodec"))
                r_old = _vcodec_compat_rank(cur.get("vcodec"))
                if r_new < r_old:
                    video_only_heights[height] = f
                elif r_new == r_old and (f.get("tbr") or 0) > (cur.get("tbr") or 0):
                    video_only_heights[height] = f
        elif has_audio and not has_video:
            abr = f.get("abr")
            label = f"audio-{int(abr)}k" if abr else "audio"
            if label not in seen:
                seen.add(label)
                formats.append({
                    "format_id": f["format_id"],
                    "ext": f.get("ext", "m4a"),
                    "resolution": label,
                    "filesize": f.get("filesize") or f.get("filesize_approx"),
                    "quality_note": f.get("format_note", ""),
                })

    # For DASH-style platforms, create merged format entries from video-only streams
    has_video_formats = any("p" in f["resolution"] for f in formats)
    if not has_video_formats and video_only_heights:
        for height in sorted(video_only_heights.keys(), reverse=True):
            f = video_only_heights[height]
            label = f"{height}p"
            if label not in seen:
                seen.add(label)
                vnote = "合并音视频"
                if _vcodec_compat_rank(f.get("vcodec")) == 0:
                    vnote = "合并音视频 · H.264 兼容"
                elif _vcodec_compat_rank(f.get("vcodec")) == 2:
                    vnote = "合并音视频 · AV1（需支持 AV1 的播放器）"
                formats.insert(0, {
                    "format_id": f"{f['format_id']}+bestaudio",
                    "ext": "mp4",
                    "resolution": label,
                    "filesize": f.get("filesize") or f.get("filesize_approx"),
                    "quality_note": f.get("format_note", "") or vnote,
                })

    # Always offer a "best" option at the top
    formats.insert(0, {
        "format_id": _FORMAT_BEST_COMPAT,
        "ext": "mp4",
        "resolution": "最佳画质",
        "filesize": None,
        "quality_note": "优先 H.264，兼容常见播放器",
    })

    return {
        "title": info.get("title", "Unknown"),
        "thumbnail": info.get("thumbnail", ""),
        "duration": info.get("duration", 0),
        "uploader": info.get("uploader", ""),
        "webpage_url": info.get("webpage_url", url),
        "extractor": info.get("extractor", ""),
        "description": (info.get("description") or "")[:300],
        "view_count": info.get("view_count"),
        "formats": formats,
    }


def _download_opts(url: str, format_id: str) -> dict:
    """yt-dlp options tuned to reduce incomplete reads (CDN / flaky HTTP)."""
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""
    return {
        "format": format_id,
        "outtmpl": str(DOWNLOAD_DIR / "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
        # Retry & resume (fixes "X bytes read, Y more expected")
        "retries": 20,
        "fragment_retries": 20,
        "file_access_retries": 10,
        "retry_sleep_functions": {"http": lambda n: min(8.0, 2**n)},
        "socket_timeout": 90,
        "continuedl": True,
        # Single fragment at a time often stabilizes Bilibili / DASH CDNs
        "concurrent_fragment_downloads": 1,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": url,
            **({"Origin": origin} if origin else {}),
        },
    }


def _primary_video_codec(path: Path) -> str | None:
    """Return first video stream codec_name, or None if unavailable."""
    try:
        r = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json", "-show_streams",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        data = json.loads(r.stdout)
        for s in data.get("streams") or []:
            if s.get("codec_type") == "video":
                return s.get("codec_name")
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return None


def _codec_is_widely_playable(codec: str | None) -> bool:
    """Codecs that Windows / common players show without extra decoders."""
    if not codec:
        return True
    c = codec.lower()
    if c in ("h264", "mpeg4", "msmpeg4v3", "mjpeg", "vp8"):
        return True
    if c.startswith("avc"):
        return True
    return False


def _transcode_video_to_h264_inplace(path: Path) -> None:
    """Re-encode video to H.264; keep audio; same path for API file_id."""
    tmp = path.with_suffix(".kinema_reencode.mp4")
    try:
        r = subprocess.run(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(path),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "copy",
                "-movflags", "+faststart",
                str(tmp),
            ],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as e:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            "未找到 ffmpeg，无法进行 H.264 转码。请安装 ffmpeg 并加入系统 PATH。"
        ) from e

    if r.returncode != 0:
        tmp.unlink(missing_ok=True)
        detail = (r.stderr or r.stdout or "ffmpeg 转码失败").strip()[:400]
        raise RuntimeError(detail)

    try:
        path.unlink()
        tmp.rename(path)
    except OSError as e:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"写入转码后的文件失败: {e}") from e


def download_video(url: str, format_id: str) -> tuple[Path, str]:
    """Download video and return (file_path, display_title)."""
    opts = _download_opts(url, format_id)
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url)
        filename = ydl.prepare_filename(info)
        title = _sanitize_filename(info.get("title", "video"))
        ext = info.get("ext", "mp4")
        # yt-dlp may change extension after merge
        filepath = Path(filename)
        if not filepath.exists():
            mp4_path = filepath.with_suffix(".mp4")
            if mp4_path.exists():
                filepath = mp4_path
                ext = "mp4"
        if not filepath.exists():
            raise RuntimeError("下载完成但未找到文件，请重试或更换清晰度")
        vcodec = _primary_video_codec(filepath)
        if vcodec and not _codec_is_widely_playable(vcodec):
            _transcode_video_to_h264_inplace(filepath)
        display_name = f"{title}.{ext}"
        return filepath, display_name


def cleanup_old_files():
    """Remove downloaded files older than _CLEANUP_MAX_AGE seconds."""
    now = time.time()
    for f in DOWNLOAD_DIR.iterdir():
        if f.is_file() and (now - f.stat().st_mtime) > _CLEANUP_MAX_AGE:
            try:
                f.unlink()
            except OSError:
                pass


def start_cleanup_scheduler(interval: int = 600):
    """Run cleanup in a background thread every `interval` seconds."""
    def _loop():
        while True:
            cleanup_old_files()
            time.sleep(interval)
    t = threading.Thread(target=_loop, daemon=True)
    t.start()
