import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Ensure .env is loaded even if this module is imported before main runs load_dotenv
_backend_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=_backend_dir / ".env", encoding="utf-8-sig", override=True)

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://api.deepseek.com"
_DEFAULT_MODEL = "deepseek-chat"
_MAX_TEXT_LENGTH = 15000
_PLACEHOLDER_KEYS = frozenset({"", "sk-xxx", "your-ark-api-key", "your-endpoint-model-id"})


def ai_error_message(exc: Exception) -> str:
    """Map OpenAI SDK / config errors to user-facing Chinese messages."""
    name = type(exc).__name__
    msg = str(exc)
    if isinstance(exc, ValueError):
        return str(exc)
    if "AuthenticationError" in name or "401" in msg or "Unauthorized" in msg:
        return (
            "AI 接口鉴权失败：请检查 backend/.env 中的 AI_API_KEY 是否正确。"
            "若使用火山方舟，需填入控制台生成的 API Key，并确认 AI_MODEL 为接入点 ID。"
        )
    if "NotFoundError" in name or "404" in msg:
        return (
            "AI 模型不存在：请检查 backend/.env 中的 AI_MODEL 是否为有效的接入点/模型 ID。"
        )
    if "RateLimitError" in name or "429" in msg:
        return "AI 接口请求过于频繁，请稍后再试。"
    if "Connection" in name or "timeout" in msg.lower():
        return "无法连接 AI 服务，请检查网络或 AI_BASE_URL 配置。"
    return f"AI 总结失败: {msg[:200]}"


def _get_client() -> OpenAI:
    api_key = (os.environ.get("AI_API_KEY") or "").strip()
    base_url = (os.environ.get("AI_BASE_URL") or _DEFAULT_BASE_URL).strip()
    if not api_key or api_key in _PLACEHOLDER_KEYS or api_key.startswith("your-"):
        raise ValueError(
            "未配置有效的 AI_API_KEY。请编辑 backend/.env，填入真实的大模型 API Key。"
            "（火山方舟：控制台 → API Key 管理；DeepSeek：platform.deepseek.com）"
        )
    return OpenAI(api_key=api_key, base_url=base_url)


def _get_model() -> str:
    model = (os.environ.get("AI_MODEL") or _DEFAULT_MODEL).strip()
    if model in _PLACEHOLDER_KEYS or model.startswith("your-"):
        raise ValueError(
            "未配置有效的 AI_MODEL。请编辑 backend/.env，填入模型或接入点 ID。"
            "（火山方舟示例：ep-xxxxxxxx-xxxxx）"
        )
    return model


def _truncate_text(text: str, max_length: int = _MAX_TEXT_LENGTH) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "\n...(内容已截断)"


_SYSTEM_PROMPT = """你是一位专业的视频内容分析助手。用户会给你一段视频的字幕/转录文本，请你对内容进行结构化总结。

请严格按照以下 JSON 格式输出（不要输出其他内容）：

{
  "summary": "用 2-3 句话概括视频的核心内容",
  "outline": [
    {
      "title": "章节/段落标题",
      "points": ["要点1", "要点2", "要点3"]
    }
  ],
  "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"]
}

要求：
1. summary 简洁精炼，让读者快速了解视频主题
2. outline 按视频内容的逻辑结构分 3-7 个章节，每个章节提炼 2-4 个核心要点
3. keywords 提取 5-8 个最能代表视频内容的关键词
4. 使用中文输出（除非原文为纯英文内容）
5. 只输出 JSON，不要有任何额外文字"""


def summarize_text(text: str, video_title: str = "") -> dict:
    """
    Send text to AI model and get structured summary.

    Returns:
        {
            "summary": "一段话总结",
            "outline": [{"title": "章节1", "points": ["要点1","要点2"]},...],
            "keywords": ["关键词1", "关键词2", ...]
        }
    """
    client = _get_client()
    model = _get_model()

    truncated = _truncate_text(text)
    user_content = f"视频标题：{video_title}\n\n字幕内容：\n{truncated}" if video_title else truncated

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        content = response.choices[0].message.content.strip()
        content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(content)

        if "summary" not in result or "outline" not in result:
            raise ValueError("AI 返回格式不正确")

        return {
            "summary": result.get("summary", ""),
            "outline": result.get("outline", []),
            "keywords": result.get("keywords", []),
        }
    except json.JSONDecodeError as e:
        logger.error("AI response JSON parse failed: %s", e)
        raise ValueError("AI 返回内容解析失败，请重试") from e
    except Exception as e:
        logger.exception("AI summarization failed")
        raise ValueError(f"AI 总结失败: {str(e)[:200]}") from e


_STREAM_SYSTEM_PROMPT = """你是一位专业的视频内容分析助手。用户会给你一段视频的字幕/转录文本，请你对内容进行详细的分析总结。

请按以下结构输出（使用 Markdown 格式）：

## 视频概述
用 2-3 句话概括视频的核心内容。

## 内容大纲
按视频内容的逻辑结构分章节，每个章节提炼核心要点。

## 关键词
列出 5-8 个最能代表视频内容的关键词。

要求：
1. 概述简洁精炼，让读者快速了解视频主题
2. 大纲按逻辑分 3-7 个章节
3. 使用中文输出（除非原文为纯英文内容）"""


def summarize_text_stream(text: str, video_title: str = ""):
    """Generator that yields text chunks from the AI model via streaming."""
    client = _get_client()
    model = _get_model()

    truncated = _truncate_text(text)
    user_content = f"视频标题：{video_title}\n\n字幕内容：\n{truncated}" if video_title else truncated

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _STREAM_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
        max_tokens=2000,
        stream=True,
    )
    for chunk in response:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


_MINDMAP_SYSTEM_PROMPT = """你是一个专业的思维导图生成助手，擅长将内容组织为清晰的层级结构。"""

_MINDMAP_USER_TEMPLATE = """请将以下视频字幕内容整理为思维导图结构，使用中文输出。

要求：
1. 使用 Markdown 标题层级格式（# 一级标题，## 二级标题，### 三级标题）
2. 最外层是视频主题
3. 第二层是主要章节/模块（3-7个）
4. 第三层是各章节的要点
5. 每个节点的文字要简洁精炼
6. 只输出 Markdown 内容，不要其他说明文字

---
视频字幕内容：
{text}"""


def generate_mindmap(text: str, video_title: str = "") -> str:
    """Generate a mindmap Markdown structure from video text (non-streaming)."""
    client = _get_client()
    model = _get_model()

    truncated = _truncate_text(text)
    user_content = _MINDMAP_USER_TEMPLATE.format(text=truncated)
    if video_title:
        user_content = f"视频标题：{video_title}\n\n" + user_content

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _MINDMAP_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.5,
        max_tokens=3000,
    )
    content = response.choices[0].message.content or ""
    return content.removeprefix("```markdown").removeprefix("```").removesuffix("```").strip()


_CHAT_SYSTEM_PROMPT = """你是一个视频内容问答助手。用户会基于一段视频的字幕内容向你提问，请根据字幕内容准确回答。

要求：
1. 回答要准确、简洁，基于视频内容
2. 如果视频内容中没有相关信息，请如实告知
3. 使用中文回答（除非用户用英文提问）
4. 可以适当推理和总结，但不要编造视频中没有的内容"""


def chat_stream(context: str, question: str):
    """Generator that yields text chunks for a Q&A response based on video context."""
    client = _get_client()
    model = _get_model()

    truncated = _truncate_text(context)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": f"以下是视频的字幕内容：\n\n{truncated}\n\n用户问题：{question}"},
        ],
        temperature=0.4,
        max_tokens=1500,
        stream=True,
    )
    for chunk in response:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
