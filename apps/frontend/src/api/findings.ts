/**
 * Findings API Client
 */

import { useAuthStore } from '@/stores/auth'

const API_BASE = '/api'

// --- Types ---

export type FindingType = 'irregularity' | 'deficiency' | 'recommendation' | 'observation'
export type FindingStatus = 'draft' | 'confirmed' | 'disputed' | 'resolved' | 'withdrawn'
export type ErrorCategory =
  | 'ineligible_expenditure'
  | 'public_procurement'
  | 'missing_documents'
  | 'calculation_error'
  | 'double_funding'
  | 'other'

export interface Finding {
  id: string
  audit_case_id: string
  finding_number: number
  finding_type: FindingType
  error_category: ErrorCategory | null
  title: string
  description: string
  financial_impact: number | null
  is_systemic: boolean
  status: FindingStatus
  response_requested: boolean
  response_deadline: string | null
  response_received: string | null
  response_received_at: string | null
  final_assessment: string | null
  corrective_action: string | null
  created_at: string
  updated_at: string
}

export interface FindingCreate {
  finding_type: FindingType
  error_category?: ErrorCategory | null
  title: string
  description: string
  financial_impact?: number | null
  is_systemic?: boolean
  response_requested?: boolean
  response_deadline?: string | null
}

export interface FindingUpdate {
  finding_type?: FindingType
  error_category?: ErrorCategory | null
  title?: string
  description?: string
  financial_impact?: number | null
  is_systemic?: boolean
  status?: FindingStatus
  response_requested?: boolean
  response_deadline?: string | null
  response_received?: string | null
  final_assessment?: string | null
  corrective_action?: string | null
}

export interface FindingsSummary {
  total: number
  by_status: Record<string, number>
  by_type: Record<string, number>
  total_financial_impact: number
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
 * List findings for an audit case
 */
export async function listFindings(
  caseId: string,
  params: { status?: FindingStatus; finding_type?: FindingType } = {}
): Promise<Finding[]> {
  const queryParams = new URLSearchParams()

  if (params.status) queryParams.set('status', params.status)
  if (params.finding_type) queryParams.set('finding_type', params.finding_type)

  const url = `${API_BASE}/audit-cases/${caseId}/findings${
    queryParams.toString() ? '?' + queryParams.toString() : ''
  }`

  const response = await fetch(url, {
    headers: getAuthHeaders(),
  })

  return handleResponse<Finding[]>(response)
}

/**
 * Create a new finding
 */
export async function createFinding(caseId: string, data: FindingCreate): Promise<Finding> {
  const response = await fetch(`${API_BASE}/audit-cases/${caseId}/findings`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })

  return handleResponse<Finding>(response)
}

/**
 * Get a specific finding
 */
export async function getFinding(caseId: string, findingId: string): Promise<Finding> {
  const response = await fetch(`${API_BASE}/audit-cases/${caseId}/findings/${findingId}`, {
    headers: getAuthHeaders(),
  })

  return handleResponse<Finding>(response)
}

/**
 * Update a finding
 */
export async function updateFinding(
  caseId: string,
  findingId: string,
  data: FindingUpdate
): Promise<Finding> {
  const response = await fetch(`${API_BASE}/audit-cases/${caseId}/findings/${findingId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })

  return handleResponse<Finding>(response)
}

/**
 * Delete a finding
 */
export async function deleteFinding(caseId: string, findingId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/audit-cases/${caseId}/findings/${findingId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to delete' }))
    throw new Error(error.detail)
  }
}

/**
 * Confirm a draft finding
 */
export async function confirmFinding(caseId: string, findingId: string): Promise<Finding> {
  const response = await fetch(`${API_BASE}/audit-cases/${caseId}/findings/${findingId}/confirm`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })

  return handleResponse<Finding>(response)
}

/**
 * Mark a finding as resolved
 */
export async function resolveFinding(
  caseId: string,
  findingId: string,
  correctiveAction?: string
): Promise<Finding> {
  const queryParams = correctiveAction ? `?corrective_action=${encodeURIComponent(correctiveAction)}` : ''
  const response = await fetch(
    `${API_BASE}/audit-cases/${caseId}/findings/${findingId}/resolve${queryParams}`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
    }
  )

  return handleResponse<Finding>(response)
}

/**
 * Get findings summary for an audit case
 */
export async function getFindingsSummary(caseId: string): Promise<FindingsSummary> {
  const response = await fetch(`${API_BASE}/audit-cases/${caseId}/findings/stats/summary`, {
    headers: getAuthHeaders(),
  })

  return handleResponse<FindingsSummary>(response)
}

// --- Labels ---

export const FINDING_TYPE_LABELS: Record<FindingType, string> = {
  irregularity: 'Unregelmäßigkeit',
  deficiency: 'Mangel',
  recommendation: 'Empfehlung',
  observation: 'Beobachtung',
}

export const FINDING_STATUS_LABELS: Record<FindingStatus, string> = {
  draft: 'Entwurf',
  confirmed: 'Bestätigt',
  disputed: 'Widerspruch',
  resolved: 'Behoben',
  withdrawn: 'Zurückgezogen',
}

export const ERROR_CATEGORY_LABELS: Record<ErrorCategory, string> = {
  ineligible_expenditure: 'Nicht förderfähige Ausgaben',
  public_procurement: 'Vergabefehler',
  missing_documents: 'Fehlende Unterlagen',
  calculation_error: 'Rechenfehler',
  double_funding: 'Doppelfinanzierung',
  other: 'Sonstiges',
}

export const FINDING_TYPE_COLORS: Record<FindingType, string> = {
  irregularity: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  deficiency: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
  recommendation: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
  observation: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
}

export const FINDING_STATUS_COLORS: Record<FindingStatus, string> = {
  draft: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
  confirmed: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
  disputed: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
  resolved: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  withdrawn: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-500',
}

/**
 * Format currency amount for display
 */
export function formatCurrency(amount: number | null): string {
  if (amount === null || amount === undefined) return '-'
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
  }).format(amount)
}
