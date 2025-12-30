/**
 * useDocumentBox - Composable für Belegkasten
 */

import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type {
  DocumentBox,
  BoxDocument,
  BoxStatistics,
} from '@flowaudit/document-box'
import { calculateBoxStatistics } from '@flowaudit/document-box'

export interface UseDocumentBoxReturn {
  box: Ref<DocumentBox | null>
  documents: ComputedRef<BoxDocument[]>
  statistics: ComputedRef<BoxStatistics>
  loading: Ref<boolean>
  error: Ref<string | null>
  isAiRunning: Ref<boolean>

  loadBox: (auditCaseId: string) => Promise<void>
  uploadDocuments: (files: File[]) => Promise<void>
  verifyDocument: (
    docId: string,
    status: 'verified' | 'rejected',
    remarks?: string
  ) => Promise<void>
  runAiVerification: () => Promise<void>
  deleteDocument: (docId: string) => Promise<void>
}

export function useDocumentBox(): UseDocumentBoxReturn {
  const box = ref<DocumentBox | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const isAiRunning = ref(false)

  const documents = computed(() => box.value?.documents ?? [])

  const statistics = computed(() => {
    if (!box.value) {
      return {
        total: 0,
        verified: 0,
        rejected: 0,
        inProgress: 0,
        pending: 0,
        aiProcessed: 0,
        aiApproved: 0,
        aiRejected: 0,
        aiUnclear: 0,
        totalAmount: 0,
        verifiedAmount: 0,
        rejectedAmount: 0,
      }
    }
    return calculateBoxStatistics(box.value.documents)
  })

  async function loadBox(auditCaseId: string): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/document-boxes/${auditCaseId}`)
      if (!response.ok) {
        throw new Error('Belegkasten konnte nicht geladen werden')
      }
      box.value = await response.json()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unbekannter Fehler'
    } finally {
      loading.value = false
    }
  }

  async function uploadDocuments(files: File[]): Promise<void> {
    if (!box.value) return

    loading.value = true
    error.value = null

    try {
      const formData = new FormData()
      for (const file of files) {
        formData.append('files', file)
      }

      const response = await fetch(`/api/document-boxes/${box.value.id}/documents`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Upload fehlgeschlagen')
      }

      await loadBox(box.value.auditCaseId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unbekannter Fehler'
    } finally {
      loading.value = false
    }
  }

  async function verifyDocument(
    docId: string,
    status: 'verified' | 'rejected',
    remarks?: string
  ): Promise<void> {
    if (!box.value) return

    loading.value = true
    error.value = null

    try {
      const response = await fetch(
        `/api/document-boxes/${box.value.id}/documents/${docId}/verify`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status, remarks }),
        }
      )

      if (!response.ok) {
        throw new Error('Verifikation fehlgeschlagen')
      }

      await loadBox(box.value.auditCaseId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unbekannter Fehler'
    } finally {
      loading.value = false
    }
  }

  async function runAiVerification(): Promise<void> {
    if (!box.value) return

    isAiRunning.value = true
    error.value = null

    try {
      const response = await fetch(
        `/api/document-boxes/${box.value.id}/ai-verification`,
        { method: 'POST' }
      )

      if (!response.ok) {
        throw new Error('KI-Prüfung fehlgeschlagen')
      }

      await loadBox(box.value.auditCaseId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unbekannter Fehler'
    } finally {
      isAiRunning.value = false
    }
  }

  async function deleteDocument(docId: string): Promise<void> {
    if (!box.value) return

    loading.value = true
    error.value = null

    try {
      const response = await fetch(
        `/api/document-boxes/${box.value.id}/documents/${docId}`,
        { method: 'DELETE' }
      )

      if (!response.ok) {
        throw new Error('Löschen fehlgeschlagen')
      }

      await loadBox(box.value.auditCaseId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unbekannter Fehler'
    } finally {
      loading.value = false
    }
  }

  return {
    box,
    documents,
    statistics,
    loading,
    error,
    isAiRunning,
    loadBox,
    uploadDocuments,
    verifyDocument,
    runAiVerification,
    deleteDocument,
  }
}
