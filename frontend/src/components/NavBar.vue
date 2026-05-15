<template>
  <nav class="sticky top-0 z-50 bg-white/70 backdrop-blur-md border-b border-slate-100/90">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center gap-4 h-[3.5rem] sm:h-[3.625rem]">
        <!-- Logo -->
        <div class="flex items-center gap-2.5 cursor-pointer shrink-0" @click="scrollToTop">
          <div class="w-9 h-9 rounded-full bg-[#2580f7] flex items-center justify-center shadow-[0_4px_14px_rgba(37,99,235,0.28)] ring-4 ring-[#dbeafe]/60">
            <svg class="w-[15px] h-[15px] text-white translate-x-[0.5px]" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-lg font-bold text-[#0f3488] tracking-tight">SaveAny</span>
            <span class="hidden sm:inline-flex text-[11px] font-semibold text-[#1d63d8] bg-[#eaf3ff] border border-[#cfe4ff]/90 rounded-full px-2.5 py-0.5">
              万能视频下载
            </span>
          </div>
        </div>

        <!-- Center nav -->
        <div class="hidden md:flex flex-1 justify-center items-center gap-12 xl:gap-14">
          <a href="#features" class="text-[15px] font-medium text-slate-600 hover:text-[#2563eb] transition-colors">
            功能特性
          </a>
          <a href="#pricing" class="text-[15px] font-medium text-slate-600 hover:text-[#2563eb] transition-colors">
            套餐价格
          </a>
          <a href="#platforms" class="text-[15px] font-medium text-slate-600 hover:text-[#2563eb] transition-colors">
            支持平台
          </a>
        </div>

        <!-- Right -->
        <div class="flex items-center gap-2 sm:gap-3 ml-auto shrink-0">
          <button
            type="button"
            class="vip-btn inline-flex items-center gap-1.5 rounded-full border border-[#b6d6ff] bg-[#e8f2ff] px-3.5 sm:px-4 py-2 text-xs sm:text-sm font-semibold text-[#1854c7] hover:bg-[#d8eaff] transition-colors shadow-sm shadow-blue-500/5"
            @click="openVip"
          >
            <svg class="w-4 h-4 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            开通 VIP
          </button>

          <button type="button" class="md:hidden p-2 text-gray-500 rounded-lg hover:bg-gray-50" @click="mobileOpen = !mobileOpen" aria-label="菜单">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path v-if="!mobileOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <div v-if="mobileOpen" class="md:hidden pb-4 space-y-1 border-t border-gray-100 mt-px pt-3">
        <a href="#features" class="block px-3 py-2.5 text-sm font-medium text-gray-600 hover:text-[#2563eb] rounded-lg hover:bg-blue-50/80" @click="mobileOpen = false">功能特性</a>
        <a href="#pricing" class="block px-3 py-2.5 text-sm font-medium text-gray-600 hover:text-[#2563eb] rounded-lg hover:bg-blue-50/80" @click="mobileOpen = false">套餐价格</a>
        <a href="#platforms" class="block px-3 py-2.5 text-sm font-medium text-gray-600 hover:text-[#2563eb] rounded-lg hover:bg-blue-50/80" @click="mobileOpen = false">支持平台</a>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'

const mobileOpen = ref(false)

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function openVip() {
  document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' })
}
</script>
