/**
 * Checklists API Client
 */

import { useAuthStore } from '@/stores/auth'

const API_BASE = '/api'

// --- Types ---

interface QuestionOption {
  value: string
  label: string
  description?: string
}

interface Question {
  id: string
  type: string
  label: string
  description?: string
  placeholder?: string
  required?: boolean
  min_value?: number
  max_value?: number
  options?: QuestionOption[]
  condition?: Record<string, unknown>
  order: number
}

interface Section {
  id: string
  title: string
  description?: string
  questions: Question[]
  order: number
}

interface ChecklistStructure {
  settings?: {
    allow_partial_save?: boolean
    require_all_questions?: boolean
    show_progress?: boolean
  }
  sections: Section[]
}

interface ChecklistTemplate {
  id: string
  tenant_id: string
  name: string
  description: string | null
  checklist_type: string
  version: number
  is_current: boolean
  structure: ChecklistStructure
  status: string
  created_at: string
  updated_at: string
}

interface ChecklistInstance {
  id: string
  audit_case_id: string
  checklist_template_id: string | null
  checklist_type: string
  status: string
  progress: number
  total_questions: number
  answered_questions: number
  responses: Record<string, ResponseValue>
  completed_by: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
  template_name?: string
  structure?: ChecklistStructure
}

interface ResponseValue {
  value: unknown
  note?: string
  answered_at?: string
  answered_by?: string
}

interface ChecklistSummary {
  id: string
  checklist_type: string
  template_name?: string
  status: string
  progress: number
  total_questions: number
  answered_questions: number
  created_at: string
  updated_at: string
}

// --- Helper ---

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

// --- Template API ---

export async function listTemplates(params: {
  checklist_type?: string
  status?: string
  search?: string
} = {}): Promise<{ items: ChecklistTemplate[]; total: number }> {
  const queryParams = new URLSearchParams()
  if (params.checklist_type) queryParams.set('checklist_type', params.checklist_type)
  if (params.status) queryParams.set('status', params.status)
  if (params.search) queryParams.set('search', params.search)

  const url = `${API_BASE}/checklists/templates${queryParams.toString() ? '?' + queryParams.toString() : ''}`
  const response = await fetch(url, { headers: getAuthHeaders() })
  return handleResponse(response)
}

export async function getTemplate(id: string): Promise<ChecklistTemplate> {
  const response = await fetch(`${API_BASE}/checklists/templates/${id}`, {
    headers: getAuthHeaders(),
  })
  return handleResponse(response)
}

export async function createDefaultTemplates(): Promise<ChecklistTemplate[]> {
  const response = await fetch(`${API_BASE}/checklists/templates/create-defaults`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  return handleResponse(response)
}

// --- Audit Case Checklist API ---

export async function listCaseChecklists(caseId: string): Promise<ChecklistSummary[]> {
  const response = await fetch(`${API_BASE}/checklists/audit-case/${caseId}`, {
    headers: getAuthHeaders(),
  })
  return handleResponse(response)
}

export async function addChecklistToCase(
  caseId: string,
  templateId: string,
  checklistType?: string
): Promise<ChecklistInstance> {
  const response = await fetch(`${API_BASE}/checklists/audit-case/${caseId}`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      template_id: templateId,
      checklist_type: checklistType,
    }),
  })
  return handleResponse(response)
}

export async function getChecklist(caseId: string, checklistId: string): Promise<ChecklistInstance> {
  const response = await fetch(`${API_BASE}/checklists/audit-case/${caseId}/${checklistId}`, {
    headers: getAuthHeaders(),
  })
  return handleResponse(response)
}

export async function updateChecklist(
  caseId: string,
  checklistId: string,
  data: {
    responses?: Record<string, unknown>
    notes?: Record<string, string>
    status?: string
  }
): Promise<ChecklistInstance> {
  const response = await fetch(`${API_BASE}/checklists/audit-case/${caseId}/${checklistId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse(response)
}

export async function deleteChecklist(caseId: string, checklistId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/checklists/audit-case/${caseId}/${checklistId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error('Failed to delete checklist')
  }
}

export type {
  Question,
  Section,
  ChecklistStructure,
  ChecklistTemplate,
  ChecklistInstance,
  ChecklistSummary,
  ResponseValue,
}
