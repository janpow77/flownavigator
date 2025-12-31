/**
 * Module Converter API Client
 */

import { useAuthStore } from '@/stores/auth'
import type {
  LLMConfiguration,
  CreateLLMConfiguration,
  ModuleTemplate,
  CreateModuleTemplate,
  ModuleConversion,
  StartConversionRequest,
  GitHubIntegration,
  CreateGitHubIntegration,
  GitHubRepository,
  GitHubBranch,
  StageFilesRequest,
  StageFilesResponse,
} from '@/types/moduleConverter'

const API_BASE = '/api/modules'

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

// =============================================================================
// LLM Configuration API
// =============================================================================

export async function listLLMConfigurations(): Promise<LLMConfiguration[]> {
  const response = await fetch(`${API_BASE}/llm-config`, {
    headers: getAuthHeaders(),
  })
  return handleResponse<LLMConfiguration[]>(response)
}

export async function getLLMConfiguration(id: string): Promise<LLMConfiguration> {
  const response = await fetch(`${API_BASE}/llm-config/${id}`, {
    headers: getAuthHeaders(),
  })
  return handleResponse<LLMConfiguration>(response)
}

export async function createLLMConfiguration(data: CreateLLMConfiguration): Promise<LLMConfiguration> {
  const response = await fetch(`${API_BASE}/llm-config`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<LLMConfiguration>(response)
}

export async function updateLLMConfiguration(
  id: string,
  data: Partial<CreateLLMConfiguration>
): Promise<LLMConfiguration> {
  const response = await fetch(`${API_BASE}/llm-config/${id}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<LLMConfiguration>(response)
}

export async function deleteLLMConfiguration(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/llm-config/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Delete failed' }))
    throw new Error(error.detail || `HTTP error ${response.status}`)
  }
}

export async function testLLMConnection(id: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/llm-config/${id}/test`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  return handleResponse<{ success: boolean; message: string }>(response)
}

// =============================================================================
// Module Templates API
// =============================================================================

export async function listModuleTemplates(): Promise<ModuleTemplate[]> {
  const response = await fetch(`${API_BASE}/module-templates`, {
    headers: getAuthHeaders(),
  })
  return handleResponse<ModuleTemplate[]>(response)
}

export async function getModuleTemplate(id: string): Promise<ModuleTemplate> {
  const response = await fetch(`${API_BASE}/module-templates/${id}`, {
    headers: getAuthHeaders(),
  })
  return handleResponse<ModuleTemplate>(response)
}

export async function createModuleTemplate(data: CreateModuleTemplate): Promise<ModuleTemplate> {
  const response = await fetch(`${API_BASE}/module-templates`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<ModuleTemplate>(response)
}

export async function updateModuleTemplate(
  id: string,
  data: Partial<CreateModuleTemplate>
): Promise<ModuleTemplate> {
  const response = await fetch(`${API_BASE}/module-templates/${id}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<ModuleTemplate>(response)
}

export async function deleteModuleTemplate(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/module-templates/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Delete failed' }))
    throw new Error(error.detail || `HTTP error ${response.status}`)
  }
}

// =============================================================================
// Conversions API
// =============================================================================

export async function listConversions(params: {
  status?: string
  template_id?: string
  page?: number
  page_size?: number
} = {}): Promise<{ items: ModuleConversion[]; total: number }> {
  const queryParams = new URLSearchParams()
  if (params.status) queryParams.set('status', params.status)
  if (params.template_id) queryParams.set('template_id', params.template_id)
  if (params.page) queryParams.set('page', String(params.page))
  if (params.page_size) queryParams.set('page_size', String(params.page_size))

  const url = `${API_BASE}/conversions${queryParams.toString() ? '?' + queryParams.toString() : ''}`
  const response = await fetch(url, {
    headers: getAuthHeaders(),
  })
  return handleResponse<{ items: ModuleConversion[]; total: number }>(response)
}

export async function getConversion(id: string): Promise<ModuleConversion> {
  const response = await fetch(`${API_BASE}/conversions/${id}`, {
    headers: getAuthHeaders(),
  })
  return handleResponse<ModuleConversion>(response)
}

export async function startConversion(data: StartConversionRequest): Promise<ModuleConversion> {
  const response = await fetch(`${API_BASE}/conversions`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<ModuleConversion>(response)
}

export async function retryConversion(id: string): Promise<ModuleConversion> {
  const response = await fetch(`${API_BASE}/conversions/${id}/retry`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  return handleResponse<ModuleConversion>(response)
}

export async function cancelConversion(id: string): Promise<ModuleConversion> {
  const response = await fetch(`${API_BASE}/conversions/${id}/cancel`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  return handleResponse<ModuleConversion>(response)
}

// =============================================================================
// GitHub Integration API
// =============================================================================

export async function listGitHubIntegrations(): Promise<GitHubIntegration[]> {
  const response = await fetch(`${API_BASE}/github-integrations`, {
    headers: getAuthHeaders(),
  })
  return handleResponse<GitHubIntegration[]>(response)
}

export async function getGitHubIntegration(id: string): Promise<GitHubIntegration> {
  const response = await fetch(`${API_BASE}/github-integrations/${id}`, {
    headers: getAuthHeaders(),
  })
  return handleResponse<GitHubIntegration>(response)
}

export async function createGitHubIntegration(data: CreateGitHubIntegration): Promise<GitHubIntegration> {
  const response = await fetch(`${API_BASE}/github-integrations`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<GitHubIntegration>(response)
}

export async function updateGitHubIntegration(
  id: string,
  data: Partial<CreateGitHubIntegration>
): Promise<GitHubIntegration> {
  const response = await fetch(`${API_BASE}/github-integrations/${id}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<GitHubIntegration>(response)
}

export async function deleteGitHubIntegration(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/github-integrations/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Delete failed' }))
    throw new Error(error.detail || `HTTP error ${response.status}`)
  }
}

export async function testGitHubConnection(id: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/github-integrations/${id}/test`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  return handleResponse<{ success: boolean; message: string }>(response)
}

export async function listGitHubRepositories(integrationId: string): Promise<GitHubRepository[]> {
  const response = await fetch(`${API_BASE}/github-integrations/${integrationId}/repositories`, {
    headers: getAuthHeaders(),
  })
  return handleResponse<GitHubRepository[]>(response)
}

export async function listGitHubBranches(integrationId: string): Promise<GitHubBranch[]> {
  const response = await fetch(`${API_BASE}/github-integrations/${integrationId}/branches`, {
    headers: getAuthHeaders(),
  })
  return handleResponse<GitHubBranch[]>(response)
}

// =============================================================================
// Staging API
// =============================================================================

export async function stageFiles(data: StageFilesRequest): Promise<StageFilesResponse> {
  const response = await fetch(`${API_BASE}/staging/stage`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<StageFilesResponse>(response)
}

export async function createPullRequest(data: {
  github_integration_id: string
  branch_name: string
  title: string
  body: string
  base_branch?: string
}): Promise<{ pr_url: string; pr_number: number }> {
  const response = await fetch(`${API_BASE}/staging/pull-request`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<{ pr_url: string; pr_number: number }>(response)
}

export type {
  LLMConfiguration,
  CreateLLMConfiguration,
  ModuleTemplate,
  CreateModuleTemplate,
  ModuleConversion,
  StartConversionRequest,
  GitHubIntegration,
  CreateGitHubIntegration,
  GitHubRepository,
  GitHubBranch,
  StageFilesRequest,
  StageFilesResponse,
}
