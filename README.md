# 映鉴（Kinema）

**一句话**：粘贴视频链接 → 解析画质与格式 → **下载到本地**；可选基于字幕/转录文本进行 **AI 总结、思维导图与问答**（需自行配置大模型 API）。

基于 Vue 3、FastAPI、[yt-dlp](https://github.com/yt-dlp/yt-dlp) 的全栈示例项目，可用作个人学习或二次开发起点。

**版本记录**

- **`v0523`** — **会员与支付**：SQLite 用户库；JWT 注册/登录；Stripe 一次性买断 VIP（CNY ¥29）；Webhook 开通/退款撤销 VIP；免费用户每日 3 次下载、最高 720p、无 AI 总结；VIP 无限下载、全清晰度、AI 总结/问答/思维导图；解析结果按登录态过滤格式并展示 VIP 锁定项；YouTube 高画质需有效 `cookies.txt`。详见 [`docs/Stripe会员支付配置指南.md`](./docs/Stripe会员支付配置指南.md)。
- **`v0515.1`** — **SEO / GEO**：`index.html` 对齐 [liyupi/free-video-downloader](https://github.com/liyupi/free-video-downloader) 主页的 TDK、Open Graph、Twitter Card、microdata，以及 `FAQPage`、`WebApplication`、`HowTo` 的 JSON-LD；无 JS 场景的 `<noscript>` 长文本与对比表；`public/llms.txt` 供生成式检索；构建时通过 `VITE_SITE_ORIGIN` 注入 canonical 与绝对地址，并在 `dist` 生成 `robots.txt`、`sitemap.xml`（含首页与 `llms.txt`）。页脚与功能区块补充可引用说明与标题层级（`sr-only` H2）。详见下文「SEO / GEO 与上线」。
- **`v0515`** — 优化前端页面，让其变得更加紧凑：解析结果双栏同屏（约 40:60）；解析成功后自动触发 AI 总结并保留「重新总结」；收紧导航与 Hero、Hero 与结果区及卡片内边距，首屏呈现更多核心内容；开发与文档默认后端端口为 **8000**（与 `frontend/vite.config.js` 代理一致）。
- **`version0513`** — 完成 AI 总结相关能力（字幕提取、流式摘要、思维导图、基于字幕的问答）。

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
| 用户注册/登录 | JWT 认证，`/api/auth/register`、`/api/auth/login`、`/api/auth/me` |
| VIP 买断 | Stripe Checkout 一次性支付（CNY），Webhook 开通永久 VIP |
| 下载限流 | 免费用户每日 3 次下载，VIP 无限（需登录） |

### 免费 vs VIP 权益

| 能力 | 免费用户 | VIP 会员 |
|------|----------|----------|
| 每日下载 | 3 次 | 不限 |
| 最高清晰度 | 720p | 1080p / 4K 等全部 |
| 音频单独提取 | 不可用 | 可用 |
| AI 总结 / 问答 / 思维导图 | 不可用 | 可用 |
| 购买方式 | — | Stripe 一次性 ¥29 买断 |

> **YouTube 高画质提示**：若解析结果只有 480p，通常是 YouTube Cookie 失效或风控导致。请在浏览器登录 YouTube 后导出 `cookies.txt` 到 `backend/` 并重启后端。VIP 与免费用户均受此限制。

AI 相关接口需在 `backend/.env` 中配置 `AI_API_KEY`（及可选的 `AI_BASE_URL`、`AI_MODEL`）。会员支付需配置 Stripe 与 `JWT_SECRET`，详见 [`docs/Stripe会员支付配置指南.md`](./docs/Stripe会员支付配置指南.md)。请参考仓库内的 [`backend/.env.example`](./backend/.env.example)，**勿将真实 `.env` 或浏览器导出的 `cookies.txt` 提交到 Git**。

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

### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env：
# - AI_API_KEY（使用 AI 总结/问答时必填）
# - JWT_SECRET（用户登录必填，生产环境请用长随机串）
# - STRIPE_*（会员支付，见 docs/Stripe会员支付配置指南.md）
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

### 5. SEO / GEO 与上线（可选）

1. 复制 [`frontend/.env.example`](./frontend/.env.example) 为 `frontend/.env.production`（或构建时注入环境变量），填写 **`VITE_SITE_ORIGIN`**（正式站点根地址，**无末尾斜杠**，如 `https://example.com`）。未填写时：本地/构建结果中不会包含依赖绝对 URL 的 meta 与部分结构化数据，且不会生成 `robots.txt` / `sitemap.xml`。
2. 在 [`frontend/public`](./frontend/public) 放置分享图 **`og-image.png`**（建议约 1200×630），与 `index.html` 中 OG / `screenshot` 引用一致。
3. 生产环境将静态资源部署到 CDN 或静态主机后，将 `sitemap.xml` 提交至各搜索引擎站长平台；可用 [Google Rich Results Test](https://search.google.com/test/rich-results) 校验 JSON-LD。
4. **`/llms.txt`**：与首页同源下发，便于 AI / 爬虫读取结构化产品说明。

## 项目结构

```
free-video-downloader/
├── backend/
│   ├── main.py                 # FastAPI 入口（解析、下载、总结、聊天、缩略图）
│   ├── downloader.py           # yt-dlp 封装
│   ├── douyin.py               # 抖音链接解析与下载
│   ├── subtitle_extractor.py   # 字幕/文本提取（供总结使用）
│   ├── ai_summarizer.py        # 大模型摘要、流式输出、思维导图与问答
│   ├── database.py             # SQLite 用户/订单/Webhook 幂等
│   ├── auth.py                 # JWT 注册登录
│   ├── billing.py              # Stripe Checkout + Webhook + 退款同步
│   ├── membership.py           # 免费/VIP 格式过滤与下载校验
│   ├── rate_limit.py           # 免费用户下载限流
│   ├── requirements.txt
│   ├── .env.example            # 环境变量示例（可复制为 .env）
│   └── downloads/              # 临时下载目录（已被 .gitignore）
├── frontend/
│   ├── public/
│   │   ├── favicon.svg
│   │   └── llms.txt            # GEO：供生成式检索 / 爬虫读取的站点说明
│   ├── src/
│   │   ├── App.vue
│   │   ├── api/index.js        # API 与 SSE 封装
│   │   ├── composables/useAuth.js  # 登录态与 VIP
│   │   └── components/         # VideoCard、AuthModal、SummaryPanel 等
│   ├── .env.example            # VITE_SITE_ORIGIN 等（不上传真实密钥）
│   ├── index.html              # TDK、OG、JSON-LD、noscript 等
│   ├── vite.config.js          # 构建期 SEO 注入与 robots/sitemap 写出
│   └── package.json
├── docs/
│   ├── 视频下载功能总结.md
│   ├── Stripe会员支付配置指南.md
│   └── 鱼厂 SEO 优化工作流.md  # 鱼厂内部 SEO 规范参考（可选读）
└── README.md
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/parse` | POST | 解析视频信息；登录后按 VIP 状态过滤格式（可选 Bearer Token） |
| `/api/download` | POST | 触发下载（需登录；免费用户限流 + 格式校验） |
| `/api/download/{file_id}` | GET | 通过 `file_id` 取回已落盘文件（`fn` 查询参数可为展示名） |
| `/api/thumbnail` | GET | 代理缩略图，查询参数 `url` |
| `/api/summarize` | POST | 提取字幕后生成 AI 摘要（VIP；JSON：summary / outline / keywords 等） |
| `/api/summarize/stream` | POST | SSE：meta → 流式摘要 chunk → mindmap → done（VIP） |
| `/api/chat` | POST | SSE：基于字幕上下文流式问答（VIP） |
| `/api/auth/register` | POST | 邮箱注册，返回 JWT |
| `/api/auth/login` | POST | 邮箱登录，返回 JWT |
| `/api/auth/me` | GET | 当前用户信息；同步 Stripe 退款状态（需 Bearer Token） |
| `/api/billing/checkout` | POST | 创建 Stripe 一次性买断 Checkout（需登录） |
| `/api/billing/verify` | POST | 支付回跳后查询订单状态（需登录） |
| `/api/stripe/webhook` | POST | Stripe Webhook（验签后开通/撤销 VIP） |

## 相关文档

- [视频下载功能实现总结](./docs/视频下载功能总结.md)：双路径架构（抖音 / yt-dlp）、接口约定、`downloader.py` 行为说明与环境依赖。
- [Stripe 会员支付配置指南](./docs/Stripe会员支付配置指南.md)：Stripe 测试模式、CLI Webhook、CNY 买断 VIP 联调步骤。
- [鱼厂 SEO 优化工作流](./docs/鱼厂%20SEO%20优化工作流.md)：页面 TDK、meta、结构化标签等工作流参考。
