# 映鉴（Kinema）

**一句话**：粘贴视频链接 → 解析画质与格式 → 将在线视频**下载保存到本地**（后端基于 yt-dlp，覆盖 YouTube、Bilibili、TikTok 等主流站点）。

基于 Vue 3、FastAPI 与 yt-dlp 的全栈示例项目，可用作个人学习或二次开发起点。

## 技术栈

- **前端**: Vue 3 + Vite + Tailwind CSS 4
- **后端**: FastAPI + yt-dlp
- **核心能力**: [yt-dlp](https://github.com/yt-dlp/yt-dlp)

## 快速开始

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
```

### 4. 启动前端开发服务器

```bash
cd frontend
npm run dev
```

前端默认运行在 http://localhost:5173 ，后端 API 运行在 http://localhost:8000 。

## 项目结构

```
free-video-downloader/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── downloader.py         # yt-dlp 封装
│   ├── requirements.txt      # Python 依赖
│   └── downloads/            # 临时下载目录
├── frontend/
│   ├── src/
│   │   ├── App.vue           # 主组件
│   │   ├── api/index.js      # API 请求封装
│   │   └── components/       # Vue 组件
│   ├── vite.config.js
│   └── package.json
└── README.md
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/parse` | POST | 解析视频信息 (标题、封面、可选格式) |
| `/api/download` | POST | 下载视频文件 |
