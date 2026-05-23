"""Email + password authentication with JWT."""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from database import get_user_by_id, user_has_active_vip

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer = HTTPBearer(auto_error=False)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# 仅本地开发兜底；生产环境必须在 backend/.env 中设置 JWT_SECRET
_DEV_JWT_SECRET = "kinema-dev-jwt-secret-do-not-use-in-production"


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "").strip()
    if secret:
        return secret
    if os.getenv("APP_ENV", "development").lower() == "production":
        raise RuntimeError("JWT_SECRET is not configured")
    return _DEV_JWT_SECRET


def ensure_auth_config() -> None:
    """Startup check: warn when JWT_SECRET is missing in non-production."""
    secret = os.getenv("JWT_SECRET", "").strip()
    if secret:
        return
    if os.getenv("APP_ENV", "development").lower() == "production":
        raise RuntimeError("JWT_SECRET is required when APP_ENV=production")
    logger.warning(
        "JWT_SECRET 未配置，正在使用本地开发默认密钥。"
        "请复制 backend/.env.example 为 backend/.env 并设置 JWT_SECRET。"
    )


def _jwt_expire_minutes() -> int:
    return int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))  # default 7 days


def validate_email(email: str) -> str:
    email = email.strip().lower()
    if not email or not EMAIL_RE.match(email):
        raise ValueError("请输入有效的邮箱地址")
    return email


def validate_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("密码至少 8 位")
    if len(password) > 128:
        raise ValueError("密码过长")
    return password


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=_jwt_expire_minutes())
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已过期，请重新登录",
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
        )
    payload = decode_token(credentials.credentials)
    user_id = int(payload.get("sub", "0"))
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已失效",
        )
    user["is_vip"] = user_has_active_vip(user_id)
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any] | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload.get("sub", "0"))
        return get_user_by_id(user_id)
    except HTTPException:
        return None
