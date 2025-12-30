/**
 * @flowaudit/checklists
 * Checklisten-Modul für Prüfungen
 */

import type { TenantEntity, UUID, SystemAuditCategory } from '@flowaudit/common'

// ============ Checklisten-Typen ============

export type ChecklistType =
  | 'main'           // Hauptcheckliste
  | 'procurement'    // Vergabeprüfung
  | 'subsidy'        // Beihilfeprüfung
  | 'eligibility'    // Förderfähigkeit
  | 'system'         // Systemprüfung

export type FieldType =
  | 'text'
  | 'textarea'
  | 'number'
  | 'currency'
  | 'date'
  | 'select'
  | 'multiselect'
  | 'checkbox'
  | 'radio'
  | 'rating'         // z.B. für Systemprüfungs-Kategorien
  | 'file'

// ============ Feld-Definition ============

export interface FieldOption {
  value: string
  label: string
  description?: string
}

export interface FieldValidation {
  required?: boolean
  min?: number
  max?: number
  minLength?: number
  maxLength?: number
  pattern?: string
  patternMessage?: string
}

export interface FieldSchema {
  id: string
  name: string
  label: string
  type: FieldType
  description?: string
  placeholder?: string
  defaultValue?: unknown
  options?: FieldOption[]
  validation?: FieldValidation
  conditional?: ConditionalLogic
  reportMapping?: ReportMapping
}

export interface ConditionalLogic {
  field: string
  operator: 'equals' | 'not_equals' | 'contains' | 'greater_than' | 'less_than'
  value: unknown
}

export interface ReportMapping {
  textModule?: string
  placeholder?: string
  format?: string
}

// ============ Checklisten-Sektion ============

export interface ChecklistSection {
  id: string
  title: string
  description?: string
  order: number
  fields: FieldSchema[]
  conditional?: ConditionalLogic
}

// ============ Checklisten-Template ============

export interface ChecklistTemplate extends TenantEntity {
  name: string
  description?: string
  type: ChecklistType
  version: number
  isActive: boolean
  isLocked: boolean

  sections: ChecklistSection[]

  // Konfiguration
  config: ChecklistConfig

  // Metadaten
  createdBy: UUID
  lastModifiedBy: UUID
}

export interface ChecklistConfig {
  // Berichtsübernahme
  reportIntegration: ReportIntegrationConfig

  // Validierung
  validateOnSave: boolean
  requireAllFields: boolean

  // Bewertung (für Systemprüfungen)
  scoring?: ScoringConfig
}

export interface ReportIntegrationConfig {
  enabled: boolean
  mode: 'full' | 'summary' | 'table_only' | 'none'
  template?: string
}

export interface ScoringConfig {
  enabled: boolean
  categories: SystemAuditCategory[]
  weightedFields?: Record<string, number>
}

// ============ Ausgefüllte Checkliste ============

export interface ChecklistInstance extends TenantEntity {
  templateId: UUID
  templateVersion: number
  auditCaseId?: UUID

  // Daten
  data: Record<string, unknown>

  // Status
  status: ChecklistInstanceStatus
  completionPercentage: number

  // Bewertung
  score?: number
  category?: SystemAuditCategory

  // Zeitstempel
  startedAt?: string
  completedAt?: string

  // Bearbeiter
  assignedTo?: UUID
  completedBy?: UUID
}

export type ChecklistInstanceStatus =
  | 'draft'
  | 'in_progress'
  | 'completed'
  | 'approved'
  | 'rejected'

// ============ Hilfsfunktionen ============

export function calculateCompletionPercentage(
  template: ChecklistTemplate,
  data: Record<string, unknown>
): number {
  const requiredFields = template.sections
    .flatMap((s) => s.fields)
    .filter((f) => f.validation?.required)

  if (requiredFields.length === 0) return 100

  const completedFields = requiredFields.filter((f) => {
    const value = data[f.name]
    return value !== undefined && value !== null && value !== ''
  })

  return Math.round((completedFields.length / requiredFields.length) * 100)
}

export function validateChecklistData(
  template: ChecklistTemplate,
  data: Record<string, unknown>
): ValidationError[] {
  const errors: ValidationError[] = []

  for (const section of template.sections) {
    for (const field of section.fields) {
      const value = data[field.name]
      const validation = field.validation

      if (!validation) continue

      // Required check
      if (validation.required && (value === undefined || value === null || value === '')) {
        errors.push({
          field: field.name,
          message: `${field.label} ist erforderlich`,
        })
        continue
      }

      if (value === undefined || value === null) continue

      // Type-specific validation
      if (typeof value === 'number') {
        if (validation.min !== undefined && value < validation.min) {
          errors.push({
            field: field.name,
            message: `${field.label} muss mindestens ${validation.min} sein`,
          })
        }
        if (validation.max !== undefined && value > validation.max) {
          errors.push({
            field: field.name,
            message: `${field.label} darf maximal ${validation.max} sein`,
          })
        }
      }

      if (typeof value === 'string') {
        if (validation.minLength !== undefined && value.length < validation.minLength) {
          errors.push({
            field: field.name,
            message: `${field.label} muss mindestens ${validation.minLength} Zeichen haben`,
          })
        }
        if (validation.maxLength !== undefined && value.length > validation.maxLength) {
          errors.push({
            field: field.name,
            message: `${field.label} darf maximal ${validation.maxLength} Zeichen haben`,
          })
        }
        if (validation.pattern) {
          const regex = new RegExp(validation.pattern)
          if (!regex.test(value)) {
            errors.push({
              field: field.name,
              message: validation.patternMessage || `${field.label} hat ein ungültiges Format`,
            })
          }
        }
      }
    }
  }

  return errors
}

export interface ValidationError {
  field: string
  message: string
}

export function isFieldVisible(
  field: FieldSchema,
  data: Record<string, unknown>
): boolean {
  if (!field.conditional) return true

  const { field: condField, operator, value: condValue } = field.conditional
  const fieldValue = data[condField]

  switch (operator) {
    case 'equals':
      return fieldValue === condValue
    case 'not_equals':
      return fieldValue !== condValue
    case 'contains':
      return typeof fieldValue === 'string' && fieldValue.includes(String(condValue))
    case 'greater_than':
      return typeof fieldValue === 'number' && fieldValue > Number(condValue)
    case 'less_than':
      return typeof fieldValue === 'number' && fieldValue < Number(condValue)
    default:
      return true
  }
}
