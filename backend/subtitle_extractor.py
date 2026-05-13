import logging
import re
from pathlib import Path
from urllib.parse import urlparse

import httpx
from yt_dlp import YoutubeDL

from downloader import _extract_with_retry, _cookie_opts as _dl_cookie_opts
from douyin import is_douyin_url, DouyinParser

logger = logging.getLogger(__name__)

_LANG_PRIORITY = ["zh-Hans", "zh", "zh-CN", "zh-TW", "en", "en-US", "en-GB"]

def _pick_best_lang(available: dict) -> str | None:
    """From available subtitle languages, pick the best one by priority."""
    for lang in _LANG_PRIORITY:
        if lang in available:
            return lang
    if available:
        return next(iter(available))
    return None


def _parse_vtt_content(content: str) -> list[dict]:
    """Parse VTT/SRT subtitle content into structured segments."""
    segments = []
    lines = content.strip().split("\n")
    current_text = []
    current_start = None

    timestamp_re = re.compile(
        r"(\d{1,2}:)?(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{1,2}:)?(\d{2}):(\d{2})[.,](\d{3})"
    )

    for line in lines:
        line = line.strip()
        match = timestamp_re.match(line)
        if match:
            if current_text and current_start is not None:
                text = " ".join(current_text).strip()
                text = re.sub(r"<[^>]+>", "", text)
                if text:
                    segments.append({"start": current_start, "text": text})
            h1 = int(match.group(1).rstrip(":")) if match.group(1) else 0
            m1 = int(match.group(2))
            s1 = int(match.group(3))
            current_start = round(h1 * 3600 + m1 * 60 + s1, 1)
            current_text = []
        elif line and not line.isdigit() and not line.startswith("WEBVTT"):
            current_text.append(line)

    if current_text and current_start is not None:
        text = " ".join(current_text).strip()
        text = re.sub(r"<[^>]+>", "", text)
        if text:
            segments.append({"start": current_start, "text": text})

    return _deduplicate_segments(segments)


def _deduplicate_segments(segments: list[dict]) -> list[dict]:
    """Remove consecutive duplicate text entries."""
    if not segments:
        return segments
    result = [segments[0]]
    for seg in segments[1:]:
        if seg["text"] != result[-1]["text"]:
            result.append(seg)
    return result


def _is_bilibili_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return "bilibili.com" in host or "b23.tv" in host


def _parse_bvid(url: str) -> str | None:
    m = re.search(r"(BV[a-zA-Z0-9]+)", url)
    return m.group(1) if m else None


def _extract_bilibili_subtitles(url: str) -> dict | None:
    """Fetch B站 CC subtitles via dm/view API (逐句带时间戳)."""
    bvid = _parse_bvid(url)
    if not bvid:
        return None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"https://www.bilibili.com/video/{bvid}",
    }

    try:
        view_resp = httpx.get(
            f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}",
            headers=headers, timeout=15,
        )
        view_data = view_resp.json().get("data", {})
        cid = view_data.get("cid")
        aid = view_data.get("aid")
        if not cid or not aid:
            return None

        dm_resp = httpx.get(
            f"https://api.bilibili.com/x/v2/dm/view?aid={aid}&oid={cid}&type=1",
            headers=headers, timeout=15,
        )
        dm_data = dm_resp.json().get("data", {})
        subtitle_list = dm_data.get("subtitle", {}).get("subtitles", [])

        if not subtitle_list:
            return None

        best = subtitle_list[0]
        for s in subtitle_list:
            lang = s.get("lan", "")
            if lang in ("zh", "zh-Hans"):
                best = s
                break

        sub_type = "auto" if best.get("lan", "").startswith("ai-") else "platform"

        sub_url = best.get("subtitle_url", "")
        if sub_url.startswith("//"):
            sub_url = "https:" + sub_url
        if not sub_url:
            return None

        sub_resp = httpx.get(sub_url, headers=headers, timeout=15)
        body = sub_resp.json().get("body", [])

        segments = []
        for item in body:
            content = item.get("content", "").strip()
            if not content:
                continue
            segments.append({
                "start": round(item.get("from", 0), 2),
                "text": content,
            })

        if not segments:
            return None

        full_text = " ".join(seg["text"] for seg in segments)
        return {
            "subtitles": segments,
            "full_text": full_text,
            "language": best.get("lan", "zh"),
            "source": sub_type,
        }
    except Exception as e:
        logger.warning("Bilibili subtitle API failed: %s", e)
        return None


def extract_subtitles(url: str) -> dict:
    """
    Extract subtitles/transcript from a video URL.

    Returns:
        {
            "subtitles": [{"start": 0.0, "text": "..."},...],
            "full_text": "complete concatenated text",
            "language": "zh",
            "source": "platform" | "auto" | "description"
        }
    """
    if is_douyin_url(url):
        return _extract_douyin_description(url)

    if _is_bilibili_url(url):
        result = _extract_bilibili_subtitles(url)
        if result:
            return result

    return _extract_via_ytdlp(url)


def _extract_douyin_description(url: str) -> dict:
    """For Douyin, use video description as content (short videos rarely have subtitles)."""
    parser = DouyinParser(download_dir=str(Path(__file__).parent / "downloads"))
    try:
        result = parser.parse(url)
        desc = result.get("description", "") or result.get("title", "")
        if not desc:
            raise ValueError("抖音视频没有描述信息，无法生成总结")
        return {
            "subtitles": [{"start": 0.0, "text": desc}],
            "full_text": desc,
            "language": "zh",
            "source": "description",
        }
    except Exception as e:
        raise ValueError(f"抖音视频信息提取失败: {e}") from e


def _extract_via_ytdlp(url: str) -> dict:
    """Extract subtitles using yt-dlp (platform subs or auto-generated)."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitlesformat": "vtt/srt/best",
    }
    opts.update(_dl_cookie_opts())
    info = _extract_with_retry(opts, url, download=False)

    subs = info.get("subtitles") or {}
    auto_subs = info.get("automatic_captions") or {}

    subtitle_content = None
    language = None
    source = "platform"

    lang = _pick_best_lang(subs)
    if lang and subs[lang]:
        subtitle_content = _download_subtitle(subs[lang], opts)
        language = lang
        source = "platform"

    if not subtitle_content:
        lang = _pick_best_lang(auto_subs)
        if lang and auto_subs[lang]:
            subtitle_content = _download_subtitle(auto_subs[lang], opts)
            language = lang
            source = "auto"

    if not subtitle_content:
        desc = info.get("description", "")
        title = info.get("title", "")
        fallback = f"{title}\n\n{desc}".strip() if desc else title
        if not fallback:
            raise ValueError("该视频没有可用的字幕或描述信息，无法生成总结")
        return {
            "subtitles": [{"start": 0.0, "text": fallback}],
            "full_text": fallback,
            "language": "zh",
            "source": "description",
        }

    segments = _parse_vtt_content(subtitle_content)
    if not segments:
        raise ValueError("字幕解析为空，无法生成总结")

    full_text = " ".join(seg["text"] for seg in segments)

    return {
        "subtitles": segments,
        "full_text": full_text,
        "language": language,
        "source": source,
    }


def _download_subtitle(sub_formats: list[dict], base_opts: dict) -> str | None:
    """Download subtitle content and return as string."""
    preferred_exts = ["vtt", "srt", "json3"]
    chosen = None
    for ext in preferred_exts:
        for fmt in sub_formats:
            if fmt.get("ext") == ext:
                chosen = fmt
                break
        if chosen:
            break
    if not chosen and sub_formats:
        chosen = sub_formats[0]

    if not chosen or "url" not in chosen:
        return None

    import httpx
    try:
        resp = httpx.get(chosen["url"], timeout=30, follow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.warning("Failed to download subtitle: %s", e)
        return None
