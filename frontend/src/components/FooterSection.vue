<template>
  <footer class="bg-white border-t border-gray-100 py-8 px-4 sm:px-6 lg:px-8">
    <div class="max-w-5xl mx-auto">
      <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </div>
          <span class="text-sm font-semibold text-gray-700">映鉴</span>
        </div>

        <p class="text-xs text-gray-400 text-center">
          本站仅提供视频下载工具，请遵守相关法律法规和版权协议。下载的内容仅供个人学习研究使用。
        </p>

        <p class="text-xs text-gray-400">
          &copy; {{ new Date().getFullYear() }} 映鉴 Kinema
        </p>
      </div>
    </div>
  </footer>
</template>
