/**
 * @flowaudit/validation
 * Validierungslogik für die FlowAudit Platform
 */

import { z } from 'zod'

// ============ Basis-Schemas ============

export const uuidSchema = z.string().uuid()

export const entitySchema = z.object({
  id: uuidSchema,
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
})

export const tenantEntitySchema = entitySchema.extend({
  tenantId: uuidSchema,
})

// ============ Benutzer-Validierung ============

export const userRoleSchema = z.enum([
  'system_admin',
  'group_admin',
  'authority_head',
  'team_leader',
  'auditor',
  'viewer',
])

export const userCreateSchema = z.object({
  email: z.string().email('Ungültige E-Mail-Adresse'),
  firstName: z.string().min(1, 'Vorname ist erforderlich'),
  lastName: z.string().min(1, 'Nachname ist erforderlich'),
  role: userRoleSchema,
  tenantId: uuidSchema,
})

export const userUpdateSchema = userCreateSchema.partial().extend({
  isActive: z.boolean().optional(),
})

// ============ Prüfungs-Validierung ============

export const auditStatusSchema = z.enum([
  'planned',
  'in_progress',
  'review',
  'completed',
  'archived',
])

export const findingSeveritySchema = z.enum(['low', 'medium', 'high', 'critical'])

export const systemAuditCategorySchema = z.union([
  z.literal(1),
  z.literal(2),
  z.literal(3),
  z.literal(4),
])

// ============ Betrags-Validierung ============

export const amountSchema = z.number().nonnegative('Betrag muss positiv sein')

export const currencySchema = z.enum(['EUR', 'USD', 'GBP', 'CHF'])

export const monetaryValueSchema = z.object({
  amount: amountSchema,
  currency: currencySchema.default('EUR'),
})

// ============ Datums-Validierung ============

export const dateRangeSchema = z
  .object({
    from: z.string().datetime(),
    to: z.string().datetime(),
  })
  .refine((data) => new Date(data.from) <= new Date(data.to), {
    message: 'Startdatum muss vor Enddatum liegen',
  })

// ============ Pagination ============

export const paginationSchema = z.object({
  page: z.number().int().positive().default(1),
  pageSize: z.number().int().min(1).max(100).default(20),
  sortBy: z.string().optional(),
  sortOrder: z.enum(['asc', 'desc']).default('asc'),
})

// ============ Hilfsfunktionen ============

export type ValidationResult<T> =
  | { success: true; data: T }
  | { success: false; errors: z.ZodError }

export function validate<T>(
  schema: z.ZodSchema<T>,
  data: unknown
): ValidationResult<T> {
  const result = schema.safeParse(data)
  if (result.success) {
    return { success: true, data: result.data }
  }
  return { success: false, errors: result.error }
}

export function formatValidationErrors(errors: z.ZodError): string[] {
  return errors.issues.map((issue) => {
    const path = issue.path.join('.')
    return path ? `${path}: ${issue.message}` : issue.message
  })
}

// Re-export zod for convenience
export { z }
