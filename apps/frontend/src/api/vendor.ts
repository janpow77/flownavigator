/**
 * Vendor API Client (Layer 0)
 */

const API_BASE = '/api/v1'

// Types
export interface Vendor {
  id: string
  name: string
  contact_email: string
  billing_email: string
  address_street: string | null
  address_city: string | null
  address_postal_code: string | null
  address_country: string
  created_at: string
  updated_at: string
}

export interface VendorUser {
  id: string
  vendor_id: string
  email: string
  first_name: string
  last_name: string
  role: VendorRole
  is_active: boolean
  last_login_at: string | null
  created_at: string
  updated_at: string
}

export type VendorRole = 'vendor_admin' | 'vendor_support' | 'vendor_developer' | 'vendor_qa'

export interface Customer {
  id: string
  vendor_id: string | null
  tenant_id: string
  contract_number: string
  contract_start: string | null
  contract_end: string | null
  licensed_users: number
  licensed_authorities: number
  billing_contact: string | null
  billing_email: string | null
  billing_address_street: string | null
  billing_address_city: string | null
  billing_address_postal_code: string | null
  billing_address_country: string
  payment_method: string | null
  status: CustomerStatus
  created_at: string
  updated_at: string
}

export type CustomerStatus = 'active' | 'suspended' | 'trial' | 'terminated'

export interface LicenseUsage {
  id: string
  customer_id: string
  date: string
  active_users: number
  active_authorities: number
  created_at: string
}

export interface LicenseAlert {
  id: string
  customer_id: string
  alert_type: 'warning' | 'critical' | 'exceeded'
  message: string
  threshold_percent: number
  current_percent: number
  acknowledged: boolean
  acknowledged_at: string | null
  acknowledged_by: string | null
  created_at: string
}

export interface Module {
  id: string
  name: string
  version: string
  description: string | null
  status: ModuleStatus
  developed_by: string | null
  released_at: string | null
  dependencies: string[] | null
  min_system_version: string | null
  feature_flags: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export type ModuleStatus = 'development' | 'testing' | 'released' | 'deprecated'

export interface ModuleDeployment {
  id: string
  module_id: string
  customer_id: string
  status: DeploymentStatus
  deployed_at: string | null
  deployed_by: string | null
  deployed_version: string
  previous_version: string | null
  error_message: string | null
  created_at: string
}

export type DeploymentStatus = 'pending' | 'deploying' | 'deployed' | 'failed' | 'rolled_back'

export interface ReleaseNote {
  id: string
  module_id: string
  version: string
  title: string
  changes: string[] | null
  breaking_changes: string[] | null
  published_at: string
  created_at: string
}

export interface CustomerWithLicenses extends Customer {
  license_usages: LicenseUsage[]
  license_alerts: LicenseAlert[]
  current_active_users: number
  current_active_authorities: number
  user_license_percent: number
  authority_license_percent: number
}

export interface LicenseHistory {
  history: LicenseUsage[]
  licensed_users: number
  licensed_authorities: number
  current_user_percent: number
  current_authority_percent: number
}

// Helper functions
function getVendorToken(): string | null {
  return localStorage.getItem('vendor_token')
}

export function setVendorToken(token: string): void {
  localStorage.setItem('vendor_token', token)
}

export function clearVendorToken(): void {
  localStorage.removeItem('vendor_token')
}

function getAuthHeaders(): Record<string, string> {
  const token = getVendorToken()
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || `HTTP error ${response.status}`)
  }
  return response.json()
}

// Authentication
export async function vendorLogin(email: string, password: string): Promise<{ access_token: string; user: VendorUser }> {
  const formData = new URLSearchParams()
  formData.append('username', email)
  formData.append('password', password)

  const response = await fetch(`${API_BASE}/vendor/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData,
  })

  const result = await handleResponse<{ access_token: string; user: VendorUser }>(response)
  setVendorToken(result.access_token)
  return result
}

// Vendor API
export async function getVendor(): Promise<Vendor> {
  const response = await fetch(`${API_BASE}/vendor`, {
    headers: getAuthHeaders(),
  })
  return handleResponse<Vendor>(response)
}

export async function updateVendor(data: Partial<Vendor>): Promise<Vendor> {
  const response = await fetch(`${API_BASE}/vendor`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<Vendor>(response)
}

// Vendor Users API
export async function listVendorUsers(): Promise<{ users: VendorUser[]; total: number }> {
  const response = await fetch(`${API_BASE}/vendor/users`, {
    headers: getAuthHeaders(),
  })
  return handleResponse<{ users: VendorUser[]; total: number }>(response)
}

export async function createVendorUser(data: {
  email: string
  password: string
  first_name: string
  last_name: string
  role: VendorRole
}): Promise<VendorUser> {
  const response = await fetch(`${API_BASE}/vendor/users`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<VendorUser>(response)
}

export async function updateVendorUser(userId: string, data: Partial<VendorUser & { password?: string }>): Promise<VendorUser> {
  const response = await fetch(`${API_BASE}/vendor/users/${userId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<VendorUser>(response)
}

export async function deactivateVendorUser(userId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/vendor/users/${userId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Delete failed' }))
    throw new Error(error.detail || `HTTP error ${response.status}`)
  }
}

// Customers API
export async function listCustomers(params: {
  skip?: number
  limit?: number
  status?: CustomerStatus
} = {}): Promise<{ customers: Customer[]; total: number }> {
  const queryParams = new URLSearchParams()
  if (params.skip !== undefined) queryParams.set('skip', String(params.skip))
  if (params.limit !== undefined) queryParams.set('limit', String(params.limit))
  if (params.status) queryParams.set('status', params.status)

  const url = `${API_BASE}/customers${queryParams.toString() ? '?' + queryParams.toString() : ''}`
  const response = await fetch(url, {
    headers: getAuthHeaders(),
  })
  return handleResponse<{ customers: Customer[]; total: number }>(response)
}

export async function getCustomer(customerId: string): Promise<CustomerWithLicenses> {
  const response = await fetch(`${API_BASE}/customers/${customerId}`, {
    headers: getAuthHeaders(),
  })
  return handleResponse<CustomerWithLicenses>(response)
}

export async function createCustomer(data: {
  contract_number: string
  tenant_name: string
  tenant_type?: 'group' | 'authority'
  licensed_users: number
  licensed_authorities: number
  contract_start?: string
  contract_end?: string
  billing_contact?: string
  billing_email?: string
  status?: CustomerStatus
}): Promise<Customer> {
  const response = await fetch(`${API_BASE}/customers`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<Customer>(response)
}

export async function updateCustomer(customerId: string, data: Partial<Customer>): Promise<Customer> {
  const response = await fetch(`${API_BASE}/customers/${customerId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<Customer>(response)
}

export async function terminateCustomer(customerId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/customers/${customerId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Delete failed' }))
    throw new Error(error.detail || `HTTP error ${response.status}`)
  }
}

export async function getLicenseHistory(customerId: string, days = 30): Promise<LicenseHistory> {
  const response = await fetch(`${API_BASE}/customers/${customerId}/licenses?days=${days}`, {
    headers: getAuthHeaders(),
  })
  return handleResponse<LicenseHistory>(response)
}

export async function adjustLicenses(customerId: string, data: {
  licensed_users?: number
  licensed_authorities?: number
}): Promise<Customer> {
  const response = await fetch(`${API_BASE}/customers/${customerId}/licenses/adjust`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<Customer>(response)
}

export async function getCustomerAuthorities(customerId: string): Promise<{
  authorities: Array<{ id: string; name: string; status: string; created_at: string }>
  total: number
}> {
  const response = await fetch(`${API_BASE}/customers/${customerId}/authorities`, {
    headers: getAuthHeaders(),
  })
  return handleResponse(response)
}

export async function acknowledgeAlert(customerId: string, alertId: string): Promise<LicenseAlert> {
  const response = await fetch(`${API_BASE}/customers/${customerId}/alerts/${alertId}/acknowledge`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  return handleResponse<LicenseAlert>(response)
}

// Modules API
export async function listModules(params: {
  skip?: number
  limit?: number
  status?: ModuleStatus
} = {}): Promise<{ modules: Module[]; total: number }> {
  const queryParams = new URLSearchParams()
  if (params.skip !== undefined) queryParams.set('skip', String(params.skip))
  if (params.limit !== undefined) queryParams.set('limit', String(params.limit))
  if (params.status) queryParams.set('status', params.status)

  const url = `${API_BASE}/modules${queryParams.toString() ? '?' + queryParams.toString() : ''}`
  const response = await fetch(url, {
    headers: getAuthHeaders(),
  })
  return handleResponse<{ modules: Module[]; total: number }>(response)
}

export async function getModule(moduleId: string): Promise<Module & {
  deployments: ModuleDeployment[]
  release_notes: ReleaseNote[]
}> {
  const response = await fetch(`${API_BASE}/modules/${moduleId}`, {
    headers: getAuthHeaders(),
  })
  return handleResponse(response)
}

export async function createModule(data: {
  name: string
  version: string
  description?: string
  dependencies?: string[]
  min_system_version?: string
  feature_flags?: Record<string, unknown>
}): Promise<Module> {
  const response = await fetch(`${API_BASE}/modules`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<Module>(response)
}

export async function updateModule(moduleId: string, data: Partial<Module>): Promise<Module> {
  const response = await fetch(`${API_BASE}/modules/${moduleId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<Module>(response)
}

export async function releaseModule(moduleId: string, releaseNote?: {
  version: string
  title: string
  changes: string[]
  breaking_changes?: string[]
}): Promise<Module> {
  const response = await fetch(`${API_BASE}/modules/${moduleId}/release`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: releaseNote ? JSON.stringify(releaseNote) : undefined,
  })
  return handleResponse<Module>(response)
}

export async function deployModule(moduleId: string, customerId: string): Promise<ModuleDeployment> {
  const response = await fetch(`${API_BASE}/modules/${moduleId}/deploy/${customerId}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  return handleResponse<ModuleDeployment>(response)
}

export async function rollbackModule(moduleId: string, customerId: string): Promise<ModuleDeployment> {
  const response = await fetch(`${API_BASE}/modules/${moduleId}/rollback/${customerId}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  return handleResponse<ModuleDeployment>(response)
}

export async function listModuleDeployments(moduleId: string): Promise<{ deployments: ModuleDeployment[]; total: number }> {
  const response = await fetch(`${API_BASE}/modules/${moduleId}/deployments`, {
    headers: getAuthHeaders(),
  })
  return handleResponse(response)
}

export async function createReleaseNote(moduleId: string, data: {
  version: string
  title: string
  changes: string[]
  breaking_changes?: string[]
}): Promise<ReleaseNote> {
  const response = await fetch(`${API_BASE}/modules/${moduleId}/release-notes`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  return handleResponse<ReleaseNote>(response)
}
