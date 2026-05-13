<template>
  <section class="pb-10 px-4 sm:px-6 lg:px-8 animate-fadeInUp">
    <div class="max-w-4xl mx-auto">
      <div class="saveany-sheet overflow-hidden">
        <!-- Video info -->
        <div class="p-6 sm:p-8 lg:p-9">
          <div class="flex flex-col sm:flex-row gap-6 lg:gap-8">
            <div class="sm:w-[272px] flex-shrink-0">
              <div class="relative rounded-2xl overflow-hidden bg-slate-100 aspect-video shadow-inner ring-1 ring-slate-100">
                <img
                  v-if="thumbnailSrc"
                  :src="thumbnailSrc"
                  :alt="video.title"
                  class="w-full h-full object-cover"
                  referrerpolicy="no-referrer"
                  @error="onImgError"
                />
                <div v-else class="w-full h-full flex items-center justify-center text-slate-300">
                  <svg class="w-14 h-14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </div>
                <div
                  v-if="video.duration"
                  class="absolute bottom-2.5 right-2.5 px-2 py-0.5 bg-black/75 text-white text-xs rounded-md font-medium tabular-nums"
                >
                  {{ formatDuration(video.duration) }}
                </div>
              </div>
            </div>

            <div class="flex-1 min-w-0">
              <h3 class="text-lg sm:text-xl font-bold text-slate-900 leading-snug mb-2.5 line-clamp-3">
                {{ video.title }}
              </h3>
              <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-500 mb-3">
                <span v-if="video.uploader" class="inline-flex items-center gap-1.5">
                  <svg class="w-4 h-4 flex-shrink-0 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  {{ video.uploader }}
                </span>
                <span v-if="video.extractor" class="inline-flex px-2.5 py-0.5 bg-[#e8f3ff] text-[#1565d8] rounded-lg text-xs font-semibold">
                  {{ video.extractor }}
                </span>
                <span v-if="video.view_count" class="inline-flex items-center gap-1">
                  <svg class="w-4 h-4 flex-shrink-0 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  {{ formatCount(video.view_count) }}
                </span>
              </div>
              <p v-if="video.description" class="text-sm text-slate-500 leading-relaxed line-clamp-4">
                {{ video.description }}
              </p>
            </div>
          </div>
        </div>

        <div class="h-px bg-slate-100" />

        <!-- Formats -->
        <div class="px-6 sm:px-8 lg:px-9 py-7">
          <h4 class="flex items-center gap-2 text-base font-semibold text-slate-900 mb-5">
            <svg class="w-5 h-5 text-[#3b82f6]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
            选择清晰度和格式
          </h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              v-for="f in video.formats"
              :key="f.format_id"
              type="button"
              @click="selectedFormat = f.format_id"
              class="flex items-start gap-3.5 p-4 rounded-xl border text-left transition-all cursor-pointer"
              :class="selectedFormat === f.format_id
                ? 'border-[#3b82f6] bg-[#f0f7ff] ring-2 ring-[#3b82f6]/20'
                : 'border-slate-200/95 bg-white hover:border-[#93c5fd] hover:bg-slate-50/80'"
            >
              <div
                class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                :class="selectedFormat === f.format_id ? 'bg-[#3b82f6] text-white shadow-md shadow-blue-500/25' : 'bg-slate-100 text-slate-400'"
              >
                <svg v-if="f.resolution.includes('audio')" class="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                </svg>
                <svg v-else class="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
              <div class="min-w-0 flex-1">
                <div class="text-[15px] font-semibold text-slate-900 leading-snug">
                  {{ formatPrimaryLine(f) }}
                </div>
                <div class="text-xs text-slate-400 mt-1">
                  {{ formatSecondaryLine(f) }}
                </div>
              </div>
            </button>
          </div>
        </div>

        <div class="h-px bg-slate-100" />

        <!-- Actions -->
        <div class="px-6 sm:px-8 lg:px-9 py-6 bg-slate-50/35">
          <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-5">
            <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-3 sm:gap-4 flex-1">
              <button
                type="button"
                @click="$emit('download', selectedFormat)"
                :disabled="downloading"
                class="btn-primary shrink-0 inline-flex items-center justify-center gap-2.5 px-10 py-3.5 rounded-full text-[15px] font-semibold"
              >
                <svg v-if="downloading" class="w-5 h-5 animate-spin shrink-0" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <svg v-else class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                {{ downloading ? '下载中...' : '立即下载' }}
              </button>
              <button
                type="button"
                @click="$emit('summarize')"
                :disabled="summarizing"
                class="shrink-0 inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-full text-[15px] font-semibold border-2 border-[#93c5fd] bg-white text-[#1d63d8] hover:bg-[#f0f7ff] transition-colors disabled:opacity-55 disabled:pointer-events-none shadow-sm shadow-slate-200/40"
              >
                <svg v-if="summarizing" class="w-5 h-5 animate-spin shrink-0" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <svg v-else class="w-5 h-5 shrink-0 text-[#f59e0b]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                {{ summarizing ? 'AI 分析中…' : 'AI 总结' }}
              </button>
            </div>
            <p class="text-sm text-slate-400 text-center lg:text-right lg:max-w-xs lg:leading-relaxed whitespace-normal">
              {{ selectedFormatLabel ? `已选择: ${selectedFormatLabel}` : '请选择清晰度及格式' }}
            </p>
          </div>
          <div v-if="downloadProgress" class="mt-4 text-center lg:text-right">
            <p class="text-sm" :class="downloadProgress.includes('失败') ? 'text-red-500' : 'text-emerald-600'">
              {{ downloadProgress }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  video: Object,
  downloading: Boolean,
  summarizing: Boolean,
  downloadProgress: String,
})

defineEmits(['download', 'summarize'])

const selectedFormat = ref('')
const imgFailed = ref(false)

const thumbnailSrc = computed(() => {
  if (imgFailed.value || !props.video?.thumbnail) return ''
  return '/api/thumbnail?url=' + encodeURIComponent(props.video.thumbnail)
})

const selectedFormatLabel = computed(() => {
  if (!props.video?.formats) return ''
  const f = props.video.formats.find((x) => x.format_id === selectedFormat.value)
  if (!f) return ''
  let label = f.resolution
  if (f.quality_note) label += ` (${f.quality_note})`
  return label
})

watch(() => props.video, (v) => {
  imgFailed.value = false
  if (v?.formats?.length > 0) {
    selectedFormat.value = v.formats[0].format_id
  }
}, { immediate: true })

function formatPrimaryLine(f) {
  if (f.quality_note) return `${f.resolution} ${f.quality_note}`
  return String(f.resolution || '')
}

function formatSecondaryLine(f) {
  const ext = String(f.ext || '').toUpperCase()
  const size = f.filesize ? formatSize(f.filesize) : ''
  if (ext && size) return `${ext} · ${size}`
  if (ext) return ext
  return '点击选择此清晰度'
}

function onImgError() {
  imgFailed.value = true
}

function formatDuration(seconds) {
  if (!seconds) return ''
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

function formatCount(n) {
  if (!n) return ''
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`
  return n.toLocaleString()
}
</script>
