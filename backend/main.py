import ipaddress
import logging
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
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse, Response
from pydantic import BaseModel, field_validator

from downloader import parse_video, download_video, start_cleanup_scheduler
from douyin import DouyinParser, is_douyin_url
from subtitle_extractor import extract_subtitles
from ai_summarizer import summarize_text, summarize_text_stream, generate_mindmap, chat_stream

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}

_douyin = DouyinParser(download_dir=str(Path(__file__).parent / "downloads"))

app = FastAPI(title="映鉴 Kinema API")

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


@app.on_event("startup")
def on_startup():
    start_cleanup_scheduler()


@app.post("/api/parse")
async def api_parse(req: ParseRequest):
    try:
        if is_douyin_url(req.url):
            result = _douyin.parse(req.url)
        else:
            result = parse_video(req.url)
        return {"code": 0, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Parse failed for URL: %s", req.url)
        msg = str(e)
        if "Sign in to confirm" in msg or "cookies" in msg.lower() or "cookie" in msg.lower():
            raise HTTPException(
                status_code=400,
                detail=(
                    "该平台需要浏览器 Cookie 才能解析。请按以下步骤操作：\n"
                    "1. 关闭 Edge/Chrome 浏览器\n"
                    "2. 重启后端服务后重试\n"
                    "或者：用浏览器扩展导出 cookies.txt 放到 backend/ 目录下（推荐）"
                ),
            )
        if "Unsupported URL" in msg:
            raise HTTPException(status_code=400, detail="不支持该链接，请确认是否为有效的视频地址")
        if "Video unavailable" in msg or "not available" in msg.lower():
            raise HTTPException(status_code=400, detail="该视频不可用，可能已被删除或设为私密")
        if "Private video" in msg:
            raise HTTPException(status_code=400, detail="该视频为私密视频，无法下载")
        raise HTTPException(status_code=400, detail=f"解析失败: {msg[:200]}")


@app.post("/api/download")
async def api_download(req: DownloadRequest):
    """Trigger download and return a file_id for the GET endpoint."""
    try:
        if is_douyin_url(req.url):
            result = _douyin.download(req.url)
            if result is None:
                raise RuntimeError("抖音下载器未返回结果")
            filepath, display_name = result
            file_id = Path(filepath).stem
        else:
            result = download_video(req.url, req.format_id)
            if result is None:
                raise RuntimeError("下载器未返回结果，请重试")
            filepath, display_name = result
            file_id = filepath.stem
        return {"code": 0, "file_id": file_id, "filename": display_name}
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
async def api_summarize(req: SummarizeRequest):
    """Extract subtitles and generate AI summary for a video."""
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
        raise HTTPException(status_code=400, detail=f"总结失败: {str(e)[:200]}")


@app.post("/api/summarize/stream")
async def api_summarize_stream(req: SummarizeRequest):
    """SSE endpoint: extract subtitles then stream AI summary."""
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
                yield f"event: error\ndata: {_json.dumps({'detail': str(e)[:200]}, ensure_ascii=False)}\n\n"

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
        raise HTTPException(status_code=400, detail=f"总结失败: {str(e)[:200]}")


class ChatRequest(BaseModel):
    url: str
    question: str
    context: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        return _validate_url(v)


@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    """SSE endpoint: AI Q&A based on video subtitles."""
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
