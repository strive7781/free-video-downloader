import ipaddress
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

_backend_dir = Path(__file__).resolve().parent
_env_file = _backend_dir / ".env"
# utf-8-sig strips BOM; override=True so empty shell vars don't mask .env
load_dotenv(dotenv_path=_env_file, encoding="utf-8-sig", override=True)
if not _env_file.is_file():
    load_dotenv(encoding="utf-8-sig", override=True)

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse, Response
from pydantic import BaseModel, field_validator

from auth import (
    create_access_token,
    ensure_auth_config,
    get_current_user,
    get_optional_user,
    hash_password,
    validate_email,
    validate_password,
    verify_password,
)
from billing import (
    FREE_DAILY_DOWNLOAD_LIMIT,
    create_checkout_session,
    handle_webhook,
    verify_checkout_session,
)
from database import (
    count_downloads_today,
    create_user,
    get_user_by_email,
    get_user_password_hash,
    init_db,
    user_has_active_vip,
)
from downloader import (
    parse_user_error_message,
    parse_video,
    download_video,
    start_cleanup_scheduler,
)
from douyin import DouyinParser, is_douyin_url
from membership import apply_tier_to_parse_result, require_vip, validate_download_format
from rate_limit import check_download_quota, record_download
from subtitle_extractor import extract_subtitles
from ai_summarizer import (
    ai_error_message,
    summarize_text,
    summarize_text_stream,
    generate_mindmap,
    chat_stream,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}

_douyin = DouyinParser(download_dir=str(Path(__file__).parent / "downloads"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_auth_config()
    init_db()
    start_cleanup_scheduler()
    yield


app = FastAPI(title="映鉴 Kinema API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    """Return 400 + readable detail so the SPA shows validation errors like other API errors."""
    parts = []
    for err in exc.errors():
        parts.append(str(err.get("msg") or err.get("type") or "参数无效"))
    msg = "; ".join(parts) if parts else "请求参数无效"
    return JSONResponse(status_code=400, content={"detail": msg})


def _normalize_url(url: str) -> str:
    """Fix common URL issues (e.g. bilibili.com -> www.bilibili.com)."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host == "bilibili.com":
        url = url.replace("://bilibili.com", "://www.bilibili.com", 1)
    return url


def _validate_url(url: str) -> str:
    url = url.strip()
    if not url:
        raise ValueError("请输入视频链接")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("请输入有效的视频链接 (以 http:// 或 https:// 开头)")
    if not parsed.netloc:
        raise ValueError("请输入有效的网站链接")
    host = parsed.hostname
    if not host:
        raise ValueError("请输入有效的网站链接")
    hl = host.lower()
    if "." in hl:
        return _normalize_url(url)
    if hl == "localhost":
        return url
    try:
        ipaddress.ip_address(hl)
        return url
    except ValueError:
        pass
    raise ValueError("请输入有效的网站链接（需为完整域名，例如 youtube.com）")


class ParseRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        return _validate_url(v)


class DownloadRequest(BaseModel):
    url: str
    format_id: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        return _validate_url(v)


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class CheckoutVerifyRequest(BaseModel):
    session_id: str


def _user_public(user: dict) -> dict:
    from database import user_has_active_vip

    is_vip = user_has_active_vip(user["id"])
    user = {**user, "is_vip": is_vip}
    used = count_downloads_today(user["id"])
    limit = None if user.get("is_vip") else FREE_DAILY_DOWNLOAD_LIMIT
    remaining = None if user.get("is_vip") else max(0, FREE_DAILY_DOWNLOAD_LIMIT - used)
    return {
        "id": user["id"],
        "email": user["email"],
        "is_vip": user["is_vip"],
        "downloads_today": used,
        "download_limit": limit,
        "downloads_remaining": remaining,
    }


@app.post("/api/auth/register")
async def api_register(req: RegisterRequest):
    try:
        email = validate_email(req.email)
        password = validate_password(req.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if get_user_by_email(email):
        raise HTTPException(status_code=400, detail="该邮箱已注册")
    user = create_user(email, hash_password(password))
    try:
        token = create_access_token(user["id"], user["email"])
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"code": 0, "data": {"token": token, "user": _user_public(user)}}


@app.post("/api/auth/login")
async def api_login(req: LoginRequest):
    try:
        email = validate_email(req.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    stored_hash = get_user_password_hash(email)
    if not stored_hash:
        raise HTTPException(status_code=401, detail="该邮箱尚未注册，请先注册")
    if not verify_password(req.password, stored_hash):
        raise HTTPException(status_code=401, detail="密码错误，请重新输入")
    user = get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=401, detail="账号异常，请重新注册或联系客服")
    try:
        token = create_access_token(user["id"], user["email"])
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"code": 0, "data": {"token": token, "user": _user_public(user)}}


@app.get("/api/auth/me")
async def api_me(user: dict = Depends(get_current_user)):
    return {"code": 0, "data": _user_public(user)}


@app.post("/api/billing/checkout")
async def api_billing_checkout(user: dict = Depends(get_current_user)):
    if user_has_active_vip(user["id"]):
        raise HTTPException(status_code=400, detail="您已是 VIP 会员")
    try:
        result = create_checkout_session(user)
        return {"code": 0, "data": result}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Create checkout session failed")
        raise HTTPException(status_code=400, detail=f"创建支付会话失败: {str(e)[:200]}")


@app.post("/api/billing/verify")
async def api_billing_verify(req: CheckoutVerifyRequest, user: dict = Depends(get_current_user)):
    try:
        session = verify_checkout_session(req.session_id, user["id"])
        refreshed = get_user_by_email(user["email"])
        return {
            "code": 0,
            "data": {
                "session": session,
                "user": _user_public(refreshed or user),
            },
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Verify checkout session failed")
        raise HTTPException(status_code=400, detail=f"查询订单失败: {str(e)[:200]}")


@app.post("/api/stripe/webhook")
async def api_stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        result = handle_webhook(payload, sig_header)
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Stripe webhook failed")
        raise HTTPException(status_code=400, detail="Webhook 处理失败")


@app.post("/api/parse")
async def api_parse(
    req: ParseRequest,
    user: dict | None = Depends(get_optional_user),
):
    is_vip = bool(user and user_has_active_vip(user["id"])) if user else False
    try:
        if is_douyin_url(req.url):
            result = _douyin.parse(req.url)
        else:
            result = parse_video(req.url)
        result = apply_tier_to_parse_result(result, is_vip)
        return {"code": 0, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        detail = parse_user_error_message(e, req.url)
        logger.warning("Parse failed for URL: %s — %s", req.url, detail.replace("\n", " "))
        raise HTTPException(status_code=400, detail=detail)


@app.post("/api/download")
async def api_download(req: DownloadRequest, user: dict = Depends(get_current_user)):
    """Trigger download and return a file_id for the GET endpoint."""
    check_download_quota(user)
    try:
        if is_douyin_url(req.url):
            parsed = _douyin.parse(req.url)
            validate_download_format(user, parsed.get("formats") or [], req.format_id)
            result = _douyin.download(req.url)
            if result is None:
                raise RuntimeError("抖音下载器未返回结果")
            filepath, display_name = result
            file_id = Path(filepath).stem
        else:
            parsed = parse_video(req.url)
            validate_download_format(user, parsed.get("formats") or [], req.format_id)
            result = download_video(req.url, req.format_id)
            if result is None:
                raise RuntimeError("下载器未返回结果，请重试")
            filepath, display_name = result
            file_id = filepath.stem
        record_download(user)
        refreshed = get_user_by_email(user["email"])
        return {
            "code": 0,
            "file_id": file_id,
            "filename": display_name,
            "user": _user_public(refreshed or user),
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error("Download failed for URL: %s\n%s", req.url, traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"下载失败: {str(e)[:200]}")


@app.get("/api/download/{file_id}")
async def api_download_file(file_id: str, fn: str = Query(default="")):
    """Serve the downloaded file directly via browser native download."""
    from downloader import DOWNLOAD_DIR
    for f in DOWNLOAD_DIR.iterdir():
        if f.stem == file_id and f.is_file():
            display_name = fn if fn else f.name
            return FileResponse(
                path=str(f),
                filename=display_name,
                media_type="video/mp4",
            )
    raise HTTPException(status_code=404, detail="文件不存在或已过期")


class SummarizeRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        return _validate_url(v)


@app.post("/api/summarize")
async def api_summarize(req: SummarizeRequest, user: dict = Depends(get_current_user)):
    """Extract subtitles and generate AI summary for a video."""
    require_vip(user, "AI 视频总结")
    try:
        subtitle_data = extract_subtitles(req.url)
        full_text = subtitle_data.get("full_text", "")
        if not full_text:
            raise HTTPException(status_code=400, detail="无法提取视频文本内容")

        title = ""
        try:
            if is_douyin_url(req.url):
                info = _douyin.parse(req.url)
            else:
                info = parse_video(req.url)
            title = info.get("title", "")
        except Exception:
            pass

        ai_result = summarize_text(full_text, video_title=title)

        return {
            "code": 0,
            "data": {
                "summary": ai_result.get("summary", ""),
                "outline": ai_result.get("outline", []),
                "keywords": ai_result.get("keywords", []),
                "subtitles": subtitle_data.get("subtitles", []),
                "full_text": full_text,
                "language": subtitle_data.get("language", ""),
                "source": subtitle_data.get("source", ""),
            },
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Summarize failed for URL: %s", req.url)
        raise HTTPException(status_code=400, detail=ai_error_message(e))


@app.post("/api/summarize/stream")
async def api_summarize_stream(req: SummarizeRequest, user: dict = Depends(get_current_user)):
    """SSE endpoint: extract subtitles then stream AI summary."""
    require_vip(user, "AI 视频总结")
    try:
        subtitle_data = extract_subtitles(req.url)
        full_text = subtitle_data.get("full_text", "")
        if not full_text:
            raise HTTPException(status_code=400, detail="无法提取视频文本内容")

        title = ""
        try:
            if is_douyin_url(req.url):
                info = _douyin.parse(req.url)
            else:
                info = parse_video(req.url)
            title = info.get("title", "")
        except Exception:
            pass

        import json as _json

        meta = {
            "subtitles": subtitle_data.get("subtitles", []),
            "source": subtitle_data.get("source", ""),
            "language": subtitle_data.get("language", ""),
            "full_text": full_text,
        }

        def generate():
            yield f"event: meta\ndata: {_json.dumps(meta, ensure_ascii=False)}\n\n"
            try:
                for text_chunk in summarize_text_stream(full_text, video_title=title):
                    yield f"event: chunk\ndata: {_json.dumps({'text': text_chunk}, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.exception("Stream summarize failed")
                yield f"event: error\ndata: {_json.dumps({'detail': ai_error_message(e)}, ensure_ascii=False)}\n\n"

            try:
                mindmap_md = generate_mindmap(full_text, video_title=title)
                yield f"event: mindmap\ndata: {_json.dumps({'markdown': mindmap_md}, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.warning("Mindmap generation failed: %s", e)

            yield "event: done\ndata: {}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream", headers=_SSE_HEADERS)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Summarize stream failed for URL: %s", req.url)
        raise HTTPException(status_code=400, detail=ai_error_message(e))


class ChatRequest(BaseModel):
    url: str
    question: str
    context: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        return _validate_url(v)


@app.post("/api/chat")
async def api_chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    """SSE endpoint: AI Q&A based on video subtitles."""
    require_vip(user, "AI 视频问答")
    if not req.context.strip():
        raise HTTPException(status_code=400, detail="缺少视频上下文")
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="请输入问题")

    import json as _json

    def generate():
        try:
            for text_chunk in chat_stream(req.context, req.question):
                yield f"event: chunk\ndata: {_json.dumps({'text': text_chunk}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.exception("Chat stream failed")
            yield f"event: error\ndata: {_json.dumps({'detail': str(e)[:200]}, ensure_ascii=False)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream", headers=_SSE_HEADERS)


@app.get("/api/thumbnail")
async def api_thumbnail(url: str = Query(...)):
    """Proxy thumbnail images to avoid referrer/CORS restrictions."""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            resp = await client.get(url, headers={"Referer": url})
            content_type = resp.headers.get("content-type", "image/jpeg")
            return Response(
                content=resp.content,
                media_type=content_type,
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception:
        raise HTTPException(status_code=404, detail="无法加载缩略图")


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
