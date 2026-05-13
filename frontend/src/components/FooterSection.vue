<template>
  <footer class="relative z-10 border-t border-slate-100/90 bg-white/65 backdrop-blur-sm py-8 px-4 sm:px-6 lg:px-8 mt-auto">
    <div class="max-w-5xl mx-auto">
      <div class="flex flex-col sm:flex-row items-center justify-between gap-5">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-full bg-[#2580f7] flex items-center justify-center shadow-sm shadow-blue-500/25">
            <svg class="w-3 h-3 text-white translate-x-[0.5px]" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
          <span class="text-sm font-bold text-[#0f3488]">SaveAny</span>
        </div>

        <p class="text-xs text-slate-400 text-center max-w-xl leading-relaxed">
          本站仅提供视频解析与下载辅助工具，请遵守法律法规与平台规则。内容仅供个人学习研究使用。
        </p>

        <p class="text-xs text-slate-400">
          &copy; {{ new Date().getFullYear() }} SaveAny
        </p>
      </div>
    </div>
  </footer>
</template>
