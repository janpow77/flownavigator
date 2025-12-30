/**
 * Audit Cases API Client
 */

import { useAuthStore } from '@/stores/auth'

const API_BASE = '/api'

interface AuditCase {
  id: string
  tenant_id: string
  fiscal_year_id: string | null
  case_number: string
  external_id: string | null
  project_name: string
  beneficiary_name: string
  approved_amount: number | null
  audited_amount: number | null
  irregular_amount: number | null
  status: string
  audit_type: string
  audit_start_date: string | null
  audit_end_date: string | null
  primary_auditor_id: string | null
  secondary_auditor_id: string | null
  team_leader_id: string | null
  result: string | null
  is_sample: boolean
  requires_follow_up: boolean
  custom_data: Record<string, unknown>
  internal_notes: string | null
  created_at: string
  updated_at: string
}

interface AuditCaseListResponse {
  items: AuditCase[]
  total: number
  page: number
  page_size: number
  pages: number
}

interface AuditCaseStatistics {
  total: number
  by_status: Record<string, number>
  by_result: Record<string, number>
  by_type: Record<string, number>
  total_audited_amount: number
  total_irregular_amount: number
  error_rate: number
}

interface ListParams {
  page?: number
  page_size?: number
  status?: string
  audit_type?: string
  search?: string
  fiscal_year_id?: string
}

interface CreateAuditCaseData {
  case_number: string
  project_name: string
  beneficiary_name: string
  external_id?: string
  audit_type?: string
  approved_amount?: number
  audited_amount?: number
  audit_start_date?: string
  audit_end_date?: string
  primary_auditor_id?: string
  secondary_auditor_id?: string
  team_leader_id?: string
  fiscal_year_id?: string
  is_sample?: boolean
  custom_data?: Record<string, unknown>
  internal_notes?: string
}

function getAuthHeaders(): Record<string, string> {
  const authStore = useAuthStore()
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authStore.token}`,
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || `HTTP error ${response.status}`)
  }
  return response.json()
}

export async function listAuditCases(params: ListParams = {}): Promise<AuditCaseListResponse> {
  const queryParams = new URLSearchParams()

  if (params.page) queryParams.set('page', String(params.page))
  if (params.page_size) queryParams.set('page_size', String(params.page_size))
  if (params.status) queryParams.set('status', params.status)
  if (params.audit_type) queryParams.set('audit_type', params.audit_type)
  if (params.search) queryParams.set('search', params.search)
  if (params.fiscal_year_id) queryParams.set('fiscal_year_id', params.fiscal_year_id)

  const url = `${API_BASE}/audit-cases${queryParams.toString() ? '?' + queryParams.toString() : ''}`
  const response = await fetch(url, {
    headers: getAuthHeaders(),
  })

  return handleResponse<AuditCaseListResponse>(response)
}

export async function getAuditCase(id: string): Promise<AuditCase> {
  const response = await fetch(`${API_BASE}/audit-cases/${id}`, {
    headers: getAuthHeaders(),
  })
  return handleResponse<AuditCase>(response)
}

export async function createAuditCase(data: CreateAuditCaseData): Promise<AuditCase> {
  const response = await fetch(`${API_BASE}/audit-cases`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<AuditCase>(response)
}

export async function updateAuditCase(id: string, data: Partial<CreateAuditCaseData>): Promise<AuditCase> {
  const response = await fetch(`${API_BASE}/audit-cases/${id}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<AuditCase>(response)
}

export async function deleteAuditCase(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/audit-cases/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Delete failed' }))
    throw new Error(error.detail || `HTTP error ${response.status}`)
  }
}

export async function getAuditStatistics(fiscal_year_id?: string): Promise<AuditCaseStatistics> {
  const url = fiscal_year_id
    ? `${API_BASE}/audit-cases/statistics?fiscal_year_id=${fiscal_year_id}`
    : `${API_BASE}/audit-cases/statistics`

  const response = await fetch(url, {
    headers: getAuthHeaders(),
  })
  return handleResponse<AuditCaseStatistics>(response)
}

export type { AuditCase, AuditCaseListResponse, AuditCaseStatistics, ListParams, CreateAuditCaseData }
