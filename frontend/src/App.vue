<template>
  <div class="relative min-h-screen flex flex-col bg-gradient-to-b from-[#eaf4ff] via-[#f5faff] to-white">
    <p
      class="pointer-events-none fixed bottom-6 right-6 z-[30] hidden sm:block text-[11px] text-slate-300 select-none tracking-wide"
      aria-hidden="true"
    >
      编程导航 <span class="text-slate-200">·</span> codefather.cn
    </p>
    <NavBar />
    <main class="flex-1 relative z-10">
      <HeroSection
        @parse="handleParse"
        :loading="parsing"
        :error="parseError"
      />
      <VideoCard
        v-if="videoInfo"
        :video="videoInfo"
        :downloading="downloading"
        :summarizing="summarizing"
        :download-progress="downloadProgress"
        @download="handleDownload"
        @summarize="handleSummarize"
      />
      <SummaryPanel
        v-if="summaryData"
        :data="summaryData"
        :streaming-text="streamingText"
        :mindmap-markdown="mindmapMarkdown"
        :current-url="currentUrl"
      />
      <FeatureSection />
      <PlatformGrid />
      <PricingSection />
    </main>
    <FooterSection />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import NavBar from './components/NavBar.vue'
import HeroSection from './components/HeroSection.vue'
import VideoCard from './components/VideoCard.vue'
import SummaryPanel from './components/SummaryPanel.vue'
import FeatureSection from './components/FeatureSection.vue'
import PlatformGrid from './components/PlatformGrid.vue'
import PricingSection from './components/PricingSection.vue'
import FooterSection from './components/FooterSection.vue'
import { parseVideo, triggerDownload, streamSummarize } from './api/index.js'

function formatApiDetail(detail) {
  if (detail == null || detail === '') return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((x) =>
        typeof x === 'object' && x != null
          ? (x.msg || x.message || JSON.stringify(x))
          : String(x),
      )
      .filter(Boolean)
      .join('; ')
  }
  return String(detail)
}

function apiErrorMessage(e) {
  return formatApiDetail(e.response?.data?.detail) || e.message || '请求失败'
}

const parsing = ref(false)
const parseError = ref('')
const videoInfo = ref(null)
const downloading = ref(false)
const downloadProgress = ref('')
const currentUrl = ref('')
const summarizing = ref(false)
const summaryData = ref(null)
const streamingText = ref('')
const mindmapMarkdown = ref('')

async function handleParse(url) {
  parsing.value = true
  parseError.value = ''
  videoInfo.value = null
  summaryData.value = null
  currentUrl.value = url

  try {
    const res = await parseVideo(url)
    if (res.code === 0) {
      videoInfo.value = res.data
    } else {
      parseError.value = res.detail || '解析失败，请检查链接是否正确'
    }
  } catch (e) {
    parseError.value = apiErrorMessage(e) || '解析失败，请检查链接是否有效'
  } finally {
    parsing.value = false
  }
}

function handleSummarize() {
  summarizing.value = true
  summaryData.value = null
  streamingText.value = ''
  mindmapMarkdown.value = ''

  summaryData.value = {
    summary: '',
    outline: [],
    keywords: [],
    subtitles: [],
    full_text: '',
    language: '',
    source: '',
  }

  streamSummarize(currentUrl.value, {
    onMeta(meta) {
      summaryData.value.subtitles = meta.subtitles || []
      summaryData.value.source = meta.source || ''
      summaryData.value.language = meta.language || ''
      summaryData.value.full_text = meta.full_text || ''
    },
    onChunk(text) {
      streamingText.value += text
    },
    onMindmap(markdown) {
      mindmapMarkdown.value = markdown
    },
    onDone(err) {
      summarizing.value = false
      if (err) {
        downloadProgress.value = err.message || 'AI 总结失败'
      }
    },
  })
}

async function handleDownload(formatId) {
  downloading.value = true
  downloadProgress.value = '正在处理：下载完成后若为 AV1/HEVC，会自动转 H.264，长视频请耐心等待…'

  try {
    const res = await triggerDownload(currentUrl.value, formatId)
    if (res.code === 0 && res.file_id) {
      downloadProgress.value = '处理完成，正在开始下载...'
      // Use browser native download via direct URL
      const fname = res.filename || 'video.mp4'
      const link = document.createElement('a')
      link.href = '/api/download/' + encodeURIComponent(res.file_id) + '?fn=' + encodeURIComponent(fname)
      link.download = fname
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      downloadProgress.value = '下载已开始!'
    } else {
      downloadProgress.value = '下载失败: ' + (res.detail || '未知错误')
    }
  } catch (e) {
    downloadProgress.value = '下载失败: ' + apiErrorMessage(e)
  } finally {
    downloading.value = false
  }
}
</script>
