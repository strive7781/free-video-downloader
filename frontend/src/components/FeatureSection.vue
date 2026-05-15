<template>
  <section id="features" class="py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-5xl mx-auto">
      <h2 class="sr-only">功能特性</h2>
      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div v-for="f in features" :key="f.title" class="card p-6 text-center">
          <div class="w-12 h-12 mx-auto mb-4 rounded-2xl flex items-center justify-center text-xl" :class="f.bg">
            {{ f.icon }}
          </div>
          <h3 class="text-base font-semibold text-gray-900 mb-1">{{ f.title }}</h3>
          <p class="text-sm text-gray-500 leading-relaxed">{{ f.desc }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
const features = [
  {
    icon: '⚡',
    title: '极速解析',
    desc: '秒级解析视频信息，无需等待',
    bg: 'bg-amber-50',
  },
  {
    icon: '🎯',
    title: '高清无水印',
    desc: '支持 4K 超高清，原画质量下载',
    bg: 'bg-blue-50',
  },
  {
    icon: '📱',
    title: '多端适配',
    desc: '手机、平板、电脑均可使用',
    bg: 'bg-green-50',
  },
  {
    icon: '🔒',
    title: '安全可靠',
    desc: '无需安装软件，在线即用即走',
    bg: 'bg-purple-50',
  },
]
</script>
