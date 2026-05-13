<template>
  <section id="hero" class="relative isolate overflow-hidden pt-14 pb-16 px-4 sm:px-6 lg:px-8">
    <!-- Soft background blobs -->
    <div class="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      <div class="hero-blob absolute -top-24 left-[8%] w-[420px] h-[420px] rounded-full bg-[#dbeafe]/45 blur-[80px]" />
      <div class="hero-blob absolute top-40 -right-20 w-[380px] h-[380px] rounded-full bg-[#e0f2fe]/50 blur-[72px]" />
      <div class="hero-blob absolute bottom-0 left-[35%] w-[280px] h-[280px] rounded-full bg-[#eff6ff]/80 blur-[64px]" />
    </div>

    <div class="max-w-4xl mx-auto text-center">
      <!-- Badge -->
      <div
        class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/90 border border-emerald-100 text-gray-700 text-sm font-medium mb-6 shadow-sm shadow-emerald-500/5 animate-fadeInUp"
      >
        <span class="inline-flex rounded-full h-2 w-2 bg-emerald-500 shrink-0 ring-4 ring-emerald-500/20" />
        支持 1800+ 平台，永久免费使用
      </div>

      <!-- Title -->
      <h1 class="text-4xl sm:text-5xl lg:text-[3.25rem] font-extrabold text-gray-800 leading-[1.2] mb-5 animate-fadeInUp" style="animation-delay: 0.08s">
        万能视频下载器，<span class="text-[#2563eb]">一键保存</span>
      </h1>

      <!-- Subtitle -->
      <div class="text-base sm:text-lg text-gray-500 max-w-2xl mx-auto mb-10 space-y-1 animate-fadeInUp" style="animation-delay: 0.14s">
        <p>粘贴视频链接，智能解析，支持多种清晰度下载。</p>
        <p class="text-gray-400 text-[0.9375rem] sm:text-base">
          YouTube、Bilibili、抖音、TikTok… 随时随地，想下就下
        </p>
      </div>

      <!-- Search -->
      <div class="max-w-2xl mx-auto animate-fadeInUp" style="animation-delay: 0.22s">
        <form @submit.prevent="handleSubmit" class="relative">
          <div
            class="flex items-stretch bg-white rounded-full shadow-[0_8px_30px_-8px_rgba(37,99,235,0.12)] border border-gray-100 focus-within:border-[#93c5fd] focus-within:ring-4 focus-within:ring-blue-500/10 transition-all pl-1 pr-2 py-1.5 gap-1"
          >
            <div class="flex items-center pl-4 pr-1 text-gray-400 shrink-0">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </div>
            <input
              v-model="url"
              type="text"
              placeholder="粘贴视频页面链接..."
              class="flex-1 min-w-0 py-3 px-2 text-[15px] sm:text-base text-gray-800 placeholder-gray-400 outline-none bg-transparent"
              :disabled="loading"
            />
            <button
              type="submit"
              :disabled="!url.trim() || loading"
              class="hero-parse-btn shrink-0 inline-flex items-center justify-center gap-2 rounded-full px-6 sm:px-8 py-3 text-[15px] font-semibold text-white bg-gradient-to-br from-[#3b82f6] to-[#2563eb] shadow-[0_4px_14px_rgba(37,99,235,0.35)] hover:shadow-[0_6px_20px_rgba(37,99,235,0.4)] hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-55 disabled:pointer-events-none disabled:shadow-none disabled:translate-y-0 transition-all"
            >
              <svg v-if="loading" class="w-[1.125rem] h-[1.125rem] animate-spin shrink-0" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <svg v-else class="w-5 h-5 shrink-0 opacity-95" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              {{ loading ? '解析中…' : '解析视频' }}
            </button>
          </div>
        </form>

        <!-- Quick samples -->
        <div class="mt-6 flex flex-wrap items-center justify-center gap-x-2 gap-y-2 text-sm">
          <span class="text-gray-500 shrink-0">试试：</span>
          <button
            v-for="s in samples"
            :key="s.label"
            type="button"
            class="px-3 py-1.5 rounded-full border border-gray-200 bg-white/80 text-gray-600 hover:border-[#93c5fd] hover:bg-blue-50/80 hover:text-[#2563eb] transition-colors"
            @click="url = s.url"
          >
            {{ s.label }}
          </button>
        </div>

        <p v-if="error" class="mt-5 text-red-500 text-sm flex items-center justify-center gap-1.5">
          <svg class="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
          {{ error }}
        </p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  loading: Boolean,
  error: String,
})

const emit = defineEmits(['parse'])
const url = ref('')

const samples = [
  { label: 'YouTube', url: 'https://www.youtube.com/watch?v=jNQXAC9IVRw' },
  { label: 'Bilibili', url: 'https://www.bilibili.com/video/BV1mAAmzqEfP' },
  { label: 'Twitter/X', url: 'https://twitter.com/w3cdevs/status/1960374525513625954' },
]

function handleSubmit() {
  if (url.value.trim()) {
    emit('parse', url.value.trim())
  }
}
</script>
