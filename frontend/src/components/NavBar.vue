<template>
  <nav class="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-100/90">
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
        <div class="hidden md:flex flex-1 justify-center items-center gap-10 xl:gap-12">
          <a href="#features" class="text-[15px] font-medium text-slate-600 hover:text-[#2563eb] transition-colors">功能特性</a>
          <a href="#pricing" class="text-[15px] font-medium text-slate-600 hover:text-[#2563eb] transition-colors">套餐价格</a>
          <a href="#platforms" class="text-[15px] font-medium text-slate-600 hover:text-[#2563eb] transition-colors">支持平台</a>
        </div>

        <!-- Right -->
        <div class="flex items-center gap-2 sm:gap-3 ml-auto shrink-0">
          <button
            v-if="!isVip"
            type="button"
            class="vip-btn hidden sm:inline-flex items-center gap-1.5 rounded-full border border-[#b6d6ff] bg-[#e8f2ff] px-3.5 sm:px-4 py-2 text-xs sm:text-sm font-semibold text-[#1854c7] hover:bg-[#d8eaff] transition-colors shadow-sm shadow-blue-500/5"
            @click="emit('upgrade')"
          >
            <svg class="w-4 h-4 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            开通 VIP
          </button>

          <!-- Logged in: avatar + dropdown -->
          <div v-if="isLoggedIn" ref="menuRoot" class="relative">
            <button
              type="button"
              class="flex items-center gap-1.5 pl-1 pr-0.5 py-1 rounded-full hover:bg-slate-50 transition-colors"
              :class="{ 'bg-slate-50': userMenuOpen }"
              aria-haspopup="menu"
              :aria-expanded="userMenuOpen"
              @click.stop="userMenuOpen = !userMenuOpen"
            >
              <span
                class="w-9 h-9 rounded-full bg-gradient-to-br from-[#3b82f6] to-[#2563eb] text-white text-sm font-bold flex items-center justify-center shadow-md shadow-blue-500/25 ring-2 ring-white"
              >
                {{ avatarText }}
              </span>
              <svg
                class="w-4 h-4 text-slate-400 transition-transform duration-200"
                :class="{ 'rotate-180': userMenuOpen }"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            <Transition
              enter-active-class="transition duration-150 ease-out"
              enter-from-class="opacity-0 scale-95 -translate-y-1"
              enter-to-class="opacity-100 scale-100 translate-y-0"
              leave-active-class="transition duration-100 ease-in"
              leave-from-class="opacity-100 scale-100"
              leave-to-class="opacity-0 scale-95"
            >
              <div
                v-if="userMenuOpen"
                class="absolute right-0 top-[calc(100%+8px)] w-56 rounded-xl bg-white border border-slate-100 shadow-xl shadow-slate-200/60 py-2 z-[60]"
                role="menu"
              >
                <div class="px-4 py-3 border-b border-slate-100">
                  <p class="text-sm font-semibold text-slate-800 truncate" :title="email">{{ maskedEmail }}</p>
                  <p class="text-xs mt-1" :class="isVip ? 'text-amber-600 font-medium' : 'text-slate-400'">
                    {{ isVip ? 'VIP 会员' : '免费用户' }}
                  </p>
                  <p v-if="!isVip" class="text-[11px] text-slate-400 mt-0.5">
                    今日下载 {{ downloadsRemaining ?? 0 }}/{{ downloadLimit ?? 3 }}
                  </p>
                </div>

                <button
                  v-if="!isVip"
                  type="button"
                  class="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-700 hover:bg-blue-50/80 hover:text-[#2563eb] transition-colors"
                  role="menuitem"
                  @click="handleUpgradeClick"
                >
                  <svg class="w-4 h-4 text-amber-500 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                  开通 VIP
                </button>

                <button
                  type="button"
                  class="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
                  role="menuitem"
                  @click="handleLogout"
                >
                  <svg class="w-4 h-4 text-slate-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  退出登录
                </button>
              </div>
            </Transition>
          </div>

          <!-- Not logged in -->
          <template v-else>
            <button
              type="button"
              class="text-xs sm:text-sm font-medium text-slate-600 hover:text-[#2563eb] px-3 py-2 rounded-lg hover:bg-slate-50 transition-colors"
              @click="emit('login')"
            >
              登录
            </button>
          </template>

          <button
            type="button"
            class="md:hidden p-2 text-gray-500 rounded-lg hover:bg-gray-50"
            @click="mobileOpen = !mobileOpen"
            aria-label="菜单"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path v-if="!mobileOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Mobile menu -->
      <div v-if="mobileOpen" class="md:hidden pb-4 space-y-1 border-t border-gray-100 mt-px pt-3">
        <a href="#features" class="block px-3 py-2.5 text-sm font-medium text-gray-600 hover:text-[#2563eb] rounded-lg hover:bg-blue-50/80" @click="mobileOpen = false">功能特性</a>
        <a href="#pricing" class="block px-3 py-2.5 text-sm font-medium text-gray-600 hover:text-[#2563eb] rounded-lg hover:bg-blue-50/80" @click="mobileOpen = false">套餐价格</a>
        <a href="#platforms" class="block px-3 py-2.5 text-sm font-medium text-gray-600 hover:text-[#2563eb] rounded-lg hover:bg-blue-50/80" @click="mobileOpen = false">支持平台</a>
        <template v-if="isLoggedIn">
          <div class="px-3 py-2 text-xs text-slate-500 border-t border-slate-100 mt-2 pt-3">
            {{ maskedEmail }} · {{ isVip ? 'VIP 会员' : '免费用户' }}
          </div>
          <button v-if="!isVip" type="button" class="block w-full text-left px-3 py-2.5 text-sm font-medium text-[#2563eb] rounded-lg hover:bg-blue-50/80" @click="handleUpgradeClick">开通 VIP</button>
          <button type="button" class="block w-full text-left px-3 py-2.5 text-sm font-medium text-gray-600 rounded-lg hover:bg-gray-50" @click="handleLogout">退出登录</button>
        </template>
        <button v-else type="button" class="block w-full text-left px-3 py-2.5 text-sm font-medium text-[#2563eb] rounded-lg hover:bg-blue-50/80" @click="emit('login'); mobileOpen = false">登录</button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useAuth } from '../composables/useAuth.js'

const emit = defineEmits(['login', 'upgrade'])

const mobileOpen = ref(false)
const userMenuOpen = ref(false)
const menuRoot = ref(null)

const { isLoggedIn, isVip, email, downloadsRemaining, downloadLimit, logout } = useAuth()

const avatarText = computed(() => {
  const e = email.value || ''
  if (!e) return '?'
  const local = e.split('@')[0] || ''
  return local.charAt(0).toUpperCase() || e.charAt(0).toUpperCase()
})

const maskedEmail = computed(() => {
  const e = email.value || ''
  const at = e.indexOf('@')
  if (at <= 0) return e
  const name = e.slice(0, at)
  const domain = e.slice(at)
  if (name.length <= 3) return `${name[0]}***${domain}`
  return `${name.slice(0, 3)}***${domain}`
})

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function closeUserMenu() {
  userMenuOpen.value = false
}

function handleUpgradeClick() {
  closeUserMenu()
  mobileOpen.value = false
  emit('upgrade')
}

function handleLogout() {
  logout()
  closeUserMenu()
  mobileOpen.value = false
}

function onDocumentClick(e) {
  if (!userMenuOpen.value) return
  const root = menuRoot.value
  if (root && !root.contains(e.target)) {
    closeUserMenu()
  }
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocumentClick)
})
</script>
