/**
 * @flowaudit/document-box
 * Belegkasten mit KI-Prüfung für Vorhabenprüfungen
 */

import type { UUID } from '@flowaudit/common'

// ============ Belegkasten ============

export interface DocumentBox {
  id: UUID
  auditCaseId: UUID

  documents: BoxDocument[]

  statistics: BoxStatistics

  aiVerification: {
    enabled: boolean
    provider: 'flow_invoice' | 'custom'
    lastRunAt?: string
    config: AiVerificationConfig
  }
}

export interface AiVerificationConfig {
  autoProcess: boolean
  confidenceThreshold: number // 0-1
  features: {
    ocr: boolean
    extraction: boolean
    verification: boolean
    duplicateDetection: boolean
  }
}

// ============ Beleg ============

export type DocumentVerificationStatus = 'pending' | 'verified' | 'rejected' | 'unclear'

export interface BoxDocument {
  id: UUID
  boxId: UUID

  expenditureItemId?: UUID

  fileName: string
  fileSize: number
  mimeType: string
  storagePath: string
  thumbnailPath?: string

  uploadedBy: UUID
  uploadedAt: string

  manualVerification?: ManualVerification

  aiVerification?: AiVerificationResult

  matchedExpenditure?: {
    itemId: UUID
    invoiceNumber: string
    amount: number
    matchConfidence: number
  }
}

export interface ManualVerification {
  status: DocumentVerificationStatus
  verifiedBy?: UUID
  verifiedAt?: string
  remarks?: string
  findings?: string[]
}

// ============ KI-Prüfergebnis ============

export interface AiVerificationResult {
  id: UUID
  documentId: UUID

  processedAt: string
  processingTime: number

  extractedData: ExtractedInvoiceData

  verificationResults: VerificationResults

  warnings: AiWarning[]
  suggestions: AiSuggestion[]

  confidence: {
    extraction: number
    verification: number
    overall: number
  }
}

export interface ExtractedInvoiceData {
  invoiceNumber?: string
  invoiceDate?: string
  vendorName?: string
  vendorAddress?: string
  vendorTaxId?: string
  totalAmount?: number
  netAmount?: number
  currency?: string
  taxAmount?: number
  taxRate?: number
  lineItems?: ExtractedLineItem[]
  paymentTerms?: string
  bankDetails?: {
    iban?: string
    bic?: string
    bankName?: string
  }
}

export interface ExtractedLineItem {
  position?: number
  description: string
  quantity?: number
  unit?: string
  unitPrice?: number
  totalPrice: number
  taxRate?: number
}

export interface VerificationResults {
  formalChecks: {
    hasInvoiceNumber: boolean
    hasDate: boolean
    hasVendorInfo: boolean
    hasAmounts: boolean
    hasRequiredElements: boolean
  }

  arithmeticChecks: {
    lineItemsSum: boolean
    taxCalculation: boolean
    totalCorrect: boolean
  }

  plausibilityChecks: {
    dateInProjectPeriod: boolean
    amountWithinBudget: boolean
    vendorKnown: boolean
    duplicateDetected: boolean
  }

  overallScore: number
  riskLevel: 'low' | 'medium' | 'high'
  requiresManualReview: boolean
}

export interface AiWarning {
  code: string
  severity: 'info' | 'warning' | 'error'
  message: string
  field?: string
  suggestion?: string
}

export interface AiSuggestion {
  type: 'correction' | 'match' | 'action'
  message: string
  field?: string
  suggestedValue?: unknown
  confidence: number
}

// ============ Statistiken ============

export interface BoxStatistics {
  total: number
  verified: number
  rejected: number
  inProgress: number
  pending: number

  aiProcessed: number
  aiApproved: number
  aiRejected: number
  aiUnclear: number

  totalAmount: number
  verifiedAmount: number
  rejectedAmount: number
}

// ============ Hilfsfunktionen ============

export function calculateBoxStatistics(documents: BoxDocument[]): BoxStatistics {
  const stats: BoxStatistics = {
    total: documents.length,
    verified: 0,
    rejected: 0,
    inProgress: 0,
    pending: 0,
    aiProcessed: 0,
    aiApproved: 0,
    aiRejected: 0,
    aiUnclear: 0,
    totalAmount: 0,
    verifiedAmount: 0,
    rejectedAmount: 0,
  }

  for (const doc of documents) {
    const amount = doc.matchedExpenditure?.amount ?? 0
    stats.totalAmount += amount

    // Manuelle Verifikation
    const manualStatus = doc.manualVerification?.status
    if (manualStatus === 'verified') {
      stats.verified++
      stats.verifiedAmount += amount
    } else if (manualStatus === 'rejected') {
      stats.rejected++
      stats.rejectedAmount += amount
    } else if (manualStatus === 'unclear') {
      stats.inProgress++
    } else {
      stats.pending++
    }

    // KI-Verifikation
    if (doc.aiVerification) {
      stats.aiProcessed++
      const result = doc.aiVerification.verificationResults
      if (result.riskLevel === 'low' && !result.requiresManualReview) {
        stats.aiApproved++
      } else if (result.riskLevel === 'high') {
        stats.aiRejected++
      } else {
        stats.aiUnclear++
      }
    }
  }

  return stats
}

export function getDocumentStatus(doc: BoxDocument): DocumentVerificationStatus {
  if (doc.manualVerification?.status) {
    return doc.manualVerification.status
  }

  if (doc.aiVerification) {
    const result = doc.aiVerification.verificationResults
    if (result.riskLevel === 'low' && !result.requiresManualReview) {
      return 'verified'
    }
    if (result.riskLevel === 'high') {
      return 'rejected'
    }
    return 'unclear'
  }

  return 'pending'
}

export function needsManualReview(doc: BoxDocument): boolean {
  if (!doc.aiVerification) return true
  return doc.aiVerification.verificationResults.requiresManualReview
}

export function getVerificationScore(doc: BoxDocument): number {
  if (doc.aiVerification) {
    return doc.aiVerification.verificationResults.overallScore
  }
  return 0
}
