import re
import logging
from urllib.parse import urlparse, unquote

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, Response
from pydantic import BaseModel, field_validator

from downloader import parse_video, download_video, start_cleanup_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="映鉴 Kinema API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _validate_url(url: str) -> str:
    url = url.strip()
    if not url:
        raise ValueError("请输入视频链接")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("请输入有效的视频链接 (以 http:// 或 https:// 开头)")
    if not parsed.netloc or "." not in parsed.netloc:
        raise ValueError("请输入有效的网站链接")
    return url


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
        result = parse_video(req.url)
        return {"code": 0, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Parse failed for URL: %s", req.url)
        msg = str(e)
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
        filepath, display_name = download_video(req.url, req.format_id)
        file_id = filepath.stem
        return {"code": 0, "file_id": file_id, "filename": display_name}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Download failed for URL: %s", req.url)
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
