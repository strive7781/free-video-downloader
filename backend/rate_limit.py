"""Download rate limiting for free vs VIP users."""

from __future__ import annotations

from fastapi import HTTPException

from billing import FREE_DAILY_DOWNLOAD_LIMIT
from database import count_downloads_today, log_download


def check_download_quota(user: dict) -> None:
    if user.get("is_vip"):
        return
    used = count_downloads_today(user["id"])
    if used >= FREE_DAILY_DOWNLOAD_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=(
                f"免费用户每日最多下载 {FREE_DAILY_DOWNLOAD_LIMIT} 次，"
                f"今日已用 {used} 次。升级 VIP 可无限下载。"
            ),
        )


def record_download(user: dict) -> None:
    log_download(user["id"])
