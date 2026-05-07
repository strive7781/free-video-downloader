<template>
  <nav class="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-gray-100">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <div class="flex items-center gap-2 cursor-pointer" @click="scrollToTop">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <div class="flex flex-col items-start leading-tight">
            <span class="text-xl font-bold text-gray-900 tracking-tight">映<span class="text-blue-600">鉴</span></span>
            <span class="text-[10px] font-medium text-gray-400 tracking-[0.2em] uppercase">Kinema</span>
          </div>
        </div>

        <!-- Desktop Menu -->
        <div class="hidden md:flex items-center gap-8">
          <a href="#hero" class="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors">首页</a>
          <a href="#platforms" class="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors">支持平台</a>
          <a href="#pricing" class="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors">定价</a>
        </div>

        <!-- Login Button -->
        <div class="flex items-center gap-3">
          <button class="hidden sm:inline-flex text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors">
            登录
          </button>
          <button class="btn-primary text-sm px-5 py-2">
            免费体验
          </button>
        </div>

        <!-- Mobile Menu Button -->
        <button class="md:hidden p-2 text-gray-500" @click="mobileOpen = !mobileOpen">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path v-if="!mobileOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Mobile Menu -->
      <div v-if="mobileOpen" class="md:hidden pb-4 space-y-2">
        <a href="#hero" class="block px-3 py-2 text-sm text-gray-600 hover:text-blue-600 rounded-lg hover:bg-blue-50" @click="mobileOpen = false">首页</a>
        <a href="#platforms" class="block px-3 py-2 text-sm text-gray-600 hover:text-blue-600 rounded-lg hover:bg-blue-50" @click="mobileOpen = false">支持平台</a>
        <a href="#pricing" class="block px-3 py-2 text-sm text-gray-600 hover:text-blue-600 rounded-lg hover:bg-blue-50" @click="mobileOpen = false">定价</a>
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
</script>
