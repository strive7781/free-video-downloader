<template>
  <section class="pb-12 px-4 sm:px-6 lg:px-8 animate-fadeInUp">
    <div class="max-w-3xl mx-auto space-y-5">

      <!-- Video Info Card -->
      <div class="card p-5 sm:p-6">
        <div class="flex flex-col sm:flex-row gap-5">
          <!-- Thumbnail -->
          <div class="sm:w-64 flex-shrink-0">
            <div class="relative rounded-xl overflow-hidden bg-gray-100 aspect-video">
              <img
                v-if="thumbnailSrc"
                :src="thumbnailSrc"
                :alt="video.title"
                class="w-full h-full object-cover"
                referrerpolicy="no-referrer"
                @error="onImgError"
              />
              <div v-else class="w-full h-full flex items-center justify-center text-gray-300">
                <svg class="w-14 h-14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
              <div v-if="video.duration" class="absolute bottom-2 right-2 px-2 py-0.5 bg-black/70 text-white text-xs rounded-md font-medium">
                {{ formatDuration(video.duration) }}
              </div>
            </div>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <h3 class="text-lg font-bold text-gray-900 leading-snug mb-2 line-clamp-2">
              {{ video.title }}
            </h3>
            <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-500 mb-3">
              <span v-if="video.uploader" class="flex items-center gap-1">
                <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                {{ video.uploader }}
              </span>
              <span v-if="video.extractor" class="px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full text-xs font-medium">
                {{ video.extractor }}
              </span>
              <span v-if="video.view_count" class="flex items-center gap-1">
                <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                {{ formatCount(video.view_count) }}
              </span>
            </div>
            <p v-if="video.description" class="text-sm text-gray-400 leading-relaxed line-clamp-3">
              {{ video.description }}
            </p>
          </div>
        </div>
      </div>

      <!-- Format Selection -->
      <div class="card p-5 sm:p-6">
        <h4 class="flex items-center gap-2 text-base font-semibold text-gray-900 mb-4">
          <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
          </svg>
          选择清晰度和格式
        </h4>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <button
            v-for="f in video.formats"
            :key="f.format_id"
            @click="selectedFormat = f.format_id"
            class="flex items-start gap-3 p-3.5 rounded-xl border-2 text-left transition-all cursor-pointer"
            :class="selectedFormat === f.format_id
              ? 'border-blue-500 bg-blue-50/50 shadow-sm'
              : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'"
          >
            <div class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
              :class="selectedFormat === f.format_id ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-400'"
            >
              <svg v-if="f.resolution.includes('audio')" class="w-4.5 h-4.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
              </svg>
              <svg v-else class="w-4.5 h-4.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </div>
            <div class="min-w-0">
              <div class="text-sm font-semibold text-gray-900">
                {{ f.resolution }}
                <span v-if="f.filesize" class="font-normal text-gray-500">({{ formatSize(f.filesize) }})</span>
              </div>
              <div class="text-xs text-gray-400 mt-0.5">
                {{ f.ext.toUpperCase() }}
                <span v-if="f.quality_note"> · {{ f.quality_note }}</span>
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- Download Button -->
      <div class="flex flex-col sm:flex-row items-center gap-4">
        <button
          @click="$emit('download', selectedFormat)"
          :disabled="downloading"
          class="btn-primary px-10 py-3.5 text-base flex items-center gap-2.5"
        >
          <svg v-if="downloading" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          {{ downloading ? '下载中...' : '立即下载' }}
        </button>
        <span v-if="selectedFormatLabel" class="text-sm text-gray-400">
          已选择: {{ selectedFormatLabel }}
        </span>
      </div>

      <!-- Download Progress -->
      <div v-if="downloadProgress" class="text-center">
        <p class="text-sm" :class="downloadProgress.includes('失败') ? 'text-red-500' : 'text-green-600'">
          {{ downloadProgress }}
        </p>
      </div>

    </div>
  </section>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  video: Object,
  downloading: Boolean,
  downloadProgress: String,
})

defineEmits(['download'])

const selectedFormat = ref('')
const imgFailed = ref(false)

const thumbnailSrc = computed(() => {
  if (imgFailed.value || !props.video?.thumbnail) return ''
  return '/api/thumbnail?url=' + encodeURIComponent(props.video.thumbnail)
})

const selectedFormatLabel = computed(() => {
  if (!props.video?.formats) return ''
  const f = props.video.formats.find(f => f.format_id === selectedFormat.value)
  if (!f) return ''
  let label = f.resolution
  if (f.quality_note) label += ' (' + f.quality_note + ')'
  return label
})

function onImgError() {
  imgFailed.value = true
}

watch(() => props.video, (v) => {
  imgFailed.value = false
  if (v?.formats?.length > 0) {
    selectedFormat.value = v.formats[0].format_id
  }
}, { immediate: true })

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
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}

function formatCount(n) {
  if (!n) return ''
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return n.toLocaleString()
}
</script>
