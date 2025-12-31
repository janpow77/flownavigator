export type UserRole =
  | 'system_admin'
  | 'group_admin'
  | 'authority_head'
  | 'team_leader'
  | 'auditor'
  | 'viewer'

export interface User {
  id: string
  email: string
  firstName: string
  lastName: string
  role: UserRole
  tenantId: string
  isActive: boolean
}

export interface Tenant {
  id: string
  name: string
  type: 'group' | 'authority'
  status: 'active' | 'suspended' | 'trial'
}

export interface ApiError {
  detail: string
  code?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// Re-export preferences types
export * from './preferences'

// Re-export module converter types
export * from './moduleConverter'
