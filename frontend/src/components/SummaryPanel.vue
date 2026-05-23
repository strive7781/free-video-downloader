<template>
  <section
    class="animate-fadeInUp"
    :class="embedded ? 'pb-0 px-0 h-full min-h-0 flex flex-col' : 'pb-14 px-4 sm:px-6 lg:px-8'"
  >
    <div
      class="mx-auto saveany-sheet"
      :class="embedded
        ? 'max-w-none w-full flex flex-col flex-1 min-h-0 overflow-hidden p-4 sm:p-4 lg:p-5'
        : 'max-w-4xl p-8 sm:p-10'"
    >
      <!-- Tab bar -->
      <div v-if="isVip" class="flex-shrink-0 flex flex-wrap gap-1 border-b border-slate-100 -mx-2 px-1 pb-px">
        <button
          type="button"
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'group flex items-center rounded-t-xl font-medium transition-colors relative',
            embedded ? 'gap-1.5 px-3 py-2 text-sm' : 'gap-2 px-4 py-3 text-[15px]',
            activeTab === tab.id
              ? 'text-[#1565d8]'
              : 'text-slate-500 hover:text-slate-800',
          ]"
        >
          <span :class="embedded ? 'text-[0.95rem]' : 'text-base'">{{ tab.icon }}</span>
          {{ tab.label }}
          <span
            v-if="activeTab === tab.id"
            class="absolute bottom-0 left-3 right-3 h-[3px] bg-[#3b82f6] rounded-t-full"
          />
        </button>
      </div>

      <p
        v-if="errorMessage && isVip"
        class="flex-shrink-0 mt-4 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700"
        role="alert"
      >
        {{ errorMessage }}
      </p>

      <!-- VIP upsell for free users -->
      <div
        v-if="!isVip"
        class="flex flex-col items-center justify-center text-center py-12 sm:py-16 px-6"
      >
        <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center text-2xl mb-4">
          ✨
        </div>
        <h3 class="text-lg font-bold text-slate-900 mb-2">AI 能力为 VIP 专属</h3>
        <p class="text-sm text-slate-500 mb-6 max-w-xs leading-relaxed">
          升级 VIP 后可使用 AI 视频总结、思维导图、字幕导出与 AI 问答等功能
        </p>
        <button type="button" class="btn-primary px-8 py-3 text-sm" @click="emit('upgrade')">
          立即升级 VIP · ¥29 买断
        </button>
      </div>

      <div
        v-else
        :class="embedded
          ? 'flex-1 min-h-0 overflow-y-auto overscroll-contain pt-3'
          : 'pt-7 min-h-[200px]'"
      >
        <!-- ========= Summary (Markdown rendered) ========= -->
        <div v-show="activeTab === 'summary'" class="summary-prose">
          <template v-if="streamingText && !summaryDone">
            <div v-html="renderedStreamingHtml"></div>
            <span class="inline-block w-1.5 h-5 bg-blue-400 rounded-sm animate-pulse ml-0.5 align-text-bottom" />
          </template>
          <template v-else-if="summaryDone">
            <div v-html="renderedSummaryHtml"></div>
          </template>
          <div v-else class="text-sm text-slate-400 py-12 text-center">
            暂无摘要内容
          </div>
        </div>

        <!-- ========= Subtitles ========= -->
        <div v-show="activeTab === 'subtitles'">
          <div v-if="data.subtitles?.length" class="space-y-0">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-2">
                <span class="text-sm text-slate-500">共 {{ data.subtitles.length }} 条字幕</span>
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-600 border border-blue-100">
                  {{ subtitleSourceLabel }} <template v-if="data.language"> · {{ data.language }}</template>
                </span>
              </div>
              <div class="flex items-center gap-3">
                <!-- Subtitle download dropdown -->
                <div ref="subtitleDropdownRef" class="relative">
                  <button
                    type="button"
                    @click="showSubtitleDropdown = !showSubtitleDropdown"
                    class="text-xs text-[#2580f7] hover:text-[#1d63d8] font-semibold transition-colors flex items-center gap-1"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    下载字幕
                  </button>
                  <div
                    v-show="showSubtitleDropdown"
                    class="absolute right-0 mt-1 w-36 bg-white rounded-xl shadow-lg border border-slate-100 py-1 z-20"
                  >
                    <button
                      v-for="fmt in subtitleFormats"
                      :key="fmt.key"
                      type="button"
                      @click="downloadSubtitle(fmt.key)"
                      class="w-full text-left px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 hover:text-[#1565d8] transition-colors"
                    >
                      {{ fmt.label }} <span class="text-slate-400 text-xs">.{{ fmt.ext }}</span>
                    </button>
                  </div>
                </div>
                <button
                  v-if="data.subtitles.length > 20"
                  type="button"
                  @click="subtitlesExpanded = !subtitlesExpanded"
                  class="text-xs text-[#2580f7] hover:text-[#1d63d8] font-semibold transition-colors"
                >
                  {{ subtitlesExpanded ? '收起' : '展开全部' }}
                </button>
              </div>
            </div>
            <div class="mb-4">
              <input
                v-model="subtitleSearch"
                type="text"
                placeholder="搜索字幕内容..."
                class="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm bg-slate-50/50 focus:outline-none focus:ring-2 focus:ring-blue-500/15 focus:border-[#93c5fd]"
              />
            </div>
            <div class="max-h-[28rem] overflow-y-auto space-y-0.5 pr-1">
              <div
                v-for="(seg, i) in displayedSubtitles"
                :key="i"
                class="flex gap-3 py-2 px-2 rounded-xl hover:bg-slate-50/90 transition-colors"
              >
                <span class="text-xs text-[#2580f7] font-mono w-[3.25rem] flex-shrink-0 pt-0.5 text-right tabular-nums">
                  {{ formatTimestamp(seg.start) }}
                </span>
                <span class="text-sm text-slate-700 leading-relaxed">{{ seg.text }}</span>
              </div>
              <div v-if="displayedSubtitles.length === 0" class="text-center py-14 text-sm text-slate-400">
                没有匹配的字幕内容
              </div>
            </div>
          </div>
          <div v-else class="text-center py-14 text-sm text-slate-400">
            暂无字幕数据
          </div>
        </div>

        <!-- ========= Mindmap ========= -->
        <div v-show="activeTab === 'mindmap'" class="-mx-1">
          <template v-if="mindmapMarkdown">
            <div class="flex items-center justify-end gap-2 mb-2">
              <button
                type="button"
                @click="downloadMindmapPng"
                class="text-xs text-slate-500 hover:text-[#1565d8] font-medium transition-colors flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-slate-50"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                PNG
              </button>
              <button
                type="button"
                @click="downloadMindmapSvg"
                class="text-xs text-slate-500 hover:text-[#1565d8] font-medium transition-colors flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-slate-50"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
                SVG
              </button>
              <button
                type="button"
                @click="toggleFullscreen"
                class="text-xs text-slate-500 hover:text-[#1565d8] font-medium transition-colors flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-slate-50"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
                {{ isFullscreen ? '退出全屏' : '全屏' }}
              </button>
            </div>
            <div ref="mindmapContainer" :class="['w-full rounded-2xl border border-slate-100 overflow-hidden bg-white mindmap-wrapper', isFullscreen ? 'mindmap-fullscreen' : 'h-96 min-h-[24rem]']">
              <svg ref="mindmapSvg" style="width:100%;height:100%"></svg>
              <button
                v-if="isFullscreen"
                type="button"
                @click="toggleFullscreen"
                class="absolute top-4 right-4 z-50 px-3 py-1.5 text-xs bg-white/90 hover:bg-white text-slate-600 rounded-lg shadow border border-slate-200 transition-colors"
              >
                退出全屏
              </button>
            </div>
          </template>
          <div v-else-if="!data.full_text" class="text-center py-16 text-sm text-slate-400">
            请先生成总结以查看思维导图
          </div>
          <div v-else class="text-center py-16">
            <div class="inline-block w-6 h-6 border-2 border-slate-300 border-t-blue-500 rounded-full animate-spin mb-3"></div>
            <p class="text-sm text-slate-400">正在生成思维导图...</p>
          </div>
        </div>

        <!-- ========= AI Q&A ========= -->
        <div v-show="activeTab === 'qa'" class="flex flex-col" style="min-height: 380px;">
          <div v-if="!data.full_text" class="text-center py-16 px-4">
            <p class="text-sm text-slate-400">请先生成视频总结，获取字幕内容后即可使用 AI 问答</p>
          </div>
          <template v-else>
            <div ref="chatContainer" class="flex-1 overflow-y-auto space-y-4 pr-1 mb-4" style="max-height: 24rem;">
              <div v-if="chatMessages.length === 0" class="text-center py-12">
                <div class="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-[#eff6ff] text-[#3b82f6] mb-3">
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <p class="text-sm text-slate-500 font-medium">向 AI 提问关于这个视频的任何问题</p>
                <p class="text-xs text-slate-400 mt-1">例如："这个视频的核心观点是什么？"</p>
              </div>
              <template v-for="(msg, i) in chatMessages" :key="i">
                <div v-if="msg.role === 'user'" class="flex justify-end">
                  <div class="max-w-[80%] px-4 py-2.5 rounded-2xl rounded-br-md bg-[#3b82f6] text-white text-sm leading-relaxed">
                    {{ msg.content }}
                  </div>
                </div>
                <div v-else class="flex justify-start">
                  <div class="max-w-[80%] px-4 py-2.5 rounded-2xl rounded-bl-md bg-slate-100 text-slate-700 text-sm leading-relaxed chat-prose">
                    <div v-html="renderMarkdown(msg.content)"></div>
                    <span v-if="msg.streaming" class="inline-block w-1.5 h-4 bg-blue-400 rounded-sm animate-pulse ml-0.5 align-text-bottom" />
                  </div>
                </div>
              </template>
            </div>
            <div class="flex gap-2 pt-3 border-t border-slate-100">
              <input
                v-model="chatInput"
                type="text"
                placeholder="输入你的问题..."
                class="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-sm bg-slate-50/50 focus:outline-none focus:ring-2 focus:ring-blue-500/15 focus:border-[#93c5fd]"
                @keydown.enter.prevent="sendChat"
                :disabled="chatLoading"
              />
              <button
                type="button"
                @click="sendChat"
                :disabled="!chatInput.trim() || chatLoading"
                class="px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-[#3b82f6] hover:bg-[#2563eb] disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex-shrink-0"
              >
                发送
              </button>
            </div>
          </template>
        </div>
      </div>

      <div
        v-if="isVip"
        class="flex-shrink-0 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3"
        :class="embedded ? 'mt-4 pt-3' : 'mt-8 pt-4'"
      >
        <span class="text-xs text-slate-400">{{ sourceLabel }}</span>
        <button
          type="button"
          @click="copyFullText"
          class="text-xs text-[#2580f7] hover:text-[#1d63d8] font-semibold flex items-center gap-1.5 transition-colors"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
          </svg>
          复制全文
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { marked } from 'marked'
import { streamChat } from '../api/index.js'

marked.setOptions({ breaks: true, gfm: true })

const props = defineProps({
  data: Object,
  streamingText: { type: String, default: '' },
  mindmapMarkdown: { type: String, default: '' },
  currentUrl: { type: String, default: '' },
  embedded: { type: Boolean, default: false },
  errorMessage: { type: String, default: '' },
  isVip: { type: Boolean, default: false },
})

const emit = defineEmits(['upgrade'])

const activeTab = ref('summary')
const subtitleSearch = ref('')
const subtitlesExpanded = ref(false)
const showSubtitleDropdown = ref(false)
const subtitleDropdownRef = ref(null)

const mindmapContainer = ref(null)
const mindmapSvg = ref(null)
let markmapInstance = null
const isFullscreen = ref(false)

const chatMessages = ref([])
const chatInput = ref('')
const chatLoading = ref(false)
const chatContainer = ref(null)

const tabs = [
  { id: 'summary', label: '总结摘要', icon: '📝' },
  { id: 'subtitles', label: '字幕文本', icon: '📄' },
  { id: 'mindmap', label: '思维导图', icon: '🧠' },
  { id: 'qa', label: 'AI 问答', icon: '💬' },
]

const subtitleFormats = [
  { key: 'srt', label: 'SRT 字幕', ext: 'srt' },
  { key: 'vtt', label: 'VTT 字幕', ext: 'vtt' },
  { key: 'txt', label: '纯文本', ext: 'txt' },
]

const summaryDone = computed(() => props.streamingText && !props.streamingText.endsWith('…'))

const renderedStreamingHtml = computed(() => renderMarkdown(props.streamingText))
const renderedSummaryHtml = computed(() => renderMarkdown(props.streamingText))

const subtitleSourceLabel = computed(() => {
  const map = { platform: '人工字幕', auto: '自动字幕', description: '视频描述' }
  return map[props.data?.source] || '字幕'
})

const filteredSubtitles = computed(() => {
  if (!props.data?.subtitles) return []
  if (!subtitleSearch.value.trim()) return props.data.subtitles
  const q = subtitleSearch.value.trim().toLowerCase()
  return props.data.subtitles.filter(s => s.text.toLowerCase().includes(q))
})

const displayedSubtitles = computed(() => {
  const list = filteredSubtitles.value
  if (subtitleSearch.value.trim()) return list
  if (!subtitlesExpanded.value && list.length > 20) return list.slice(0, 20)
  return list
})

const sourceLabel = computed(() => {
  const map = { platform: '来源：平台字幕', auto: '来源：自动生成字幕', description: '来源：视频描述' }
  return map[props.data?.source] || ''
})

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

function formatTimestamp(seconds) {
  if (seconds == null) return ''
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

function copyFullText() {
  if (props.data?.full_text) {
    navigator.clipboard.writeText(props.data.full_text)
  }
}

// ===== Mindmap =====
async function renderMindmap(md) {
  if (!mindmapSvg.value || !md) return
  try {
    const { Markmap } = await import('markmap-view')
    const { Transformer } = await import('markmap-lib')

    mindmapSvg.value.innerHTML = ''
    const transformer = new Transformer()
    const { root } = transformer.transform(md)
    markmapInstance = Markmap.create(mindmapSvg.value, { autoFit: true }, root)
  } catch (e) {
    console.warn('Mindmap render failed:', e)
  }
}

function toggleFullscreen() {
  if (!mindmapContainer.value) return
  if (!isFullscreen.value) {
    (mindmapContainer.value.requestFullscreen || mindmapContainer.value.webkitRequestFullscreen)?.call(mindmapContainer.value)
  } else {
    (document.exitFullscreen || document.webkitExitFullscreen)?.call(document)
  }
}

function onFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
  nextTick(() => markmapInstance?.fit())
}

function getContentBBox() {
  const svgEl = mindmapSvg.value
  const gRoot = svgEl?.querySelector('g')
  if (gRoot) {
    try {
      const bbox = gRoot.getBBox()
      if (bbox.width > 0 && bbox.height > 0) {
        const transform = gRoot.getAttribute('transform') || ''
        const tm = transform.match(/translate\(\s*([-\d.e]+)\s*[,\s]\s*([-\d.e]+)\s*\)/)
        const sm = transform.match(/scale\(\s*([-\d.e]+)/)
        const tx = tm ? parseFloat(tm[1]) : 0
        const ty = tm ? parseFloat(tm[2]) : 0
        const sc = sm ? parseFloat(sm[1]) : 1
        return { x: bbox.x * sc + tx, y: bbox.y * sc + ty, width: bbox.width * sc, height: bbox.height * sc }
      }
    } catch {}
  }
  return { x: 0, y: 0, width: 800, height: 600 }
}

function setFullViewBox(svgClone) {
  const dims = getContentBBox()
  const pad = 60
  svgClone.setAttribute('viewBox', `${dims.x - pad} ${dims.y - pad} ${dims.width + pad * 2} ${dims.height + pad * 2}`)
  svgClone.setAttribute('width', String(dims.width + pad * 2))
  svgClone.setAttribute('height', String(dims.height + pad * 2))
  return { vw: dims.width + pad * 2, vh: dims.height + pad * 2 }
}

function buildExportableSvg() {
  if (!mindmapSvg.value) return null
  const cloned = mindmapSvg.value.cloneNode(true)
  cloned.querySelectorAll('foreignObject').forEach(fo => {
    const text = fo.textContent?.trim() || ''
    if (!text) { fo.remove(); return }
    const x = parseFloat(fo.getAttribute('x')) || 0
    const y = parseFloat(fo.getAttribute('y')) || 0
    const h = parseFloat(fo.getAttribute('height')) || 20
    const textEl = document.createElementNS('http://www.w3.org/2000/svg', 'text')
    textEl.setAttribute('x', String(x + 4))
    textEl.setAttribute('y', String(y + h / 2 + 5))
    textEl.setAttribute('font-size', '14')
    textEl.setAttribute('font-family', 'sans-serif')
    textEl.setAttribute('fill', '#333')
    textEl.textContent = text
    fo.parentNode.replaceChild(textEl, fo)
  })
  return cloned
}

async function downloadMindmapPng() {
  const exportSvg = buildExportableSvg()
  if (!exportSvg) return
  const { vw, vh } = setFullViewBox(exportSvg)
  const scale = Math.max(4, Math.ceil(3840 / vw))
  const svgString = new XMLSerializer().serializeToString(exportSvg)
  const canvas = document.createElement('canvas')
  canvas.width = vw * scale
  canvas.height = vh * scale
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  const img = new Image()
  const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  img.onload = () => {
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
    URL.revokeObjectURL(url)
    canvas.toBlob(pngBlob => {
      if (pngBlob) triggerBlobDownload(pngBlob, '思维导图.png')
    }, 'image/png')
  }
  img.onerror = () => { URL.revokeObjectURL(url); alert('PNG 导出失败，请使用 SVG 下载') }
  img.src = url
}

function downloadMindmapSvg() {
  if (!mindmapSvg.value) return
  const cloned = mindmapSvg.value.cloneNode(true)
  setFullViewBox(cloned)
  const svgString = new XMLSerializer().serializeToString(cloned)
  const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' })
  triggerBlobDownload(blob, '思维导图.svg')
}

// ===== Subtitle download =====
function downloadSubtitle(format) {
  showSubtitleDropdown.value = false
  const segments = props.data?.subtitles
  if (!segments?.length) return

  let content = ''
  if (format === 'srt') {
    content = segments.map((seg, i) => {
      const start = formatSrtTime(seg.start)
      const end = formatSrtTime(seg.end || seg.start + 5)
      return `${i + 1}\n${start} --> ${end}\n${seg.text}\n`
    }).join('\n')
  } else if (format === 'vtt') {
    content = 'WEBVTT\n\n' + segments.map(seg => {
      const start = formatVttTime(seg.start)
      const end = formatVttTime(seg.end || seg.start + 5)
      return `${start} --> ${end}\n${seg.text}\n`
    }).join('\n')
  } else {
    content = segments.map(seg => seg.text).join('\n')
  }

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  triggerBlobDownload(blob, `字幕.${format}`)
}

function formatSrtTime(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  const ms = Math.round((seconds % 1) * 1000)
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(ms).padStart(3, '0')}`
}

function formatVttTime(seconds) {
  return formatSrtTime(seconds).replace(',', '.')
}

// ===== Utilities =====
function triggerBlobDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function handleClickOutside(e) {
  if (subtitleDropdownRef.value && !subtitleDropdownRef.value.contains(e.target)) {
    showSubtitleDropdown.value = false
  }
}

// ===== AI Chat =====
function scrollChatToBottom() {
  nextTick(() => {
    if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  })
}

function sendChat() {
  const question = chatInput.value.trim()
  if (!question || chatLoading.value) return

  chatMessages.value.push({ role: 'user', content: question })
  chatInput.value = ''
  chatLoading.value = true
  chatMessages.value.push({ role: 'assistant', content: '', streaming: true })
  scrollChatToBottom()

  streamChat(
    props.currentUrl,
    question,
    props.data.full_text || '',
    (text) => {
      const msgs = chatMessages.value
      const last = msgs[msgs.length - 1]
      if (last?.role === 'assistant') {
        msgs[msgs.length - 1] = { role: 'assistant', content: last.content + text, streaming: true }
      }
      scrollChatToBottom()
    },
    (err) => {
      const msgs = chatMessages.value
      const last = msgs[msgs.length - 1]
      if (last?.role === 'assistant') {
        msgs[msgs.length - 1] = {
          role: 'assistant',
          content: last.content + (err ? `\n\n[错误: ${err.message}]` : ''),
          streaming: false,
        }
      }
      chatLoading.value = false
      scrollChatToBottom()
    },
  )
}

// ===== Watchers & Lifecycle =====
watch(() => props.mindmapMarkdown, (val) => {
  if (val) nextTick(() => renderMindmap(val))
})

watch(activeTab, (tab) => {
  if (tab === 'mindmap' && props.mindmapMarkdown) {
    nextTick(() => renderMindmap(props.mindmapMarkdown))
  }
})

onMounted(() => {
  document.addEventListener('fullscreenchange', onFullscreenChange)
  document.addEventListener('webkitfullscreenchange', onFullscreenChange)
  document.addEventListener('click', handleClickOutside)
  if (props.mindmapMarkdown) renderMindmap(props.mindmapMarkdown)
})

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  document.removeEventListener('webkitfullscreenchange', onFullscreenChange)
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.summary-prose :deep(h1) { font-size: 1.25rem; font-weight: 700; margin: 1.5rem 0 .75rem; color: #1e293b; padding-bottom: .5rem; border-bottom: 2px solid #bfdbfe; }
.summary-prose :deep(h2) { font-size: 1.125rem; font-weight: 700; margin: 1.5rem 0 .75rem; color: #1e293b; padding-bottom: .5rem; border-bottom: 1px solid #e2e8f0; }
.summary-prose :deep(h3) { font-size: 1rem; font-weight: 600; margin: 1.25rem 0 .5rem; color: #1e293b; }
.summary-prose :deep(p) { margin-bottom: .75rem; line-height: 1.8; color: #334155; }
.summary-prose :deep(ul), .summary-prose :deep(ol) { margin-bottom: .75rem; padding-left: 1.5rem; }
.summary-prose :deep(li) { margin-bottom: .35rem; line-height: 1.8; }
.summary-prose :deep(li::marker) { color: #3b82f6; }
.summary-prose :deep(strong) { color: #1e293b; font-weight: 600; }
.summary-prose :deep(hr) { margin: 1.5rem 0; border-color: #e2e8f0; }
.summary-prose :deep(blockquote) { border-left: 3px solid #3b82f6; padding: .75rem 1rem; color: #64748b; margin: 1rem 0; background: #f8fafc; border-radius: 0 8px 8px 0; }
.summary-prose :deep(code) { background: #f1f5f9; padding: .15rem .4rem; border-radius: 4px; font-size: .85em; color: #1e40af; }
.summary-prose :deep(pre) { background: #1e293b; color: #e2e8f0; border-radius: 8px; padding: 1rem; overflow-x: auto; margin: 1rem 0; }
.summary-prose :deep(pre code) { background: none; padding: 0; color: inherit; }

.chat-prose :deep(p) { margin-bottom: .5rem; line-height: 1.7; }
.chat-prose :deep(p:last-child) { margin-bottom: 0; }
.chat-prose :deep(ul), .chat-prose :deep(ol) { margin-bottom: .5rem; padding-left: 1.25rem; }
.chat-prose :deep(li) { margin-bottom: .2rem; line-height: 1.7; }
.chat-prose :deep(code) { background: rgba(0,0,0,.06); padding: .1rem .35rem; border-radius: 3px; font-size: .85em; }
.chat-prose :deep(strong) { font-weight: 600; }

.mindmap-wrapper :deep(foreignObject) { overflow: visible !important; }
.mindmap-wrapper :deep(foreignObject div) { font: 300 16px/20px sans-serif; color: #333; }
.mindmap-fullscreen { position: fixed !important; inset: 0; z-index: 40; border-radius: 0 !important; border: none !important; background: #fff; }
</style>
