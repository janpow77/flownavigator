/**
 * Audit Logs API Client
 */

import { useAuthStore } from '@/stores/auth'

const API_BASE = '/api'

// --- Types ---

export type AuditAction =
  | 'create'
  | 'update'
  | 'delete'
  | 'status_change'
  | 'assign'
  | 'unassign'
  | 'upload'
  | 'download'
  | 'verify'
  | 'confirm'
  | 'resolve'
  | 'comment'

export interface AuditLogEntry {
  id: string
  entity_type: string
  entity_id: string
  action: AuditAction
  field_name: string | null
  old_value: string | null
  new_value: string | null
  changes: Record<string, unknown> | null
  description: string | null
  user_id: string | null
  user_email: string | null
  user_name: string | null
  created_at: string
}

export interface AuditLogListResponse {
  items: AuditLogEntry[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface AuditLogCreate {
  action: 'comment'
  description: string
}

// --- Helpers ---

function getAuthHeaders(): Record<string, string> {
  const authStore = useAuthStore()
  return {
    'Content-Type': 'application/json',
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
 * List audit logs for an audit case
 */
export async function listAuditLogs(
  caseId: string,
  params: { action?: AuditAction; page?: number; page_size?: number } = {}
): Promise<AuditLogListResponse> {
  const queryParams = new URLSearchParams()

  if (params.action) queryParams.set('action', params.action)
  if (params.page) queryParams.set('page', String(params.page))
  if (params.page_size) queryParams.set('page_size', String(params.page_size))

  const url = `${API_BASE}/audit-cases/${caseId}/history${
    queryParams.toString() ? '?' + queryParams.toString() : ''
  }`

  const response = await fetch(url, {
    headers: getAuthHeaders(),
  })

  return handleResponse<AuditLogListResponse>(response)
}

/**
 * Add a comment to an audit case
 */
export async function addComment(caseId: string, description: string): Promise<AuditLogEntry> {
  const response = await fetch(`${API_BASE}/audit-cases/${caseId}/history`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      action: 'comment',
      description,
    }),
  })

  return handleResponse<AuditLogEntry>(response)
}

// --- Labels ---

export const ACTION_LABELS: Record<AuditAction, string> = {
  create: 'Erstellt',
  update: 'Aktualisiert',
  delete: 'Gelöscht',
  status_change: 'Status geändert',
  assign: 'Zugewiesen',
  unassign: 'Zuweisung entfernt',
  upload: 'Hochgeladen',
  download: 'Heruntergeladen',
  verify: 'Verifiziert',
  confirm: 'Bestätigt',
  resolve: 'Behoben',
  comment: 'Kommentar',
}

export const ACTION_ICONS: Record<AuditAction, string> = {
  create: 'plus-circle',
  update: 'pencil',
  delete: 'trash',
  status_change: 'arrow-path',
  assign: 'user-plus',
  unassign: 'user-minus',
  upload: 'arrow-up-tray',
  download: 'arrow-down-tray',
  verify: 'check-badge',
  confirm: 'check-circle',
  resolve: 'check',
  comment: 'chat-bubble-left',
}

export const ACTION_COLORS: Record<AuditAction, string> = {
  create: 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30',
  update: 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900/30',
  delete: 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/30',
  status_change: 'text-purple-600 bg-purple-100 dark:text-purple-400 dark:bg-purple-900/30',
  assign: 'text-cyan-600 bg-cyan-100 dark:text-cyan-400 dark:bg-cyan-900/30',
  unassign: 'text-orange-600 bg-orange-100 dark:text-orange-400 dark:bg-orange-900/30',
  upload: 'text-indigo-600 bg-indigo-100 dark:text-indigo-400 dark:bg-indigo-900/30',
  download: 'text-teal-600 bg-teal-100 dark:text-teal-400 dark:bg-teal-900/30',
  verify: 'text-emerald-600 bg-emerald-100 dark:text-emerald-400 dark:bg-emerald-900/30',
  confirm: 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30',
  resolve: 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30',
  comment: 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-800',
}

/**
 * Format date/time for display
 */
export function formatDateTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Format relative time
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Gerade eben'
  if (diffMins < 60) return `vor ${diffMins} Min.`
  if (diffHours < 24) return `vor ${diffHours} Std.`
  if (diffDays < 7) return `vor ${diffDays} Tagen`

  return date.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

/**
 * Get a human-readable description for a log entry
 */
export function getLogDescription(log: AuditLogEntry): string {
  if (log.description) {
    return log.description
  }

  const actionLabel = ACTION_LABELS[log.action] || log.action

  if (log.field_name) {
    if (log.old_value && log.new_value) {
      return `${actionLabel}: ${log.field_name} von "${log.old_value}" zu "${log.new_value}"`
    }
    return `${actionLabel}: ${log.field_name}`
  }

  return actionLabel
}
