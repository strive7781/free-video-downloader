# 映鉴（Kinema）

**一句话**：粘贴视频链接 → 解析画质与格式 → **下载到本地**；可选基于字幕/转录文本进行 **AI 总结、思维导图与问答**（需自行配置大模型 API）。

基于 Vue 3、FastAPI、[yt-dlp](https://github.com/yt-dlp/yt-dlp) 的全栈示例项目，可用作个人学习或二次开发起点。

**版本记录**：`v0515` — 前端布局优化：解析结果双栏同屏（约 40:60）、解析成功后自动触发 AI 总结并保留「重新总结」；收紧导航下 Hero 与结果区的纵向间距以便首屏呈现更多核心内容；开发与文档默认后端端口为 **8000**（与 `frontend/vite.config.js` 代理一致）。历史版本：`version0513` — 完成 AI 总结相关能力（字幕提取、流式摘要、思维导图、基于字幕的问答）。

## 功能概览

| 模块 | 说明 |
|------|------|
| 视频解析 | 支持抖音单独链路；其余站点通过 yt-dlp 解析标题、封面、可选格式等 |
| 本地下载 | 选择格式后触发下载，通过 `file_id` 取回文件；下载目录见下文 |
| 缩略图代理 | `/api/thumbnail` 代理封面图，减轻前端跨域与 Referer 限制 |
| AI 总结 | 从视频提取字幕/可用文本 → 调用兼容 OpenAI SDK 的接口生成结构化摘要、大纲、关键词 |
| 流式体验 | SSE：`/api/summarize/stream` 流式输出摘要，并在完成后尝试生成 Markdown 思维导图 |
| 字幕面板 | 展示分段字幕、来源与语言；支持前端导出常见字幕格式（见 `SummaryPanel.vue`） |
| AI 问答 | 基于当前视频字幕上下文，`/api/chat` 流式回答用户提问 |

AI 相关接口需在 `backend/.env` 中配置 `AI_API_KEY`（及可选的 `AI_BASE_URL`、`AI_MODEL`）。请参考仓库内的 [`backend/.env.example`](./backend/.env.example)，**勿将真实 `.env` 或浏览器导出的 `cookies.txt` 提交到 Git**。

部分站点解析或下载需要 Cookie 时，可按后端报错提示将 `cookies.txt` 放在 `backend/` 目录本地使用；该文件已列入 `.gitignore`。

## 技术栈

- **前端**: Vue 3 + Vite + Tailwind CSS 4（axios、marked、markmap 等）
- **后端**: FastAPI + yt-dlp + httpx；AI 调用通过 `openai` 官方 SDK（兼容 DeepSeek、火山方舟等 OpenAI 兼容网关）
- **核心下载/字幕**: [yt-dlp](https://github.com/yt-dlp/yt-dlp)

## 快速开始

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置 AI（可选，仅在使用总结/问答时需要）

```bash
cp .env.example .env
# 编辑 .env，填入 AI_API_KEY；按需修改 AI_BASE_URL、AI_MODEL
```

### 3. 启动后端服务

开发与前端默认代理一致时，建议使用 **8000** 端口（与 `frontend/vite.config.js` 中 `/api` 代理目标一致）：

```bash
cd backend
uvicorn main:app --reload --port 8000
```

若改用其他端口，请同步修改 `frontend/vite.config.js` 里的 `proxy['/api'].target`。

### 4. 安装并启动前端

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器默认：<http://localhost:5173> ，接口通过 Vite 代理到后端 `/api`。

## 项目结构

```
free-video-downloader/
├── backend/
│   ├── main.py                 # FastAPI 入口（解析、下载、总结、聊天、缩略图）
│   ├── downloader.py           # yt-dlp 封装
│   ├── douyin.py               # 抖音链接解析与下载
│   ├── subtitle_extractor.py   # 字幕/文本提取（供总结使用）
│   ├── ai_summarizer.py        # 大模型摘要、流式输出、思维导图与问答
│   ├── requirements.txt
│   ├── .env.example            # 环境变量示例（可复制为 .env）
│   └── downloads/              # 临时下载目录（已被 .gitignore）
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── api/index.js        # API 与 SSE 封装
│   │   └── components/         # 含 SummaryPanel 等
│   ├── vite.config.js
│   └── package.json
├── docs/
│   └── 视频下载功能总结.md
└── README.md
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/parse` | POST | 解析视频信息（标题、封面、可选格式等） |
| `/api/download` | POST | 触发下载，返回 `file_id` 与建议文件名 |
| `/api/download/{file_id}` | GET | 通过 `file_id` 取回已落盘文件（`fn` 查询参数可为展示名） |
| `/api/thumbnail` | GET | 代理缩略图，查询参数 `url` |
| `/api/summarize` | POST | 提取字幕后生成 AI 摘要（JSON：summary / outline / keywords 等） |
| `/api/summarize/stream` | POST | SSE：meta → 流式摘要 chunk → mindmap → done |
| `/api/chat` | POST | SSE：基于字幕上下文 `context` 与 `question` 流式问答 |

## 相关文档

- [视频下载功能实现总结](./docs/视频下载功能总结.md)：双路径架构（抖音 / yt-dlp）、接口约定、`downloader.py` 行为说明与环境依赖。
