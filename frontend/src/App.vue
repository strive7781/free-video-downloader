<template>
  <div class="min-h-screen flex flex-col bg-[#f8fafc]">
    <NavBar />
    <main class="flex-1">
      <HeroSection
        @parse="handleParse"
        :loading="parsing"
        :error="parseError"
      />
      <VideoCard
        v-if="videoInfo"
        :video="videoInfo"
        :downloading="downloading"
        :download-progress="downloadProgress"
        @download="handleDownload"
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
import FeatureSection from './components/FeatureSection.vue'
import PlatformGrid from './components/PlatformGrid.vue'
import PricingSection from './components/PricingSection.vue'
import FooterSection from './components/FooterSection.vue'
import { parseVideo, triggerDownload } from './api/index.js'

const parsing = ref(false)
const parseError = ref('')
const videoInfo = ref(null)
const downloading = ref(false)
const downloadProgress = ref('')
const currentUrl = ref('')

async function handleParse(url) {
  parsing.value = true
  parseError.value = ''
  videoInfo.value = null
  currentUrl.value = url

  try {
    const res = await parseVideo(url)
    if (res.code === 0) {
      videoInfo.value = res.data
    } else {
      parseError.value = res.detail || '解析失败，请检查链接是否正确'
    }
  } catch (e) {
    parseError.value = e.response?.data?.detail || '解析失败，请检查链接是否有效'
  } finally {
    parsing.value = false
  }
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
    const msg = e.response?.data?.detail || e.message
    downloadProgress.value = '下载失败: ' + msg
  } finally {
    downloading.value = false
  }
}
</script>
