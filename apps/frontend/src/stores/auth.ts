import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'

const API_URL = '/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const userRole = computed(() => user.value?.role ?? null)
  const userName = computed(() =>
    user.value ? `${user.value.firstName} ${user.value.lastName}` : ''
  )

  function setAuth(newToken: string, newUser: User) {
    token.value = newToken
    user.value = newUser
    localStorage.setItem('token', newToken)
    localStorage.setItem('user', JSON.stringify(newUser))
  }

  function clearAuth() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  function checkAuth() {
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')

    if (storedToken && storedUser) {
      token.value = storedToken
      try {
        user.value = JSON.parse(storedUser)
      } catch {
        clearAuth()
      }
    }
  }

  async function login(email: string, password: string): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      const formData = new URLSearchParams()
      formData.append('username', email)
      formData.append('password', password)

      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Anmeldung fehlgeschlagen')
      }

      const data = await response.json()

      const userData: User = {
        id: data.user.id,
        email: data.user.email,
        firstName: data.user.first_name,
        lastName: data.user.last_name,
        role: data.user.role,
        tenantId: data.user.tenant_id,
        isActive: data.user.is_active,
      }

      setAuth(data.access_token, userData)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Anmeldung fehlgeschlagen'
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    clearAuth()
  }

  async function fetchCurrentUser(): Promise<void> {
    if (!token.value) return

    try {
      const response = await fetch(`${API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token.value}`,
        },
      })

      if (!response.ok) {
        clearAuth()
        return
      }

      const data = await response.json()
      user.value = {
        id: data.id,
        email: data.email,
        firstName: data.first_name,
        lastName: data.last_name,
        role: data.role,
        tenantId: data.tenant_id,
        isActive: data.is_active,
      }
    } catch {
      clearAuth()
    }
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    userRole,
    userName,
    login,
    logout,
    checkAuth,
    fetchCurrentUser,
  }
})
