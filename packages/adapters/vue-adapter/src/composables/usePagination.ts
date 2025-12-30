/**
 * usePagination - Composable für Paginierung
 */

import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type { PaginationParams, PaginatedResponse } from '@flowaudit/common'

export interface UsePaginationOptions {
  initialPage?: number
  initialPageSize?: number
  initialSortBy?: string
  initialSortOrder?: 'asc' | 'desc'
}

export interface UsePaginationReturn<T> {
  items: Ref<T[]>
  total: Ref<number>
  page: Ref<number>
  pageSize: Ref<number>
  totalPages: ComputedRef<number>
  sortBy: Ref<string | undefined>
  sortOrder: Ref<'asc' | 'desc'>
  loading: Ref<boolean>
  error: Ref<string | null>

  params: ComputedRef<PaginationParams>
  hasNextPage: ComputedRef<boolean>
  hasPrevPage: ComputedRef<boolean>

  setPage: (newPage: number) => void
  setPageSize: (newSize: number) => void
  setSort: (field: string, order?: 'asc' | 'desc') => void
  nextPage: () => void
  prevPage: () => void
  refresh: () => Promise<void>

  loadData: (fetcher: (params: PaginationParams) => Promise<PaginatedResponse<T>>) => void
}

export function usePagination<T>(
  options: UsePaginationOptions = {}
): UsePaginationReturn<T> {
  const {
    initialPage = 1,
    initialPageSize = 20,
    initialSortBy,
    initialSortOrder = 'asc',
  } = options

  const items = ref<T[]>([]) as Ref<T[]>
  const total = ref(0)
  const page = ref(initialPage)
  const pageSize = ref(initialPageSize)
  const sortBy = ref<string | undefined>(initialSortBy)
  const sortOrder = ref<'asc' | 'desc'>(initialSortOrder)
  const loading = ref(false)
  const error = ref<string | null>(null)

  let currentFetcher: ((params: PaginationParams) => Promise<PaginatedResponse<T>>) | null = null

  const totalPages = computed(() =>
    Math.ceil(total.value / pageSize.value)
  )

  const params = computed<PaginationParams>(() => ({
    page: page.value,
    pageSize: pageSize.value,
    sortBy: sortBy.value,
    sortOrder: sortOrder.value,
  }))

  const hasNextPage = computed(() => page.value < totalPages.value)
  const hasPrevPage = computed(() => page.value > 1)

  function setPage(newPage: number): void {
    if (newPage >= 1 && newPage <= totalPages.value) {
      page.value = newPage
      refresh()
    }
  }

  function setPageSize(newSize: number): void {
    pageSize.value = newSize
    page.value = 1
    refresh()
  }

  function setSort(field: string, order?: 'asc' | 'desc'): void {
    if (sortBy.value === field && !order) {
      sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortBy.value = field
      sortOrder.value = order ?? 'asc'
    }
    page.value = 1
    refresh()
  }

  function nextPage(): void {
    if (hasNextPage.value) {
      setPage(page.value + 1)
    }
  }

  function prevPage(): void {
    if (hasPrevPage.value) {
      setPage(page.value - 1)
    }
  }

  async function refresh(): Promise<void> {
    if (!currentFetcher) return

    loading.value = true
    error.value = null

    try {
      const response = await currentFetcher(params.value)
      items.value = response.items
      total.value = response.total
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Fehler beim Laden'
    } finally {
      loading.value = false
    }
  }

  function loadData(
    fetcher: (params: PaginationParams) => Promise<PaginatedResponse<T>>
  ): void {
    currentFetcher = fetcher
    refresh()
  }

  return {
    items,
    total,
    page,
    pageSize,
    totalPages,
    sortBy,
    sortOrder,
    loading,
    error,
    params,
    hasNextPage,
    hasPrevPage,
    setPage,
    setPageSize,
    setSort,
    nextPage,
    prevPage,
    refresh,
    loadData,
  }
}
