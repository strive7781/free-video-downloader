<template>
  <section id="platforms" class="py-16 px-4 sm:px-6 lg:px-8">
    <div class="max-w-5xl mx-auto text-center">
      <h2 class="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">
        支持<span class="gradient-text">海量平台</span>
      </h2>
      <p class="text-gray-500 mb-12 max-w-xl mx-auto">
        覆盖全球主流视频平台，一个工具满足所有下载需求
      </p>

      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <div
          v-for="p in platforms"
          :key="p.name"
          class="card flex flex-col items-center justify-center p-5 gap-3 hover:scale-105 transition-transform cursor-default"
        >
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl" :class="p.bg">
            {{ p.icon }}
          </div>
          <span class="text-sm font-medium text-gray-700">{{ p.name }}</span>
        </div>
      </div>

      <p class="mt-8 text-sm text-gray-400">
        还有 1000+ 其他平台...
      </p>
    </div>
  </section>
</template>

<script setup>
const platforms = [
  { name: 'YouTube', icon: '▶', bg: 'bg-red-50 text-red-500' },
  { name: 'Bilibili', icon: '📺', bg: 'bg-pink-50 text-pink-500' },
  { name: 'TikTok', icon: '🎵', bg: 'bg-gray-100 text-gray-800' },
  { name: '抖音', icon: '🎶', bg: 'bg-gray-100 text-gray-800' },
  { name: 'Twitter/X', icon: '𝕏', bg: 'bg-gray-100 text-gray-800' },
  { name: 'Instagram', icon: '📷', bg: 'bg-gradient-to-br from-purple-50 to-pink-50 text-purple-500' },
  { name: 'Facebook', icon: '📘', bg: 'bg-blue-50 text-blue-600' },
  { name: 'Vimeo', icon: '🎬', bg: 'bg-cyan-50 text-cyan-600' },
  { name: 'Twitch', icon: '🟣', bg: 'bg-purple-50 text-purple-500' },
  { name: '西瓜视频', icon: '🍉', bg: 'bg-red-50 text-red-400' },
  { name: '微博', icon: '📰', bg: 'bg-orange-50 text-orange-500' },
  { name: '更多...', icon: '🌐', bg: 'bg-blue-50 text-blue-400' },
]
</script>
