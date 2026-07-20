import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'

export interface UserInfo {
  id: number
  username: string
  role: 'admin' | 'user'
  created_at?: string
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string>(localStorage.getItem('access_token') || '')
  const refreshToken = ref<string>(localStorage.getItem('refresh_token') || '')
  const user = ref<UserInfo | null>(JSON.parse(localStorage.getItem('user') || 'null'))

  // Getters
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // Actions
  async function login(username: string, password: string) {
    const res = await authApi.login(username, password)
    setAuth(res.access_token, res.refresh_token, res.user)
  }

  async function register(username: string, password: string) {
    await authApi.register(username, password)
  }

  function setAuth(accessToken: string, refreshTkn: string, userInfo: UserInfo) {
    token.value = accessToken
    refreshToken.value = refreshTkn
    user.value = userInfo
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshTkn)
    localStorage.setItem('user', JSON.stringify(userInfo))
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  async function fetchUserInfo() {
    try {
      const info = await authApi.getMe()
      user.value = info
      localStorage.setItem('user', JSON.stringify(info))
    } catch {
      logout()
    }
  }

  async function changePassword(oldPassword: string, newPassword: string) {
    await authApi.changePassword(oldPassword, newPassword)
  }

  return {
    token,
    refreshToken,
    user,
    isLoggedIn,
    isAdmin,
    login,
    register,
    logout,
    fetchUserInfo,
    changePassword,
  }
})
