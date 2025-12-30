/**
 * useApi - Basis-Composable für API-Aufrufe
 */

import { ref, type Ref } from 'vue'
import type { ApiResponse, ApiError } from '@flowaudit/common'

export interface UseApiOptions {
  baseUrl?: string
  headers?: Record<string, string>
}

export interface UseApiReturn<T> {
  data: Ref<T | null>
  error: Ref<ApiError | null>
  loading: Ref<boolean>
  execute: () => Promise<void>
}

export function useApi<T>(
  fetcher: () => Promise<ApiResponse<T>>,
  _options: UseApiOptions = {}
): UseApiReturn<T> {
  const data = ref<T | null>(null) as Ref<T | null>
  const error = ref<ApiError | null>(null)
  const loading = ref(false)

  async function execute(): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const response = await fetcher()
      if (response.success) {
        data.value = response.data
      } else {
        error.value = {
          code: 'API_ERROR',
          message: response.message || 'Ein Fehler ist aufgetreten',
        }
      }
    } catch (err) {
      error.value = {
        code: 'NETWORK_ERROR',
        message: err instanceof Error ? err.message : 'Netzwerkfehler',
      }
    } finally {
      loading.value = false
    }
  }

  return {
    data,
    error,
    loading,
    execute,
  }
}

export function createApiClient(baseUrl: string) {
  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  function setAuthToken(token: string) {
    defaultHeaders['Authorization'] = `Bearer ${token}`
  }

  function removeAuthToken() {
    delete defaultHeaders['Authorization']
  }

  async function request<T>(
    method: string,
    path: string,
    body?: unknown
  ): Promise<ApiResponse<T>> {
    const response = await fetch(`${baseUrl}${path}`, {
      method,
      headers: defaultHeaders,
      body: body ? JSON.stringify(body) : undefined,
    })

    const data = await response.json()

    if (!response.ok) {
      return {
        data: null as T,
        success: false,
        message: data.detail || data.message || 'Fehler',
      }
    }

    return {
      data,
      success: true,
    }
  }

  return {
    setAuthToken,
    removeAuthToken,
    get: <T>(path: string) => request<T>('GET', path),
    post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
    put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body),
    patch: <T>(path: string, body?: unknown) => request<T>('PATCH', path, body),
    delete: <T>(path: string) => request<T>('DELETE', path),
  }
}
