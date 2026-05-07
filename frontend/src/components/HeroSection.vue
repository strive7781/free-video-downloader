<template>
  <section id="hero" class="pt-20 pb-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-4xl mx-auto text-center">
      <!-- Badge -->
      <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50 text-blue-600 text-sm font-medium mb-6 animate-fadeInUp">
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" />
        </svg>
        支持 1000+ 视频平台
      </div>

      <!-- Brand lockup -->
      <p
        class="text-sm font-semibold text-gray-500 tracking-[0.12em] uppercase mb-3 animate-fadeInUp"
        style="animation-delay: 0.05s"
      >
        映鉴 · Kinema
      </p>

      <!-- Title：一句话说清项目 -->
      <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-gray-900 leading-tight mb-4 animate-fadeInUp" style="animation-delay: 0.1s">
        粘贴视频链接，<span class="gradient-text">下载高清到本地</span>
      </h1>

      <!-- Subtitle -->
      <p class="text-lg sm:text-xl text-gray-500 max-w-2xl mx-auto mb-10 animate-fadeInUp" style="animation-delay: 0.2s">
        解析 YouTube、B 站、抖音、TikTok、Twitter 等链接，自选清晰度，文件保存到你的电脑或手机
      </p>

      <!-- Search Box -->
      <div class="max-w-2xl mx-auto animate-fadeInUp" style="animation-delay: 0.3s">
        <form @submit.prevent="handleSubmit" class="relative">
          <div class="flex items-center bg-white rounded-2xl shadow-lg shadow-blue-100/50 border border-gray-200 focus-within:border-blue-400 focus-within:shadow-blue-200/60 transition-all p-2">
            <div class="pl-4 pr-2 text-gray-400">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </div>
            <input
              v-model="url"
              type="text"
              placeholder="粘贴视频链接，例如 https://www.youtube.com/watch?v=..."
              class="flex-1 px-2 py-3 text-base text-gray-800 placeholder-gray-400 outline-none bg-transparent"
              :disabled="loading"
            />
            <button
              type="submit"
              :disabled="!url.trim() || loading"
              class="btn-primary px-6 sm:px-8 py-3 text-base flex items-center gap-2 whitespace-nowrap"
            >
              <svg v-if="loading" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              {{ loading ? '解析中...' : '解析视频' }}
            </button>
          </div>
        </form>

        <!-- Error Message -->
        <p v-if="error" class="mt-4 text-red-500 text-sm flex items-center justify-center gap-1">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
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

function handleSubmit() {
  if (url.value.trim()) {
    emit('parse', url.value.trim())
  }
}
</script>
