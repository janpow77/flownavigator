/**
 * Document Box API Client
 */

import { useAuthStore } from '@/stores/auth'

const API_BASE = '/api'

// --- Types ---

type DocumentCategory = 'belege' | 'bescheide' | 'korrespondenz' | 'vertraege' | 'nachweise' | 'sonstige'
type DocumentStatus = 'pending' | 'verified' | 'rejected' | 'unclear'

interface BoxDocument {
  id: string
  box_id: string
  file_name: string
  file_size: number
  mime_type: string
  category: DocumentCategory
  thumbnail_path: string | null
  uploaded_by: string
  uploaded_at: string
  manual_status: DocumentStatus | null
  manual_verified_by: string | null
  manual_verified_at: string | null
  manual_remarks: string | null
  created_at: string
  updated_at: string
}

interface DocumentBoxInfo {
  id: string
  audit_case_id: string
  ai_verification_enabled: boolean
  documents_count: number
  created_at: string
  updated_at: string
}

interface BoxDocumentListResponse {
  items: BoxDocument[]
  total: number
  page: number
  page_size: number
  pages: number
}

interface ListParams {
  category?: DocumentCategory
  status?: DocumentStatus
  page?: number
  page_size?: number
}

interface UpdateDocumentData {
  category?: DocumentCategory
  manual_status?: DocumentStatus
  manual_remarks?: string
}

// --- Helpers ---

function getAuthHeaders(): Record<string, string> {
  const authStore = useAuthStore()
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${authStore.token}`,
  }
}

function getAuthHeadersMultipart(): Record<string, string> {
  const authStore = useAuthStore()
  return {
    Authorization: `Bearer ${authStore.token}`,
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || `HTTP error ${response.status}`)
  }
  return response.json()
}

// --- API Functions ---

/**
 * List documents for an audit case
 */
export async function listDocuments(
  caseId: string,
  params: ListParams = {}
): Promise<BoxDocumentListResponse> {
  const queryParams = new URLSearchParams()

  if (params.category) queryParams.set('category', params.category)
  if (params.status) queryParams.set('status', params.status)
  if (params.page) queryParams.set('page', String(params.page))
  if (params.page_size) queryParams.set('page_size', String(params.page_size))

  const url = `${API_BASE}/audit-cases/${caseId}/documents${
    queryParams.toString() ? '?' + queryParams.toString() : ''
  }`

  const response = await fetch(url, {
    headers: getAuthHeaders(),
  })

  return handleResponse<BoxDocumentListResponse>(response)
}

/**
 * Get document box info for an audit case
 */
export async function getDocumentBoxInfo(caseId: string): Promise<DocumentBoxInfo> {
  const response = await fetch(`${API_BASE}/audit-cases/${caseId}/documents/box/info`, {
    headers: getAuthHeaders(),
  })
  return handleResponse<DocumentBoxInfo>(response)
}

/**
 * Upload a document to an audit case
 */
export async function uploadDocument(
  caseId: string,
  file: File,
  category: DocumentCategory = 'sonstige'
): Promise<BoxDocument> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('category', category)

  const response = await fetch(`${API_BASE}/audit-cases/${caseId}/documents`, {
    method: 'POST',
    headers: getAuthHeadersMultipart(),
    body: formData,
  })

  return handleResponse<BoxDocument>(response)
}

/**
 * Get document metadata
 */
export async function getDocument(caseId: string, docId: string): Promise<BoxDocument> {
  const response = await fetch(`${API_BASE}/audit-cases/${caseId}/documents/${docId}`, {
    headers: getAuthHeaders(),
  })
  return handleResponse<BoxDocument>(response)
}

/**
 * Download a document file
 */
export async function downloadDocument(caseId: string, docId: string): Promise<Blob> {
  const authStore = useAuthStore()
  const response = await fetch(`${API_BASE}/audit-cases/${caseId}/documents/${docId}/download`, {
    headers: {
      Authorization: `Bearer ${authStore.token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Failed to download document')
  }

  return response.blob()
}

/**
 * Update document metadata
 */
export async function updateDocument(
  caseId: string,
  docId: string,
  data: UpdateDocumentData
): Promise<BoxDocument> {
  const response = await fetch(`${API_BASE}/audit-cases/${caseId}/documents/${docId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })

  return handleResponse<BoxDocument>(response)
}

/**
 * Delete a document
 */
export async function deleteDocument(caseId: string, docId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/audit-cases/${caseId}/documents/${docId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to delete' }))
    throw new Error(error.detail)
  }
}

// --- Category Labels ---

export const CATEGORY_LABELS: Record<DocumentCategory, string> = {
  belege: 'Belege',
  bescheide: 'Bescheide',
  korrespondenz: 'Korrespondenz',
  vertraege: 'Vertr\u00e4ge',
  nachweise: 'Nachweise',
  sonstige: 'Sonstige',
}

export const STATUS_LABELS: Record<DocumentStatus, string> = {
  pending: 'Ausstehend',
  verified: 'Verifiziert',
  rejected: 'Abgelehnt',
  unclear: 'Unklar',
}

export const STATUS_COLORS: Record<DocumentStatus, string> = {
  pending: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
  verified: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  rejected: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  unclear: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
}

// --- Utility Functions ---

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

/**
 * Get icon name based on mime type
 */
export function getFileIcon(mimeType: string): string {
  if (mimeType.startsWith('image/')) return 'photo'
  if (mimeType === 'application/pdf') return 'document'
  if (mimeType.includes('word') || mimeType.includes('document')) return 'document-text'
  if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return 'table-cells'
  return 'paper-clip'
}

export type { BoxDocument, DocumentBoxInfo, BoxDocumentListResponse, DocumentCategory, DocumentStatus, ListParams, UpdateDocumentData }
