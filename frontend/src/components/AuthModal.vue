<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm"
      @click.self="emit('close')"
    >
      <div class="w-full max-w-md bg-white rounded-2xl shadow-2xl border border-slate-100 overflow-hidden">
        <div class="px-6 pt-6 pb-4 border-b border-slate-100">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-bold text-gray-900">
              {{ mode === 'register' ? '注册账号' : '登录账号' }}
            </h3>
            <button
              type="button"
              class="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-50"
              @click="emit('close')"
              aria-label="关闭"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p class="mt-1 text-sm text-gray-500">
            {{ hint || (mode === 'register' ? '注册后即可下载视频并购买 VIP' : '登录后继续下载或升级 VIP') }}
          </p>
        </div>

        <form class="px-6 py-5 space-y-4" @submit.prevent="handleSubmit">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">邮箱</label>
            <input
              v-model="email"
              type="email"
              required
              autocomplete="email"
              placeholder="you@example.com"
              class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none text-sm"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">密码</label>
            <input
              v-model="password"
              type="password"
              required
              :autocomplete="mode === 'register' ? 'new-password' : 'current-password'"
              placeholder="至少 8 位"
              class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none text-sm"
            />
          </div>

          <p v-if="error" class="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{{ error }}</p>

          <button
            type="submit"
            class="btn-primary w-full py-3 text-sm disabled:opacity-60"
            :disabled="loading"
          >
            {{ loading ? '处理中…' : (mode === 'register' ? '注册' : '登录') }}
          </button>
        </form>

        <div class="px-6 pb-6 text-center text-sm text-gray-500">
          <template v-if="mode === 'login'">
            还没有账号？
            <button type="button" class="text-blue-600 font-medium hover:underline" @click="mode = 'register'; error = ''">
              立即注册
            </button>
          </template>
          <template v-else>
            已有账号？
            <button type="button" class="text-blue-600 font-medium hover:underline" @click="mode = 'login'; error = ''">
              去登录
            </button>
          </template>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { register, login, apiErrorMessage } from '../api/index.js'
import { useAuth } from '../composables/useAuth.js'

const props = defineProps({
  visible: { type: Boolean, default: false },
  initialMode: { type: String, default: 'login' },
  hint: { type: String, default: '' },
})

const emit = defineEmits(['close', 'success'])

const { setSession } = useAuth()

const mode = ref(props.initialMode)
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

watch(
  () => props.visible,
  (v) => {
    if (v) {
      mode.value = props.initialMode
      error.value = ''
    }
  },
)

async function handleSubmit() {
  loading.value = true
  error.value = ''
  try {
    const fn = mode.value === 'register' ? register : login
    const res = await fn(email.value, password.value)
    if (res.code === 0 && res.data?.token) {
      setSession(res.data.token, res.data.user)
      emit('success', res.data.user)
      emit('close')
    } else {
      error.value = res.detail || '操作失败'
    }
  } catch (e) {
    error.value = apiErrorMessage(e)
  } finally {
    loading.value = false
  }
}
</script>
