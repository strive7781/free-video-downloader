import json
import logging
import random
import re
import subprocess
import time
import threading
from pathlib import Path
from urllib.parse import urlparse

from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Max age for temp files (1 hour)
_CLEANUP_MAX_AGE = 3600

# ---------------------------------------------------------------------------
# Cookie helpers — only use cookies.txt if present, never read browser DB
# ---------------------------------------------------------------------------
_COOKIES_FILE = Path(__file__).parent / "cookies.txt"

_MAX_RETRIES = 4
_RETRY_BASE_DELAY = 2.0


def _cookie_opts() -> dict:
    if _COOKIES_FILE.is_file():
        logger.info("Using cookies.txt at %s", _COOKIES_FILE)
        return {"cookiefile": str(_COOKIES_FILE)}
    return {}


def _is_retryable(err: Exception) -> bool:
    msg = str(err)
    return any(k in msg for k in ("403", "Forbidden", "429", "Too Many", "timed out", "Connection"))


def _extract_with_retry(opts: dict, url: str, download: bool = False):
    """
    Call yt-dlp extract_info with retries on transient HTTP errors (403/429 etc.).
    Uses exponential backoff with jitter.
    """
    last_err = None
    for attempt in range(_MAX_RETRIES):
        try:
            with YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=download)
        except Exception as e:
            last_err = e
            if attempt < _MAX_RETRIES - 1 and _is_retryable(e):
                delay = _RETRY_BASE_DELAY * (2 ** attempt) + random.uniform(0, 1)
                logger.warning("yt-dlp attempt %d/%d failed (%s), retrying in %.1fs…",
                               attempt + 1, _MAX_RETRIES, str(e)[:100], delay)
                time.sleep(delay)
            else:
                break
    raise last_err


def _format_size(bytes_val) -> str:
    """Human-readable file size string."""
    if not bytes_val:
        return ""
    if bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f}KB"
    if bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f}MB"
    return f"{bytes_val / (1024 * 1024 * 1024):.2f}GB"


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


_FORMAT_BEST_QUALITY = "bestvideo+bestaudio/best"


def parse_video(url: str) -> dict:
    """Extract video metadata without downloading."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
    }
    opts.update(_cookie_opts())
    info = _extract_with_retry(opts, url, download=False)

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
                filesize = f.get("filesize") or f.get("filesize_approx")
                size_str = _format_size(filesize) if filesize else ""
                note = f"(视频+音频合并, {size_str})" if size_str else "(视频+音频合并)"
                formats.append({
                    "format_id": f["format_id"],
                    "ext": f.get("ext", "mp4"),
                    "resolution": label,
                    "filesize": filesize,
                    "quality_note": note,
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
                filesize = f.get("filesize") or f.get("filesize_approx")
                size_str = _format_size(filesize) if filesize else ""
                note = f"(仅音频, {size_str})" if size_str else "(仅音频)"
                formats.append({
                    "format_id": f["format_id"],
                    "ext": f.get("ext", "m4a"),
                    "resolution": label,
                    "filesize": filesize,
                    "quality_note": note,
                })

    # Always show DASH video-only streams as merged options (video+bestaudio)
    if video_only_heights:
        for height in sorted(video_only_heights.keys(), reverse=True):
            f = video_only_heights[height]
            label = f"{height}p"
            if label not in seen:
                seen.add(label)
                filesize = f.get("filesize") or f.get("filesize_approx")
                size_str = _format_size(filesize) if filesize else ""
                note = f"(仅视频, {size_str})" if size_str else "(仅视频)"
                formats.append({
                    "format_id": f"{f['format_id']}+bestaudio",
                    "ext": "mp4",
                    "resolution": label,
                    "filesize": filesize,
                    "quality_note": note,
                })

    # Sort formats by resolution height descending
    def _height_key(fmt):
        m = __import__('re').match(r'(\d+)p', fmt.get('resolution', ''))
        return int(m.group(1)) if m else 0
    formats.sort(key=_height_key, reverse=True)

    # Determine best resolution label from available formats
    max_height = 0
    for fmt in formats:
        m = __import__('re').match(r'(\d+)p', fmt.get('resolution', ''))
        if m:
            max_height = max(max_height, int(m.group(1)))

    best_label = f"{max_height}p 最佳" if max_height > 0 else "最佳画质"

    # Always offer a "best quality" option at the top (no codec restriction)
    formats.insert(0, {
        "format_id": _FORMAT_BEST_QUALITY,
        "ext": "mp4",
        "resolution": best_label,
        "filesize": None,
        "quality_note": "(视频+音频合并)",
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
    opts = {
        "format": format_id,
        "outtmpl": str(DOWNLOAD_DIR / "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "merge_output_format": "mp4",
        "retries": 20,
        "fragment_retries": 20,
        "file_access_retries": 10,
        "retry_sleep_functions": {"http": lambda n: min(8.0, 2**n)},
        "socket_timeout": 90,
        "continuedl": True,
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
    opts.update(_cookie_opts())
    return opts


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
    info = _extract_with_retry(opts, url, download=True)
    if not info:
        raise RuntimeError("yt-dlp 未返回视频信息，下载可能未成功")
    with YoutubeDL(opts) as ydl:
        filename = ydl.prepare_filename(info)
    if not filename:
        raise RuntimeError("下载完成但未获取文件名")
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
