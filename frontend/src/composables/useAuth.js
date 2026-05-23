import { ref, computed } from 'vue'

const TOKEN_KEY = 'kinema_auth_token'
const USER_KEY = 'kinema_auth_user'

const token = ref(localStorage.getItem(TOKEN_KEY) || '')
const user = ref(safeParse(localStorage.getItem(USER_KEY)))

function safeParse(raw) {
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function useAuth() {
  const isLoggedIn = computed(() => !!token.value)
  const isVip = computed(() => !!user.value?.is_vip)
  const email = computed(() => user.value?.email || '')
  const downloadsRemaining = computed(() => user.value?.downloads_remaining)
  const downloadLimit = computed(() => user.value?.download_limit)

  function setSession(newToken, newUser) {
    token.value = newToken
    user.value = newUser
    localStorage.setItem(TOKEN_KEY, newToken)
    localStorage.setItem(USER_KEY, JSON.stringify(newUser))
  }

  function setUser(newUser) {
    user.value = newUser
    if (newUser) {
      localStorage.setItem(USER_KEY, JSON.stringify(newUser))
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  function getToken() {
    return token.value
  }

  return {
    token,
    user,
    isLoggedIn,
    isVip,
    email,
    downloadsRemaining,
    downloadLimit,
    setSession,
    setUser,
    logout,
    getToken,
  }
}
