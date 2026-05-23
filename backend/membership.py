"""Free vs VIP tier rules and enforcement."""

from __future__ import annotations

import re

from fastapi import HTTPException

from billing import FREE_DAILY_DOWNLOAD_LIMIT

FREE_MAX_HEIGHT = 720
FORMAT_BEST_QUALITY = "bestvideo+bestaudio/best"
FREE_BEST_QUALITY = "bestvideo[height<=720]+bestaudio/best[height<=720]/best[height<=720]"

_FREE_BEST_FORMAT = {
    "format_id": FREE_BEST_QUALITY,
    "ext": "mp4",
    "resolution": "720p 及以下最佳",
    "height": FREE_MAX_HEIGHT,
    "filesize": None,
    "quality_note": "(免费用户最高 720p，自动合并音视频)",
}


def tier_meta(is_vip: bool) -> dict:
    return {
        "is_vip": is_vip,
        "max_height": None if is_vip else FREE_MAX_HEIGHT,
        "daily_download_limit": None if is_vip else FREE_DAILY_DOWNLOAD_LIMIT,
        "features": {
            "ai_summary": is_vip,
            "subtitle_export": is_vip,
            "audio_extract": is_vip,
            "hd_above_720p": is_vip,
        },
    }


def require_vip(user: dict, feature: str = "该功能") -> None:
    if user.get("is_vip"):
        return
    raise HTTPException(
        status_code=403,
        detail=f"{feature}为 VIP 专属功能，升级后可无限下载、4K 超清与 AI 总结等高级能力。",
    )


def _format_height(fmt: dict) -> int | None:
    if fmt.get("height"):
        return int(fmt["height"])
    resolution = str(fmt.get("resolution") or "")
    if "audio" in resolution.lower():
        return None
    match = re.search(r"(\d+)p", resolution)
    return int(match.group(1)) if match else None


def is_audio_only_format(fmt: dict) -> bool:
    resolution = str(fmt.get("resolution") or "").lower()
    return resolution.startswith("audio") or "仅音频" in str(fmt.get("quality_note") or "")


def _max_video_height(formats: list[dict]) -> int:
    heights = [_format_height(f) or 0 for f in formats if not is_audio_only_format(f)]
    return max(heights) if heights else 0


def _locked_vip_formats(formats: list[dict]) -> list[dict]:
    """Show higher tiers as locked so free users know VIP unlocks them."""
    locked: list[dict] = []
    seen: set[int] = set()
    for fmt in formats:
        if is_audio_only_format(fmt):
            continue
        height = _format_height(fmt)
        if height is None or height <= FREE_MAX_HEIGHT or height in seen:
            continue
        seen.add(height)
        locked.append(
            {
                **fmt,
                "format_id": f"vip-locked-{height}p",
                "vip_only": True,
                "quality_note": f"(VIP 专属 · 升级后可下载 {height}p)",
            }
        )
    locked.sort(key=lambda f: _format_height(f) or 0, reverse=True)
    return locked


def filter_formats(formats: list[dict], is_vip: bool) -> list[dict]:
    """Return formats allowed for the user's tier."""
    if is_vip:
        return formats

    filtered: list[dict] = []
    has_capped_best = False

    for fmt in formats:
        fmt_id = fmt.get("format_id", "")
        if fmt_id == FORMAT_BEST_QUALITY:
            filtered.append(dict(_FREE_BEST_FORMAT))
            has_capped_best = True
            continue
        if is_audio_only_format(fmt):
            continue
        height = _format_height(fmt)
        if height is not None and height > FREE_MAX_HEIGHT:
            continue
        filtered.append(fmt)

    if not has_capped_best:
        filtered.insert(0, dict(_FREE_BEST_FORMAT))

    if not any(not is_audio_only_format(f) and f.get("format_id") != FREE_BEST_QUALITY for f in filtered):
        # Only capped-best or empty explicit streams — keep capped-best only
        filtered = [dict(_FREE_BEST_FORMAT)]

    filtered.sort(key=lambda f: _format_height(f) or 0, reverse=True)
    return filtered


def validate_download_format(user: dict, formats: list[dict], format_id: str) -> None:
    """Ensure free users cannot bypass frontend and download VIP-only formats."""
    if user.get("is_vip"):
        return
    if format_id.startswith("vip-locked-"):
        raise HTTPException(status_code=403, detail="该清晰度为 VIP 专属，请先升级会员。")
    if format_id == FORMAT_BEST_QUALITY:
        raise HTTPException(
            status_code=403,
            detail=f"免费用户最高支持 {FREE_MAX_HEIGHT}p，请升级 VIP 解锁 4K 超清与最佳画质。",
        )
    allowed_ids = {f.get("format_id") for f in filter_formats(formats, False)}
    if format_id not in allowed_ids:
        raise HTTPException(
            status_code=403,
            detail=(
                f"免费用户仅可下载 {FREE_MAX_HEIGHT}p 及以下清晰度，"
                "不可下载音频单独提取或更高画质。升级 VIP 可解锁全部格式。"
            ),
        )


def apply_tier_to_parse_result(result: dict, is_vip: bool) -> dict:
    raw_formats = result.get("formats") or []
    max_height = _max_video_height(raw_formats)

    if is_vip:
        formats = raw_formats
        notice = None
        if max_height and max_height <= 480:
            notice = (
                "当前仅解析到 480p 或更低，通常是平台 Cookie 失效或风控导致。"
                "请更新 backend/cookies.txt（YouTube 需登录 Cookie）后重启后端并重试。"
            )
    else:
        formats = filter_formats(raw_formats, False) + _locked_vip_formats(raw_formats)
        notice = None
        if max_height > FREE_MAX_HEIGHT:
            notice = f"免费用户最高可选 {FREE_MAX_HEIGHT}p；1080p 及以上需升级 VIP（列表中带 VIP 标记）。"
        elif max_height and max_height <= 480:
            notice = (
                f"免费用户最高 {FREE_MAX_HEIGHT}p，但当前源仅解析到 {max_height}p。"
                "可尝试更新 backend/cookies.txt 后重试，或升级 VIP 获取更稳定的高清源。"
            )

    return {
        **result,
        "formats": formats,
        "tier": tier_meta(is_vip),
        "quality_notice": notice,
    }
