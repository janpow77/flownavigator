/**
 * @flowaudit/group-queries
 * Konzern-Abfragen für Prüfbehörden
 */

import type { TenantEntity, UUID } from '@flowaudit/common'

// ============ Konzern-Abfrage ============

export type GroupQueryCategory =
  | 'annual_report'        // Jahresabfrage
  | 'quarterly_report'     // Quartalsabfrage
  | 'ad_hoc'              // Ad-hoc Abfrage
  | 'system_audit_summary' // Systemprüfungs-Zusammenfassung
  | 'statistics'          // Statistische Erhebung

export type GroupQueryStatus =
  | 'draft'               // Entwurf
  | 'published'           // Veröffentlicht
  | 'in_progress'         // In Bearbeitung
  | 'evaluation'          // Auswertung läuft
  | 'completed'           // Abgeschlossen
  | 'archived'            // Archiviert

export interface GroupQuery extends TenantEntity {
  // Metadaten
  title: string
  description?: string
  category: GroupQueryCategory
  fiscalYear: number

  // Zeitraum
  publishedAt?: string
  deadline: string

  // Checkliste
  checklistTemplateId: UUID
  checklistVersion: number

  // Konfiguration
  config: GroupQueryConfig

  // Status
  status: GroupQueryStatus

  // Zuweisungen
  assignments: GroupQueryAssignment[]
}

export interface GroupQueryConfig {
  evaluationTrigger: 'on_submission' | 'after_deadline' | 'manual'

  requiredAttachments: AttachmentRequirement[]

  reminderSettings: {
    enabled: boolean
    daysBefore: number[]
    sendToTeamLeader: boolean
  }

  validationRules: ValidationRule[]

  aggregationConfig?: AggregationConfig
}

export interface AttachmentRequirement {
  id: string
  name: string
  description?: string
  fileTypes: string[]
  required: boolean
  maxSize: number // in MB
}

export interface ValidationRule {
  field: string
  rule: 'required' | 'min' | 'max' | 'pattern'
  value: unknown
  message: string
}

export interface AggregationConfig {
  groupBy: string[]
  sumFields: string[]
  avgFields: string[]
  countFields: string[]
}

// ============ Zuweisung ============

export type AssignmentStatus =
  | 'pending'              // Nicht begonnen
  | 'in_progress'          // In Bearbeitung
  | 'ready_for_review'     // Bereit zur internen Prüfung
  | 'submitted'            // Eingereicht
  | 'returned'             // Zurückgewiesen (Nachbesserung)
  | 'accepted'             // Akzeptiert

export interface GroupQueryAssignment {
  id: UUID
  queryId: UUID
  authorityId: UUID
  authorityName?: string

  status: AssignmentStatus
  progress: number

  assignedAt: string
  startedAt?: string
  submittedAt?: string

  responseId?: UUID

  attachments: GroupQueryAttachment[]

  remarks?: string
  internalNotes?: string
}

export interface GroupQueryAttachment {
  id: UUID
  assignmentId: UUID
  requirementId?: UUID

  fileName: string
  fileSize: number
  mimeType: string
  storagePath: string

  uploadedBy: UUID
  uploadedAt: string

  verificationStatus?: 'pending' | 'verified' | 'rejected'
  verifiedBy?: UUID
  verifiedAt?: string
}

// ============ Antwort ============

export interface GroupQueryResponse {
  id: UUID
  assignmentId: UUID

  checklistData: Record<string, unknown>

  summaryData: {
    totalOperations?: number
    totalAmount?: number
    errorRate?: number
    findingsCount?: number
    [key: string]: unknown
  }

  versions: ResponseVersion[]
  currentVersion: number

  submittedBy: UUID
  submittedAt: string

  confirmation?: {
    confirmedBy: UUID
    confirmedAt: string
    digitalSignature?: string
  }
}

export interface ResponseVersion {
  version: number
  data: Record<string, unknown>
  savedAt: string
  savedBy: UUID
}

// ============ Auswertung ============

export interface GroupQueryEvaluation {
  id: UUID
  queryId: UUID

  createdAt: string
  createdBy: UUID

  includedAssignments: UUID[]
  excludedAssignments: UUID[]

  results: EvaluationResults

  comparisons: AuthorityComparison[]

  trends?: TrendAnalysis
}

export interface EvaluationResults {
  totalAuthorities: number
  respondedAuthorities: number
  responseRate: number

  aggregatedData: {
    totalOperations: number
    totalAuditedAmount: number
    totalErrors: number
    weightedErrorRate: number

    byFund: Record<string, FundSummary>
    byErrorCategory: Record<string, number>
    byAuditType: Record<string, AuditTypeSummary>
  }

  statistics: {
    mean: number
    median: number
    stdDev: number
    min: number
    max: number
    quartiles: [number, number, number]
  }
}

export interface FundSummary {
  operations: number
  amount: number
  errors: number
  errorRate: number
}

export interface AuditTypeSummary {
  count: number
  amount: number
  findingsCount: number
}

export interface AuthorityComparison {
  authorityId: UUID
  authorityName: string

  metrics: {
    operationsCount: number
    auditedAmount: number
    errorRate: number
    findingsCount: number
    completionRate: number
  }

  deviations: {
    errorRateDeviation: number
    amountDeviation: number
  }

  rankings: {
    byErrorRate: number
    byVolume: number
    byCompleteness: number
  }
}

export interface TrendAnalysis {
  years: number[]
  errorRates: number[]
  operationCounts: number[]
  amounts: number[]
  trend: 'improving' | 'stable' | 'declining'
}

// ============ Hilfsfunktionen ============

export function calculateProgress(assignment: GroupQueryAssignment): number {
  return assignment.progress
}

export function isOverdue(query: GroupQuery): boolean {
  return new Date(query.deadline) < new Date()
}

export function getSubmittedCount(query: GroupQuery): number {
  return query.assignments.filter(
    (a) => a.status === 'submitted' || a.status === 'accepted'
  ).length
}

export function getProgressPercentage(query: GroupQuery): number {
  if (query.assignments.length === 0) return 0
  return Math.round(
    (getSubmittedCount(query) / query.assignments.length) * 100
  )
}

export function canEvaluate(query: GroupQuery): boolean {
  const config = query.config

  switch (config.evaluationTrigger) {
    case 'manual':
      return true
    case 'after_deadline':
      return isOverdue(query)
    case 'on_submission':
      return getSubmittedCount(query) > 0
    default:
      return false
  }
}

export function getPendingAuthorities(query: GroupQuery): GroupQueryAssignment[] {
  return query.assignments.filter(
    (a) => a.status === 'pending' || a.status === 'in_progress'
  )
}
