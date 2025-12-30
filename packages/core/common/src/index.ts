/**
 * @flowaudit/common
 * Gemeinsame Typen, Utilities und Konstanten für die FlowAudit Platform
 */

// ============ Basis-Typen ============

export type UUID = string

export interface Entity {
  id: UUID
  createdAt: string
  updatedAt: string
}

export interface TenantEntity extends Entity {
  tenantId: UUID
}

// ============ Mandanten ============

export type TenantType = 'group' | 'authority'

export interface Tenant extends Entity {
  name: string
  type: TenantType
  parentId?: UUID // Bei authority: Zugehöriger Konzern
  status: 'active' | 'suspended' | 'trial'
}

// ============ Benutzer ============

export type UserRole =
  | 'system_admin'
  | 'group_admin'
  | 'authority_head'
  | 'team_leader'
  | 'auditor'
  | 'viewer'

export interface User extends TenantEntity {
  email: string
  firstName: string
  lastName: string
  role: UserRole
  isActive: boolean
  lastLoginAt?: string
}

// ============ Status-Typen ============

export type AuditStatus =
  | 'planned'
  | 'in_progress'
  | 'review'
  | 'completed'
  | 'archived'

export type FindingSeverity = 'low' | 'medium' | 'high' | 'critical'

// ============ Prüfungskategorien ============

export type SystemAuditCategory = 1 | 2 | 3 | 4

export const SYSTEM_AUDIT_CATEGORY_LABELS: Record<SystemAuditCategory, string> = {
  1: 'System funktioniert gut',
  2: 'Verbesserungen nötig',
  3: 'Erhebliche Mängel',
  4: 'System funktioniert nicht',
}

export const SYSTEM_AUDIT_CATEGORY_COLORS: Record<SystemAuditCategory, string> = {
  1: '#22c55e', // Grün
  2: '#eab308', // Gelb
  3: '#f97316', // Orange
  4: '#ef4444', // Rot
}

// ============ Pagination ============

export interface PaginationParams {
  page: number
  pageSize: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// ============ API Response ============

export interface ApiResponse<T> {
  data: T
  success: boolean
  message?: string
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

// ============ Utilities ============

export function formatDate(date: string | Date, locale = 'de-DE'): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString(locale, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

export function formatDateTime(date: string | Date, locale = 'de-DE'): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleString(locale, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatCurrency(
  amount: number,
  currency = 'EUR',
  locale = 'de-DE'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
  }).format(amount)
}

export function formatPercent(
  value: number,
  decimals = 2,
  locale = 'de-DE'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value / 100)
}

export function generateId(): UUID {
  return crypto.randomUUID()
}

export function isEmpty(value: unknown): boolean {
  if (value === null || value === undefined) return true
  if (typeof value === 'string') return value.trim() === ''
  if (Array.isArray(value)) return value.length === 0
  if (typeof value === 'object') return Object.keys(value).length === 0
  return false
}

export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj))
}
