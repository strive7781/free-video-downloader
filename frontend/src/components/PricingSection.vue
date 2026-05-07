<template>
  <section id="pricing" class="py-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-transparent to-blue-50/50">
    <div class="max-w-5xl mx-auto text-center">
      <h2 class="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">
        选择适合你的<span class="gradient-text">方案</span>
      </h2>
      <p class="text-gray-500 mb-12 max-w-xl mx-auto">
        免费即可体验核心功能，升级解锁更多高级能力
      </p>

      <div class="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
        <!-- Free Plan -->
        <div class="card p-8 text-left relative">
          <h3 class="text-lg font-semibold text-gray-900 mb-1">免费版</h3>
          <p class="text-sm text-gray-500 mb-6">满足基本下载需求</p>
          <div class="mb-6">
            <span class="text-4xl font-bold text-gray-900">¥0</span>
            <span class="text-gray-500 text-sm"> / 永久</span>
          </div>
          <ul class="space-y-3 mb-8">
            <li v-for="f in freePlan" :key="f" class="flex items-start gap-2 text-sm text-gray-600">
              <svg class="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
              {{ f }}
            </li>
          </ul>
          <button class="w-full py-3 rounded-xl border-2 border-gray-200 text-gray-700 font-semibold text-sm hover:border-blue-300 hover:text-blue-600 transition-all">
            当前方案
          </button>
        </div>

        <!-- Pro Plan -->
        <div class="card p-8 text-left relative border-2 border-blue-500 shadow-xl shadow-blue-100/50">
          <div class="absolute -top-3 right-6 px-3 py-1 bg-gradient-to-r from-amber-400 to-orange-500 text-white text-xs font-bold rounded-full">
            推荐
          </div>
          <h3 class="text-lg font-semibold text-gray-900 mb-1">高级版</h3>
          <p class="text-sm text-gray-500 mb-6">专业用户的最佳选择</p>
          <div class="mb-6">
            <span class="text-4xl font-bold text-gray-900">¥29</span>
            <span class="text-gray-500 text-sm"> / 月</span>
          </div>
          <ul class="space-y-3 mb-8">
            <li v-for="f in proPlan" :key="f" class="flex items-start gap-2 text-sm text-gray-600">
              <svg class="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
              {{ f }}
            </li>
          </ul>
          <button class="btn-primary w-full py-3 text-sm">
            立即升级
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
const freePlan = [
  '每日 3 次免费下载',
  '支持 720p 清晰度',
  '单个视频下载',
  '常见格式支持',
]

const proPlan = [
  '无限次下载',
  '支持 4K 超高清',
  '批量下载功能',
  '字幕提取与翻译',
  '音频单独提取',
  '无广告 · 极速下载',
  '专属客服支持',
]
</script>
