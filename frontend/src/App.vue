<template>
  <div class="relative min-h-screen flex flex-col bg-gradient-to-b from-[#eaf4ff] via-[#f5faff] to-white">
    <p
      class="pointer-events-none fixed bottom-6 right-6 z-[30] hidden sm:block text-[11px] text-slate-300 select-none tracking-wide"
      aria-hidden="true"
    >
      编程导航 <span class="text-slate-200">·</span> codefather.cn
    </p>

    <NavBar @login="openAuth('login')" @upgrade="handleUpgrade" />
    <AuthModal
      :visible="authVisible"
      :initial-mode="authMode"
      :hint="authHint"
      @close="authVisible = false"
      @success="onAuthSuccess"
    />

    <div
      v-if="toast.message"
      class="fixed top-20 left-1/2 -translate-x-1/2 z-[90] max-w-md w-[calc(100%-2rem)] px-4 py-3 rounded-xl shadow-lg text-sm font-medium"
      :class="toast.type === 'error' ? 'bg-red-50 text-red-700 border border-red-100' : 'bg-green-50 text-green-700 border border-green-100'"
    >
      {{ toast.message }}
    </div>

    <main class="flex-1 relative z-10">
      <HeroSection @parse="handleParse" :loading="parsing" :error="parseError" />
      <section
        v-if="videoInfo"
        class="animate-fadeInUp pb-5 sm:pb-7 pt-0 px-4 sm:px-6 lg:px-8 bg-slate-200/35 border-t border-slate-300/25"
      >
        <div class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)] gap-4 lg:gap-6 items-start">
          <div class="min-w-0">
            <VideoCard
              embedded
              :video="videoInfo"
              :downloading="downloading"
              :summarizing="summarizing"
              :download-progress="downloadProgress"
              :summarize-regenerate="summaryCompleted"
              :is-vip="isVip"
              :downloads-remaining="downloadsRemaining"
              :download-limit="downloadLimit"
              @download="handleDownload"
              @summarize="handleSummarize"
              @upgrade="handleUpgrade"
            />
          </div>
          <div class="min-w-0 h-full lg:sticky lg:top-16 lg:self-start lg:max-h-[calc(100vh-4.5rem)] lg:flex lg:flex-col">
            <SummaryPanel
              v-if="summaryData || (!isVip && videoInfo)"
              embedded
              class="lg:flex-1 lg:min-h-0"
              :data="summaryData"
              :streaming-text="streamingText"
              :mindmap-markdown="mindmapMarkdown"
              :current-url="currentUrl"
              :error-message="summaryError"
              :is-vip="isVip"
              @upgrade="handleUpgrade"
            />
          </div>
        </div>
      </section>
      <FeatureSection />
      <PlatformGrid />
      <PricingSection
        :checkout-loading="checkoutLoading"
        :checkout-error="checkoutError"
        @upgrade="handleUpgrade"
      />
    </main>
    <FooterSection />
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import NavBar from './components/NavBar.vue'
import AuthModal from './components/AuthModal.vue'
import HeroSection from './components/HeroSection.vue'
import VideoCard from './components/VideoCard.vue'
import SummaryPanel from './components/SummaryPanel.vue'
import FeatureSection from './components/FeatureSection.vue'
import PlatformGrid from './components/PlatformGrid.vue'
import PricingSection from './components/PricingSection.vue'
import FooterSection from './components/FooterSection.vue'
import {
  apiErrorMessage,
  createCheckout,
  fetchMe,
  parseVideo,
  triggerDownload,
  verifyCheckout,
  streamSummarize,
} from './api/index.js'
import { useAuth } from './composables/useAuth.js'

const { isLoggedIn, isVip, setUser, getToken, downloadsRemaining, downloadLimit } = useAuth()

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
const summaryError = ref('')
const summaryCompleted = ref(false)

const authVisible = ref(false)
const authMode = ref('login')
const authHint = ref('')
const pendingAction = ref(null)

const checkoutLoading = ref(false)
const checkoutError = ref('')

const toast = ref({ message: '', type: 'success' })
let toastTimer = null

function showToast(message, type = 'success') {
  toast.value = { message, type }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toast.value = { message: '', type: 'success' }
  }, 5000)
}

function openAuth(mode = 'login', hint = '', after = null) {
  authMode.value = mode
  authHint.value = hint
  pendingAction.value = after
  authVisible.value = true
}

function onAuthSuccess() {
  if (typeof pendingAction.value === 'function') {
    const fn = pendingAction.value
    pendingAction.value = null
    fn()
  }
}

async function refreshUser() {
  if (!getToken()) return
  try {
    const res = await fetchMe()
    if (res.code === 0 && res.data) setUser(res.data)
  } catch {
    /* token expired — ignore until next protected action */
  }
}

async function handleUpgrade() {
  checkoutError.value = ''
  if (!isLoggedIn.value) {
    openAuth('register', '注册并登录后即可购买 VIP', () => handleUpgrade())
    return
  }
  if (isVip.value) {
    showToast('您已是 VIP 会员')
    return
  }
  checkoutLoading.value = true
  try {
    const res = await createCheckout()
    if (res.code === 0 && res.data?.checkout_url) {
      window.location.href = res.data.checkout_url
    } else {
      checkoutError.value = res.detail || '创建支付失败'
    }
  } catch (e) {
    checkoutError.value = apiErrorMessage(e)
  } finally {
    checkoutLoading.value = false
  }
}

async function handleCheckoutReturn() {
  const params = new URLSearchParams(window.location.search)
  const checkout = params.get('checkout')
  const sessionId = params.get('session_id')
  if (!checkout) return

  window.history.replaceState({}, '', window.location.pathname)

  if (checkout === 'cancel') {
    showToast('已取消支付', 'error')
    return
  }
  if (checkout !== 'success' || !sessionId) return

  if (!getToken()) {
    openAuth('login', '请登录以确认您的 VIP 订单')
    return
  }

  showToast('支付成功，正在确认订单…')
  try {
    const res = await verifyCheckout(sessionId)
    if (res.code === 0 && res.data?.user) {
      setUser(res.data.user)
      if (res.data.user.is_vip) {
        showToast('🎉 VIP 已开通，感谢支持！')
      } else if (res.data.session?.payment_status === 'paid') {
        showToast('支付已成功，正在同步 VIP 状态…')
        await refreshUser()
        if (isVip.value) {
          showToast('🎉 VIP 已开通，感谢支持！')
        }
      } else {
        showToast('支付处理中，请稍后刷新页面', 'error')
      }
    }
  } catch (e) {
    showToast(apiErrorMessage(e), 'error')
  }
}

onMounted(async () => {
  await refreshUser()
  await handleCheckoutReturn()
})

watch(isVip, async (vip, prev) => {
  if (prev !== undefined && vip !== prev && currentUrl.value) {
    await handleParse(currentUrl.value)
  }
})

async function handleParse(url) {
  parsing.value = true
  parseError.value = ''
  videoInfo.value = null
  summaryData.value = null
  summaryError.value = ''
  summaryCompleted.value = false
  streamingText.value = ''
  mindmapMarkdown.value = ''
  currentUrl.value = url

  try {
    const res = await parseVideo(url)
    if (res.code === 0) {
      videoInfo.value = res.data
      summaryData.value = null
      summaryError.value = ''
      if (isVip.value) {
        handleSummarize()
      }
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
  if (!isVip.value) {
    handleUpgrade()
    return
  }
  summarizing.value = true
  summaryError.value = ''
  summaryCompleted.value = false
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
        summaryError.value = err.message || 'AI 总结失败'
        summaryCompleted.value = false
      } else {
        summaryCompleted.value = true
      }
    },
  })
}

async function doDownload(formatId) {
  downloading.value = true
  downloadProgress.value = '正在处理：下载完成后若为 AV1/HEVC，会自动转 H.264，长视频请耐心等待…'

  try {
    const res = await triggerDownload(currentUrl.value, formatId)
    if (res.code === 0 && res.file_id) {
      if (res.user) setUser(res.user)
      downloadProgress.value = '处理完成，正在开始下载...'
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

function handleDownload(formatId) {
  if (!isLoggedIn.value) {
    openAuth('login', '登录后即可下载视频（免费用户每日 3 次）', () => doDownload(formatId))
    return
  }
  doDownload(formatId)
}
</script>
