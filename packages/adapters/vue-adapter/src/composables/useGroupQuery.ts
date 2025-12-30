/**
 * useGroupQuery - Composable für Konzern-Abfragen
 */

import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type {
  GroupQuery,
  GroupQueryAssignment,
} from '@flowaudit/group-queries'
import {
  isOverdue,
  getSubmittedCount,
  getProgressPercentage,
  canEvaluate,
  getPendingAuthorities,
} from '@flowaudit/group-queries'

export interface UseGroupQueryReturn {
  query: Ref<GroupQuery | null>
  loading: Ref<boolean>
  error: Ref<string | null>

  isOverdue: ComputedRef<boolean>
  submittedCount: ComputedRef<number>
  progressPercentage: ComputedRef<number>
  canEvaluate: ComputedRef<boolean>
  pendingAuthorities: ComputedRef<GroupQueryAssignment[]>

  loadQuery: (id: string) => Promise<void>
  updateAssignment: (assignmentId: string, data: Partial<GroupQueryAssignment>) => Promise<void>
  submitAssignment: (assignmentId: string) => Promise<void>
  sendReminders: (authorityIds?: string[]) => Promise<void>
}

export function useGroupQuery(): UseGroupQueryReturn {
  const query = ref<GroupQuery | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isOverdueValue = computed(() =>
    query.value ? isOverdue(query.value) : false
  )

  const submittedCountValue = computed(() =>
    query.value ? getSubmittedCount(query.value) : 0
  )

  const progressPercentageValue = computed(() =>
    query.value ? getProgressPercentage(query.value) : 0
  )

  const canEvaluateValue = computed(() =>
    query.value ? canEvaluate(query.value) : false
  )

  const pendingAuthoritiesValue = computed(() =>
    query.value ? getPendingAuthorities(query.value) : []
  )

  async function loadQuery(id: string): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/group-queries/${id}`)
      if (!response.ok) {
        throw new Error('Abfrage konnte nicht geladen werden')
      }
      query.value = await response.json()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unbekannter Fehler'
    } finally {
      loading.value = false
    }
  }

  async function updateAssignment(
    assignmentId: string,
    data: Partial<GroupQueryAssignment>
  ): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/group-queries/assignments/${assignmentId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error('Aktualisierung fehlgeschlagen')
      }

      // Reload query to get updated data
      if (query.value) {
        await loadQuery(query.value.id)
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unbekannter Fehler'
    } finally {
      loading.value = false
    }
  }

  async function submitAssignment(assignmentId: string): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(
        `/api/group-queries/assignments/${assignmentId}/submit`,
        { method: 'POST' }
      )

      if (!response.ok) {
        throw new Error('Einreichung fehlgeschlagen')
      }

      if (query.value) {
        await loadQuery(query.value.id)
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unbekannter Fehler'
    } finally {
      loading.value = false
    }
  }

  async function sendReminders(authorityIds?: string[]): Promise<void> {
    if (!query.value) return

    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/group-queries/${query.value.id}/remind`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ authority_ids: authorityIds }),
      })

      if (!response.ok) {
        throw new Error('Erinnerungen konnten nicht gesendet werden')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unbekannter Fehler'
    } finally {
      loading.value = false
    }
  }

  return {
    query,
    loading,
    error,
    isOverdue: isOverdueValue,
    submittedCount: submittedCountValue,
    progressPercentage: progressPercentageValue,
    canEvaluate: canEvaluateValue,
    pendingAuthorities: pendingAuthoritiesValue,
    loadQuery,
    updateAssignment,
    submitAssignment,
    sendReminders,
  }
}
