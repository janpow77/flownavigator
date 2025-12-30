# FlowAudit Platform - Implementierungsplan

> Umfassende Planung für Konzernansicht, Prüfer-Schreibtisch und FlowNavigator

---

## Übersicht der Module

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FlowAudit Platform                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ FlowAudit   │  │ FlowAudit   │  │ FlowAudit   │  │ FlowNavigator       │ │
│  │ Portal      │  │ Konzern     │  │ Admin       │  │ (Deployment-Tool)   │ │
│  │ (Prüfer)    │  │ (Gruppe)    │  │ (Verwaltung)│  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│         │                │                │                    │            │
│         └────────────────┴────────────────┴────────────────────┘            │
│                                    │                                        │
│                          ┌─────────▼─────────┐                              │
│                          │  @flowaudit/*     │                              │
│                          │  npm Packages     │                              │
│                          └───────────────────┘                              │
│                                                                             │
│  Zusatzmodule:                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                          │
│  │ FlowInvoice │  │ FlowReport  │  │ FlowStats   │                          │
│  │ (KI-Beleg)  │  │ (Berichte)  │  │ (Statistik) │                          │
│  └─────────────┘  └─────────────┘  └─────────────┘                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Teil 1: Konzernansicht (Group Portal)

### 1.1 Funktionsübersicht

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FlowAudit Konzern                        🔔 5   👤 Konzern-Admin   ⚙️  🌙  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ Navigation ─────────────────────────────────────────────────────────┐   │
│  │ 🏠 Dashboard │ 📋 Abfragen │ 📊 Auswertungen │ 🏢 Behörden │ ⚙️ Admin │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  📋 Konzern-Abfragen                                    [+ Neue Abfrage] │
│  │  ────────────────────────────────────────────────────────────────────│   │
│  │                                                                      │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │ Jahresabfrage 2024                              Status: Offen  │  │   │
│  │  │ Frist: 31.01.2025                                              │  │   │
│  │  │ ──────────────────────────────────────────────────────────────│  │   │
│  │  │ Eingegangen: 3/8 Behörden    ████████░░░░░░░░░░░░ 37%         │  │   │
│  │  │                                                                │  │   │
│  │  │ ✅ Prüfbehörde Bayern      Eingereicht am 15.12.2024          │  │   │
│  │  │ ✅ Prüfbehörde NRW         Eingereicht am 18.12.2024          │  │   │
│  │  │ ✅ Prüfbehörde Hessen      Eingereicht am 20.12.2024          │  │   │
│  │  │ ⏳ Prüfbehörde Sachsen     In Bearbeitung (65%)               │  │   │
│  │  │ ⏳ Prüfbehörde Baden-W.    In Bearbeitung (30%)               │  │   │
│  │  │ ○ Prüfbehörde Berlin       Nicht begonnen                     │  │   │
│  │  │ ○ Prüfbehörde Hamburg      Nicht begonnen                     │  │   │
│  │  │ ○ Prüfbehörde Niedersachs. Nicht begonnen                     │  │   │
│  │  │                                                                │  │   │
│  │  │                    [Auswertung starten] [Erinnerung senden]    │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Datenmodell

```typescript
// packages/domain/group-queries/types.ts

/**
 * Konzern-Abfrage (vom Konzern erstellte Checkliste für Prüfbehörden)
 */
export interface GroupQuery {
  id: string
  tenantId: string              // Konzern-Mandant

  // Metadaten
  title: string                 // "Jahresabfrage 2024"
  description?: string
  category: GroupQueryCategory
  fiscalYear: number

  // Zeitraum
  createdAt: string
  publishedAt?: string          // Wann veröffentlicht
  deadline: string              // Abgabefrist

  // Checkliste
  checklistTemplateId: string   // Vorlage der Checkliste
  checklistVersion: number

  // Konfiguration
  config: GroupQueryConfig

  // Status
  status: GroupQueryStatus

  // Zuweisungen
  assignments: GroupQueryAssignment[]
}

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

export interface GroupQueryConfig {
  // Wann kann der Konzern auswerten?
  evaluationTrigger: 'on_submission' | 'after_deadline' | 'manual'

  // Dateianforderungen
  requiredAttachments: AttachmentRequirement[]

  // Erinnerungen
  reminderSettings: {
    enabled: boolean
    daysBefore: number[]    // z.B. [14, 7, 3, 1]
    sendToTeamLeader: boolean
  }

  // Validierung
  validationRules: ValidationRule[]

  // Aggregation
  aggregationConfig?: AggregationConfig
}

export interface AttachmentRequirement {
  id: string
  name: string              // "Prüfbericht Q4"
  description?: string
  fileTypes: string[]       // ['.pdf', '.docx']
  required: boolean
  maxSize: number           // in MB
}

/**
 * Zuweisung einer Abfrage an eine Prüfbehörde
 */
export interface GroupQueryAssignment {
  id: string
  queryId: string
  authorityId: string       // Prüfbehörde

  // Status
  status: AssignmentStatus
  progress: number          // 0-100

  // Bearbeitung
  assignedAt: string
  startedAt?: string
  submittedAt?: string

  // Antwort
  responseId?: string       // Verweis auf ausgefüllte Checkliste

  // Dateien
  attachments: GroupQueryAttachment[]

  // Kommunikation
  remarks?: string
  internalNotes?: string    // Nur für Konzern sichtbar
}

export type AssignmentStatus =
  | 'pending'              // Nicht begonnen
  | 'in_progress'          // In Bearbeitung
  | 'ready_for_review'     // Bereit zur internen Prüfung
  | 'submitted'            // Eingereicht
  | 'returned'             // Zurückgewiesen (Nachbesserung)
  | 'accepted'             // Akzeptiert

export interface GroupQueryAttachment {
  id: string
  assignmentId: string
  requirementId?: string    // Zuordnung zu AttachmentRequirement

  fileName: string
  fileSize: number
  mimeType: string
  storagePath: string

  uploadedBy: string
  uploadedAt: string

  // Optional: Prüfstatus
  verificationStatus?: 'pending' | 'verified' | 'rejected'
  verifiedBy?: string
  verifiedAt?: string
}

/**
 * Antwort einer Prüfbehörde auf eine Konzern-Abfrage
 */
export interface GroupQueryResponse {
  id: string
  assignmentId: string

  // Ausgefüllte Checkliste
  checklistData: Record<string, any>  // JSONB

  // Aggregierte Werte (für schnelle Auswertung)
  summaryData: {
    totalOperations?: number
    totalAmount?: number
    errorRate?: number
    findingsCount?: number
    // ... weitere aggregierte Felder
  }

  // Versionen
  versions: ResponseVersion[]
  currentVersion: number

  // Abgabe
  submittedBy: string
  submittedAt: string

  // Signatur/Bestätigung
  confirmation: {
    confirmedBy: string       // Prüfbehördenleiter
    confirmedAt: string
    digitalSignature?: string
  }
}
```

### 1.3 Konzern-Auswertungen

```typescript
// packages/domain/group-queries/evaluation.ts

/**
 * Auswertung einer Konzern-Abfrage
 */
export interface GroupQueryEvaluation {
  id: string
  queryId: string

  // Zeitpunkt
  createdAt: string
  createdBy: string

  // Basis
  includedAssignments: string[]  // Welche Behörden einbezogen
  excludedAssignments: string[]  // Welche ausgeschlossen (noch nicht eingereicht)

  // Aggregierte Ergebnisse
  results: EvaluationResults

  // Vergleiche
  comparisons: AuthorityComparison[]

  // Trends (wenn Vorjahre verfügbar)
  trends?: TrendAnalysis
}

export interface EvaluationResults {
  // Übersicht
  totalAuthorities: number
  respondedAuthorities: number
  responseRate: number

  // Aggregierte Zahlen
  aggregatedData: {
    totalOperations: number
    totalAuditedAmount: number
    totalErrors: number
    weightedErrorRate: number

    // Nach Fonds
    byFund: Record<string, FundSummary>

    // Nach Fehlerart
    byErrorCategory: Record<string, number>

    // Nach Prüfungsart
    byAuditType: Record<string, AuditTypeSummary>
  }

  // Statistik
  statistics: {
    mean: number
    median: number
    stdDev: number
    min: number
    max: number
    quartiles: [number, number, number]
  }
}

export interface AuthorityComparison {
  authorityId: string
  authorityName: string

  // Kennzahlen
  metrics: {
    operationsCount: number
    auditedAmount: number
    errorRate: number
    findingsCount: number
    completionRate: number
  }

  // Abweichung vom Durchschnitt
  deviations: {
    errorRateDeviation: number      // +/- %
    amountDeviation: number
  }

  // Ranking
  rankings: {
    byErrorRate: number             // 1 = beste (niedrigste)
    byVolume: number
    byCompleteness: number
  }
}

/**
 * Auswertungs-Ansichten für den Konzern
 */
export interface EvaluationViews {
  // Übersichts-Dashboard
  dashboard: {
    kpis: KpiCard[]
    statusChart: ChartData         // Einreichungsstatus
    errorRateChart: ChartData      // Fehlerquoten-Vergleich
    trendChart: ChartData          // Entwicklung über Zeit
  }

  // Detailansichten
  authorityMatrix: {
    rows: AuthorityRow[]
    columns: MetricColumn[]
    totals: TotalRow
  }

  // Drill-Down
  drillDown: {
    byAuthority: AuthorityDetail[]
    byFund: FundDetail[]
    byErrorCategory: ErrorCategoryDetail[]
  }
}
```

### 1.4 Vue-Komponenten für Konzernansicht

```vue
<!-- apps/group-portal/src/views/GroupQueryListView.vue -->
<template>
  <div class="group-queries">
    <PageHeader :title="$t('groupQueries.title')">
      <template #actions>
        <Button @click="createQuery" variant="primary">
          <Plus class="w-4 h-4 mr-2" />
          {{ $t('groupQueries.createNew') }}
        </Button>
      </template>
    </PageHeader>

    <!-- Filter -->
    <QueryFilters v-model="filters" />

    <!-- Abfragen-Liste -->
    <div class="queries-grid">
      <GroupQueryCard
        v-for="query in filteredQueries"
        :key="query.id"
        :query="query"
        @open="openQuery"
        @evaluate="startEvaluation"
        @remind="sendReminder"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGroupQueryStore } from '@/stores/groupQuery'
import { Plus } from 'lucide-vue-next'

const router = useRouter()
const store = useGroupQueryStore()

const filters = ref({
  status: 'all',
  year: new Date().getFullYear(),
  category: 'all'
})

const filteredQueries = computed(() => {
  return store.queries.filter(q => {
    if (filters.value.status !== 'all' && q.status !== filters.value.status) return false
    if (filters.value.year && q.fiscalYear !== filters.value.year) return false
    if (filters.value.category !== 'all' && q.category !== filters.value.category) return false
    return true
  })
})

function createQuery() {
  router.push({ name: 'group-query-create' })
}

function openQuery(id: string) {
  router.push({ name: 'group-query-detail', params: { id } })
}

async function startEvaluation(queryId: string) {
  await store.createEvaluation(queryId)
  router.push({ name: 'group-query-evaluation', params: { id: queryId } })
}

async function sendReminder(queryId: string) {
  await store.sendReminders(queryId)
}

onMounted(() => {
  store.loadQueries()
})
</script>
```

```vue
<!-- apps/group-portal/src/components/GroupQueryCard.vue -->
<template>
  <div class="query-card" @click="$emit('open', query.id)">
    <div class="query-card__header">
      <h3 class="query-card__title">{{ query.title }}</h3>
      <StatusBadge :status="query.status" />
    </div>

    <div class="query-card__meta">
      <span class="query-card__year">
        <Calendar class="w-4 h-4" />
        {{ query.fiscalYear }}
      </span>
      <span class="query-card__deadline" :class="{ 'text-red-500': isOverdue }">
        <Clock class="w-4 h-4" />
        {{ formatDate(query.deadline) }}
      </span>
    </div>

    <!-- Fortschrittsanzeige -->
    <div class="query-card__progress">
      <div class="progress-header">
        <span>{{ submittedCount }}/{{ totalCount }} {{ $t('groupQueries.authorities') }}</span>
        <span>{{ progressPercent }}%</span>
      </div>
      <ProgressBar :value="progressPercent" />
    </div>

    <!-- Authority Status List -->
    <div class="query-card__authorities">
      <div
        v-for="assignment in visibleAssignments"
        :key="assignment.id"
        class="authority-row"
      >
        <span class="authority-status">
          <CheckCircle v-if="assignment.status === 'submitted'" class="text-green-500" />
          <Clock v-else-if="assignment.status === 'in_progress'" class="text-amber-500" />
          <Circle v-else class="text-slate-300" />
        </span>
        <span class="authority-name">{{ assignment.authorityName }}</span>
        <span class="authority-progress" v-if="assignment.status === 'in_progress'">
          {{ assignment.progress }}%
        </span>
      </div>
      <div v-if="hiddenCount > 0" class="more-authorities">
        + {{ hiddenCount }} {{ $t('common.more') }}
      </div>
    </div>

    <!-- Actions -->
    <div class="query-card__actions" @click.stop>
      <Button
        v-if="canEvaluate"
        size="sm"
        variant="primary"
        @click="$emit('evaluate', query.id)"
      >
        {{ $t('groupQueries.startEvaluation') }}
      </Button>
      <Button
        v-if="hasPendingAuthorities"
        size="sm"
        variant="ghost"
        @click="$emit('remind', query.id)"
      >
        {{ $t('groupQueries.sendReminder') }}
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Calendar, Clock, CheckCircle, Circle } from 'lucide-vue-next'
import type { GroupQuery } from '@flowaudit/domain/group-queries'

interface Props {
  query: GroupQuery
}

const props = defineProps<Props>()

const emit = defineEmits<{
  open: [id: string]
  evaluate: [id: string]
  remind: [id: string]
}>()

const totalCount = computed(() => props.query.assignments.length)
const submittedCount = computed(() =>
  props.query.assignments.filter(a => a.status === 'submitted').length
)
const progressPercent = computed(() =>
  Math.round((submittedCount.value / totalCount.value) * 100)
)

const isOverdue = computed(() => new Date(props.query.deadline) < new Date())

const visibleAssignments = computed(() => props.query.assignments.slice(0, 5))
const hiddenCount = computed(() => Math.max(0, totalCount.value - 5))

const canEvaluate = computed(() => {
  const config = props.query.config
  if (config.evaluationTrigger === 'manual') return true
  if (config.evaluationTrigger === 'after_deadline') return isOverdue.value
  if (config.evaluationTrigger === 'on_submission') return submittedCount.value > 0
  return false
})

const hasPendingAuthorities = computed(() =>
  props.query.assignments.some(a =>
    a.status === 'pending' || a.status === 'in_progress'
  )
)
</script>
```

### 1.5 API Endpoints für Konzern

```python
# backend/app/api/group_queries.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
from app.schemas.group_query import (
    GroupQueryCreate, GroupQueryUpdate, GroupQueryResponse,
    AssignmentUpdate, EvaluationResponse
)
from app.services.group_query_service import GroupQueryService
from app.core.auth import get_current_user, require_group_admin

router = APIRouter(prefix="/group-queries", tags=["Group Queries"])

@router.get("", response_model=List[GroupQueryResponse])
async def list_queries(
    status: Optional[str] = None,
    year: Optional[int] = None,
    current_user = Depends(require_group_admin),
    service: GroupQueryService = Depends()
):
    """Liste aller Konzern-Abfragen"""
    return await service.list_queries(
        tenant_id=current_user.tenant_id,
        status=status,
        year=year
    )

@router.post("", response_model=GroupQueryResponse)
async def create_query(
    data: GroupQueryCreate,
    current_user = Depends(require_group_admin),
    service: GroupQueryService = Depends()
):
    """Neue Konzern-Abfrage erstellen"""
    return await service.create_query(data, current_user)

@router.post("/{query_id}/publish")
async def publish_query(
    query_id: str,
    current_user = Depends(require_group_admin),
    service: GroupQueryService = Depends()
):
    """Abfrage an Prüfbehörden veröffentlichen"""
    return await service.publish_query(query_id, current_user)

@router.post("/{query_id}/evaluate", response_model=EvaluationResponse)
async def create_evaluation(
    query_id: str,
    include_pending: bool = False,
    current_user = Depends(require_group_admin),
    service: GroupQueryService = Depends()
):
    """Auswertung starten"""
    return await service.create_evaluation(
        query_id,
        include_pending=include_pending,
        created_by=current_user.id
    )

@router.post("/{query_id}/remind")
async def send_reminders(
    query_id: str,
    authority_ids: Optional[List[str]] = None,
    current_user = Depends(require_group_admin),
    service: GroupQueryService = Depends()
):
    """Erinnerungen an ausstehende Behörden senden"""
    return await service.send_reminders(query_id, authority_ids)

# --- Prüfbehörden-Endpoints ---

@router.get("/assignments/my", response_model=List[AssignmentResponse])
async def my_assignments(
    current_user = Depends(get_current_user),
    service: GroupQueryService = Depends()
):
    """Meine zugewiesenen Abfragen (für Prüfbehörde)"""
    return await service.get_assignments_for_authority(
        current_user.tenant_id
    )

@router.patch("/assignments/{assignment_id}")
async def update_assignment(
    assignment_id: str,
    data: AssignmentUpdate,
    current_user = Depends(get_current_user),
    service: GroupQueryService = Depends()
):
    """Antwort auf Abfrage aktualisieren"""
    return await service.update_assignment(assignment_id, data, current_user)

@router.post("/assignments/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: str,
    current_user = Depends(get_current_user),
    service: GroupQueryService = Depends()
):
    """Abfrage als fertig markieren und einreichen"""
    return await service.submit_assignment(assignment_id, current_user)

@router.post("/assignments/{assignment_id}/attachments")
async def upload_attachment(
    assignment_id: str,
    requirement_id: Optional[str] = None,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    service: GroupQueryService = Depends()
):
    """Datei zur Abfrage hochladen"""
    return await service.upload_attachment(
        assignment_id,
        requirement_id,
        file,
        current_user
    )
```

---

## Teil 2: Prüfer-Schreibtisch (Auditor Desk)

### 2.1 Schreibtisch-Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Vorhabenprüfung: VH-2024-0234                                    [← Zurück]│
│  Digitalisierung Handwerk GmbH                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         PRÜFER-SCHREIBTISCH                            ││
│  │                                                                         ││
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  ││
│  │   │ 📋           │  │ 📄           │  │ 📁           │                  ││
│  │   │ Checklisten  │  │ Belegliste   │  │ Dokumente    │                  ││
│  │   │              │  │              │  │              │                  ││
│  │   │  3 Stück     │  │  52 Belege   │  │  12 Dateien  │                  ││
│  │   │  ✅ 2 fertig │  │  ⚠️ 7 offen  │  │              │                  ││
│  │   └──────────────┘  └──────────────┘  └──────────────┘                  ││
│  │                                                                         ││
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  ││
│  │   │ 📝           │  │ 💬           │  │ 📊           │                  ││
│  │   │ Feststellung-│  │ Stellung-    │  │ Statistik    │                  ││
│  │   │ en           │  │ nahmen       │  │              │                  ││
│  │   │  2 offen     │  │  1 aussteh.  │  │              │                  ││
│  │   └──────────────┘  └──────────────┘  └──────────────┘                  ││
│  │                                                                         ││
│  │   ┌──────────────────────────────────────────────────────────┐          ││
│  │   │ 📥 BELEGKASTEN                                    [KI-Prüfung]     ││
│  │   │ ──────────────────────────────────────────────────────────│          ││
│  │   │                                                           │          ││
│  │   │   Ziehen Sie Belege hierher oder klicken Sie zum Hochladen│          ││
│  │   │                                                           │          ││
│  │   │   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐            │          ││
│  │   │   │ 📄     │ │ 📄     │ │ 📄     │ │ 📄     │            │          ││
│  │   │   │RE-001  │ │RE-002  │ │RE-003  │ │RE-004  │            │          ││
│  │   │   │✅      │ │⚠️      │ │🔄      │ │○       │            │          ││
│  │   │   └────────┘ └────────┘ └────────┘ └────────┘            │          ││
│  │   │                                                           │          ││
│  │   │   Geprüft: 12/52    In Prüfung: 3    Offen: 37           │          ││
│  │   └──────────────────────────────────────────────────────────┘          ││
│  │                                                                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Belegkasten mit FlowInvoice-Integration

```typescript
// packages/domain/document-box/types.ts

/**
 * Belegkasten - Container für zu prüfende Belege
 */
export interface DocumentBox {
  id: string
  auditCaseId: string

  // Belege
  documents: BoxDocument[]

  // Status
  statistics: BoxStatistics

  // KI-Prüfung
  aiVerification: {
    enabled: boolean
    provider: 'flow_invoice' | 'custom'
    lastRunAt?: string
    config: AiVerificationConfig
  }
}

export interface BoxDocument {
  id: string
  boxId: string

  // Beleg-Referenz
  expenditureItemId?: string    // Verweis auf Beleglistenposition

  // Datei
  fileName: string
  fileSize: number
  mimeType: string
  storagePath: string
  thumbnailPath?: string

  // Upload
  uploadedBy: string
  uploadedAt: string

  // Manuelle Prüfung
  manualVerification?: {
    status: 'pending' | 'verified' | 'rejected' | 'unclear'
    verifiedBy?: string
    verifiedAt?: string
    remarks?: string
    findings?: string[]
  }

  // KI-Prüfung (FlowInvoice)
  aiVerification?: AiVerificationResult

  // Zuordnung
  matchedExpenditure?: {
    itemId: string
    invoiceNumber: string
    amount: number
    matchConfidence: number    // 0-1
  }
}

export interface AiVerificationResult {
  id: string
  documentId: string

  // Zeitpunkt
  processedAt: string
  processingTime: number       // ms

  // Extraktion
  extractedData: {
    invoiceNumber?: string
    invoiceDate?: string
    vendorName?: string
    vendorAddress?: string
    totalAmount?: number
    currency?: string
    taxAmount?: number
    lineItems?: ExtractedLineItem[]
    paymentTerms?: string
  }

  // Prüfergebnisse
  verificationResults: {
    // Formale Prüfung
    formalChecks: {
      hasInvoiceNumber: boolean
      hasDate: boolean
      hasVendorInfo: boolean
      hasAmounts: boolean
      hasRequiredElements: boolean
    }

    // Rechnerische Prüfung
    arithmeticChecks: {
      lineItemsSum: boolean
      taxCalculation: boolean
      totalCorrect: boolean
    }

    // Plausibilität
    plausibilityChecks: {
      dateInProjectPeriod: boolean
      amountWithinBudget: boolean
      vendorKnown: boolean
      duplicateDetected: boolean
    }

    // Gesamtergebnis
    overallScore: number        // 0-100
    riskLevel: 'low' | 'medium' | 'high'
    requiresManualReview: boolean
  }

  // Warnungen & Hinweise
  warnings: AiWarning[]
  suggestions: AiSuggestion[]

  // Confidence
  confidence: {
    extraction: number          // 0-1
    verification: number        // 0-1
    overall: number
  }
}

export interface AiWarning {
  code: string
  severity: 'info' | 'warning' | 'error'
  message: string
  field?: string
  suggestion?: string
}

export interface ExtractedLineItem {
  description: string
  quantity?: number
  unitPrice?: number
  totalPrice: number
  taxRate?: number
}

export interface BoxStatistics {
  total: number
  verified: number
  rejected: number
  inProgress: number
  pending: number

  // KI-Statistik
  aiProcessed: number
  aiApproved: number
  aiRejected: number
  aiUnclear: number

  // Beträge
  totalAmount: number
  verifiedAmount: number
  rejectedAmount: number
}
```

### 2.3 Vue-Komponente für Belegkasten

```vue
<!-- apps/audit-portal/src/components/desk/DocumentBox.vue -->
<template>
  <div class="document-box">
    <div class="document-box__header">
      <h3 class="document-box__title">
        <Inbox class="w-5 h-5" />
        {{ $t('documentBox.title') }}
      </h3>
      <div class="document-box__actions">
        <Button
          v-if="aiEnabled"
          @click="runAiVerification"
          :loading="isAiRunning"
          variant="secondary"
        >
          <Sparkles class="w-4 h-4 mr-2" />
          {{ $t('documentBox.aiVerification') }}
        </Button>
        <Button @click="openUploadDialog" variant="ghost">
          <Upload class="w-4 h-4 mr-2" />
          {{ $t('common.upload') }}
        </Button>
      </div>
    </div>

    <!-- Drop Zone -->
    <div
      class="document-box__dropzone"
      :class="{ 'dropzone--active': isDragging }"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @drop.prevent="handleDrop"
    >
      <div v-if="documents.length === 0" class="dropzone-empty">
        <FileUp class="w-12 h-12 text-slate-300" />
        <p>{{ $t('documentBox.dropHint') }}</p>
      </div>

      <!-- Document Grid -->
      <div v-else class="documents-grid">
        <DocumentThumbnail
          v-for="doc in documents"
          :key="doc.id"
          :document="doc"
          @click="openDocument(doc)"
          @verify="openVerificationPanel(doc)"
        />
      </div>
    </div>

    <!-- Statistics Bar -->
    <div class="document-box__stats">
      <div class="stat stat--verified">
        <CheckCircle class="w-4 h-4" />
        <span>{{ stats.verified }}</span>
      </div>
      <div class="stat stat--warning">
        <AlertTriangle class="w-4 h-4" />
        <span>{{ stats.rejected }}</span>
      </div>
      <div class="stat stat--processing">
        <Loader class="w-4 h-4 animate-spin" />
        <span>{{ stats.inProgress }}</span>
      </div>
      <div class="stat stat--pending">
        <Circle class="w-4 h-4" />
        <span>{{ stats.pending }}</span>
      </div>
    </div>

    <!-- AI Verification Panel -->
    <Teleport to="body">
      <AiVerificationPanel
        v-if="selectedDocument"
        :document="selectedDocument"
        @close="selectedDocument = null"
        @verify="handleManualVerification"
      />
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Inbox, Upload, Sparkles, FileUp,
  CheckCircle, AlertTriangle, Loader, Circle
} from 'lucide-vue-next'
import { useDocumentBoxStore } from '@/stores/documentBox'
import type { BoxDocument } from '@flowaudit/domain/document-box'

interface Props {
  auditCaseId: string
}

const props = defineProps<Props>()
const store = useDocumentBoxStore()

const isDragging = ref(false)
const selectedDocument = ref<BoxDocument | null>(null)
const isAiRunning = ref(false)

const documents = computed(() => store.documents)
const stats = computed(() => store.statistics)
const aiEnabled = computed(() => store.box?.aiVerification.enabled ?? false)

async function handleDrop(event: DragEvent) {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files) {
    await store.uploadDocuments(props.auditCaseId, Array.from(files))
  }
}

function openUploadDialog() {
  // Open file picker
  const input = document.createElement('input')
  input.type = 'file'
  input.multiple = true
  input.accept = '.pdf,.jpg,.jpeg,.png,.tiff'
  input.onchange = async (e) => {
    const files = (e.target as HTMLInputElement).files
    if (files) {
      await store.uploadDocuments(props.auditCaseId, Array.from(files))
    }
  }
  input.click()
}

async function runAiVerification() {
  isAiRunning.value = true
  try {
    await store.runAiVerification(props.auditCaseId)
  } finally {
    isAiRunning.value = false
  }
}

function openDocument(doc: BoxDocument) {
  // Open in viewer
  window.open(`/api/documents/${doc.id}/view`, '_blank')
}

function openVerificationPanel(doc: BoxDocument) {
  selectedDocument.value = doc
}

async function handleManualVerification(
  docId: string,
  status: 'verified' | 'rejected',
  remarks?: string
) {
  await store.verifyDocument(docId, status, remarks)
  selectedDocument.value = null
}
</script>

<style scoped>
.document-box {
  @apply bg-white dark:bg-slate-800 rounded-xl;
  @apply border border-slate-200 dark:border-slate-700;
  @apply overflow-hidden;
}

.document-box__header {
  @apply flex justify-between items-center px-6 py-4;
  @apply border-b border-slate-100 dark:border-slate-700;
}

.document-box__title {
  @apply flex items-center gap-2 text-lg font-semibold;
  @apply text-slate-900 dark:text-white;
}

.document-box__dropzone {
  @apply p-6 min-h-[300px];
  @apply transition-colors duration-200;
}

.dropzone--active {
  @apply bg-primary-50 dark:bg-primary-900/20;
  @apply border-2 border-dashed border-primary-300;
}

.dropzone-empty {
  @apply flex flex-col items-center justify-center h-full;
  @apply text-slate-400 dark:text-slate-500;
}

.documents-grid {
  @apply grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-4;
}

.document-box__stats {
  @apply flex gap-6 px-6 py-3;
  @apply bg-slate-50 dark:bg-slate-900/50;
  @apply border-t border-slate-100 dark:border-slate-700;
}

.stat {
  @apply flex items-center gap-1.5 text-sm;
}

.stat--verified { @apply text-green-600 dark:text-green-400; }
.stat--warning { @apply text-amber-600 dark:text-amber-400; }
.stat--processing { @apply text-blue-600 dark:text-blue-400; }
.stat--pending { @apply text-slate-400; }
</style>
```

### 2.4 FlowInvoice Service-Integration

```typescript
// packages/documents/flow-invoice/service.ts

import type { BoxDocument, AiVerificationResult } from '@flowaudit/domain/document-box'

export interface FlowInvoiceConfig {
  apiUrl: string
  apiKey: string
  tenant: string
  features: {
    ocr: boolean
    extraction: boolean
    verification: boolean
    duplicateDetection: boolean
  }
}

export class FlowInvoiceService {
  private config: FlowInvoiceConfig

  constructor(config: FlowInvoiceConfig) {
    this.config = config
  }

  /**
   * Beleg mit KI analysieren
   */
  async analyzeDocument(document: BoxDocument): Promise<AiVerificationResult> {
    const response = await fetch(`${this.config.apiUrl}/analyze`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.config.apiKey}`,
        'X-Tenant': this.config.tenant,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        documentId: document.id,
        documentUrl: document.storagePath,
        features: this.config.features,
        context: {
          expenditureItemId: document.expenditureItemId,
          expectedAmount: document.matchedExpenditure?.amount
        }
      })
    })

    if (!response.ok) {
      throw new Error(`FlowInvoice API error: ${response.status}`)
    }

    return await response.json()
  }

  /**
   * Batch-Analyse mehrerer Belege
   */
  async analyzeBatch(documents: BoxDocument[]): Promise<Map<string, AiVerificationResult>> {
    const results = new Map<string, AiVerificationResult>()

    // Parallel mit Rate-Limiting
    const batchSize = 5
    for (let i = 0; i < documents.length; i += batchSize) {
      const batch = documents.slice(i, i + batchSize)
      const batchResults = await Promise.all(
        batch.map(doc => this.analyzeDocument(doc))
      )

      batch.forEach((doc, index) => {
        results.set(doc.id, batchResults[index])
      })
    }

    return results
  }

  /**
   * Duplikatprüfung
   */
  async checkDuplicates(
    document: BoxDocument,
    existingDocuments: BoxDocument[]
  ): Promise<DuplicateCheckResult> {
    const response = await fetch(`${this.config.apiUrl}/duplicates`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.config.apiKey}`,
        'X-Tenant': this.config.tenant,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        documentId: document.id,
        compareWith: existingDocuments.map(d => d.id)
      })
    })

    return await response.json()
  }
}

export interface DuplicateCheckResult {
  isDuplicate: boolean
  confidence: number
  matches: Array<{
    documentId: string
    similarity: number
    matchedFields: string[]
  }>
}
```

---

## Teil 3: FlowNavigator (Deployment-Tool)

### 3.1 Übersicht

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FlowNavigator - Administration & Deployment                       v1.0.0  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ Navigation ─────────────────────────────────────────────────────────┐   │
│  │ 🏠 Dashboard │ 📦 Pakete │ 🏢 Mandanten │ 🚀 Deployments │ 📊 Monitor │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  📦 Verfügbare Pakete                                               │   │
│  │  ────────────────────────────────────────────────────────────────── │   │
│  │                                                                      │   │
│  │  @flowaudit/core                                                     │   │
│  │  ├─ @flowaudit/common           v2.1.0  ✅ Installiert              │   │
│  │  ├─ @flowaudit/validation       v2.1.0  ✅ Installiert              │   │
│  │  ├─ @flowaudit/calculations     v2.0.3  ⚠️ Update verfügbar (2.1.0) │   │
│  │  └─ @flowaudit/permissions      v2.1.0  ✅ Installiert              │   │
│  │                                                                      │   │
│  │  @flowaudit/domain                                                   │   │
│  │  ├─ @flowaudit/fiscal-year      v1.5.0  ✅ Installiert              │   │
│  │  ├─ @flowaudit/operations       v1.5.0  ✅ Installiert              │   │
│  │  ├─ @flowaudit/checklists       v1.5.2  ⚠️ Update verfügbar (1.6.0) │   │
│  │  ├─ @flowaudit/audit-cases      v1.5.0  ✅ Installiert              │   │
│  │  ├─ @flowaudit/findings         v1.5.0  ✅ Installiert              │   │
│  │  ├─ @flowaudit/sampling         v1.4.0  ○ Nicht installiert         │   │
│  │  └─ @flowaudit/group-queries    v1.2.0  ○ Nicht installiert         │   │
│  │                                                                      │   │
│  │  @flowaudit/reporting                                                │   │
│  │  ├─ @flowaudit/report-engine    v1.3.0  ✅ Installiert              │   │
│  │  ├─ @flowaudit/templates        v1.3.0  ✅ Installiert              │   │
│  │  ├─ @flowaudit/text-modules     v1.2.0  ○ Nicht installiert         │   │
│  │  └─ @flowaudit/jkb              v1.1.0  ○ Nicht installiert         │   │
│  │                                                                      │   │
│  │  @flowaudit/documents                                                │   │
│  │  ├─ @flowaudit/file-manager     v1.2.0  ✅ Installiert              │   │
│  │  ├─ @flowaudit/word-export      v1.2.0  ✅ Installiert              │   │
│  │  ├─ @flowaudit/excel-import     v1.1.0  ✅ Installiert              │   │
│  │  └─ @flowaudit/flow-invoice     v0.9.0  ○ Beta - Nicht installiert  │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  🏢 Mandanten-Übersicht                                             │   │
│  │  ────────────────────────────────────────────────────────────────── │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │ Konzern A    │  │ Konzern B    │  │ Konzern C    │               │   │
│  │  │ ──────────── │  │ ──────────── │  │ ──────────── │               │   │
│  │  │ 5 Behörden   │  │ 3 Behörden   │  │ 8 Behörden   │               │   │
│  │  │ 12 Module    │  │ 8 Module     │  │ 15 Module    │               │   │
│  │  │ ✅ Online    │  │ ✅ Online    │  │ ⚠️ 2 Updates │               │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Datenmodell

```typescript
// apps/flow-navigator/src/types/index.ts

/**
 * FlowNavigator - Zentrales Deployment & Administration Tool
 */

// ============ Pakete ============

export interface Package {
  name: string                    // "@flowaudit/checklists"
  displayName: string             // "Checklisten-Modul"
  description: string
  category: PackageCategory

  // Versionen
  latestVersion: string
  versions: PackageVersion[]

  // Abhängigkeiten
  dependencies: string[]          // Andere @flowaudit/* Pakete
  peerDependencies: string[]

  // Lizenzierung
  license: LicenseType

  // Status
  status: 'stable' | 'beta' | 'alpha' | 'deprecated'

  // Dokumentation
  docsUrl: string
  changelogUrl: string
}

export type PackageCategory =
  | 'core'           // Kernfunktionalität
  | 'domain'         // Fachliche Module
  | 'reporting'      // Berichtswesen
  | 'documents'      // Dokumentenmanagement
  | 'adapters'       // Framework-Adapter
  | 'integrations'   // Externe Integrationen

export interface PackageVersion {
  version: string
  releaseDate: string
  releaseNotes: string
  breaking: boolean
  minRequirements: {
    node: string
    pnpm: string
  }
  checksum: string
}

export type LicenseType =
  | 'enterprise'     // Kostenpflichtig
  | 'professional'   // Mittleres Tier
  | 'community'      // Kostenlos (eingeschränkt)

// ============ Mandanten ============

export interface Tenant {
  id: string
  name: string
  type: 'group' | 'authority'     // Konzern oder Prüfbehörde
  parentId?: string               // Bei authority: Zugehöriger Konzern

  // Kontakt
  contact: TenantContact

  // Lizenz
  license: TenantLicense

  // Installation
  installation: TenantInstallation

  // Status
  status: 'active' | 'suspended' | 'trial'

  // Metriken
  metrics: TenantMetrics
}

export interface TenantContact {
  companyName: string
  address: string
  adminName: string
  adminEmail: string
  phone?: string
}

export interface TenantLicense {
  type: 'enterprise' | 'professional' | 'trial'
  validFrom: string
  validUntil: string
  maxUsers: number
  modules: string[]              // Lizenzierte Module
  features: string[]             // Freigeschaltete Features
}

export interface TenantInstallation {
  // Umgebung
  environment: 'cloud' | 'on-premise' | 'hybrid'
  region?: string                // Bei Cloud: "eu-central-1"

  // Installierte Pakete
  packages: InstalledPackage[]

  // Datenbank
  database: {
    type: 'postgresql'
    version: string
    host: string
    status: 'online' | 'offline' | 'degraded'
  }

  // Backend
  backend: {
    version: string
    url: string
    status: 'online' | 'offline' | 'degraded'
    lastHealthCheck: string
  }

  // Frontend
  frontend: {
    version: string
    url: string
    status: 'online' | 'offline'
  }
}

export interface InstalledPackage {
  name: string
  version: string
  installedAt: string
  installedBy: string
  updateAvailable?: string       // Neuere Version
  config: Record<string, any>    // Modul-spezifische Konfiguration
}

export interface TenantMetrics {
  users: {
    total: number
    active: number
    lastMonth: number
  }
  storage: {
    used: number                 // GB
    limit: number
  }
  audits: {
    total: number
    thisYear: number
    inProgress: number
  }
  api: {
    requestsToday: number
    requestsThisMonth: number
    errorRate: number
  }
}

// ============ Deployments ============

export interface Deployment {
  id: string
  tenantId: string

  // Was wird deployed
  type: 'install' | 'update' | 'uninstall' | 'config'
  packages: DeploymentPackage[]

  // Zeitplan
  scheduledAt?: string
  startedAt?: string
  completedAt?: string

  // Status
  status: DeploymentStatus
  progress: number               // 0-100

  // Logs
  logs: DeploymentLog[]

  // Ersteller
  createdBy: string
  createdAt: string

  // Rollback
  canRollback: boolean
  rollbackDeploymentId?: string
}

export type DeploymentStatus =
  | 'scheduled'
  | 'pending'
  | 'in_progress'
  | 'validating'
  | 'completed'
  | 'failed'
  | 'rolled_back'

export interface DeploymentPackage {
  name: string
  fromVersion?: string           // Bei Update
  toVersion: string
  status: 'pending' | 'installing' | 'completed' | 'failed'
  error?: string
}

export interface DeploymentLog {
  timestamp: string
  level: 'info' | 'warning' | 'error'
  message: string
  details?: Record<string, any>
}

// ============ Monitoring ============

export interface SystemHealth {
  overall: 'healthy' | 'degraded' | 'critical'

  services: ServiceHealth[]

  alerts: Alert[]

  metrics: {
    cpu: number
    memory: number
    disk: number
    network: {
      in: number
      out: number
    }
  }
}

export interface ServiceHealth {
  name: string
  status: 'healthy' | 'degraded' | 'critical' | 'offline'
  responseTime: number           // ms
  uptime: number                 // Percentage
  lastCheck: string
  details?: string
}

export interface Alert {
  id: string
  severity: 'info' | 'warning' | 'error' | 'critical'
  title: string
  message: string
  source: string
  timestamp: string
  acknowledged: boolean
  acknowledgedBy?: string
}
```

### 3.3 FlowNavigator API

```python
# apps/flow-navigator/backend/app/api/packages.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.schemas.package import PackageResponse, PackageVersionResponse
from app.services.package_service import PackageService
from app.services.registry_service import NpmRegistryService
from app.core.auth import require_admin

router = APIRouter(prefix="/packages", tags=["Packages"])

@router.get("", response_model=List[PackageResponse])
async def list_packages(
    category: Optional[str] = None,
    current_user = Depends(require_admin),
    service: PackageService = Depends()
):
    """Liste aller verfügbaren @flowaudit/* Pakete"""
    return await service.list_packages(category=category)

@router.get("/{package_name}/versions")
async def get_versions(
    package_name: str,
    service: NpmRegistryService = Depends()
):
    """Verfügbare Versionen eines Pakets"""
    return await service.get_versions(f"@flowaudit/{package_name}")

@router.get("/{package_name}/changelog")
async def get_changelog(
    package_name: str,
    from_version: Optional[str] = None,
    service: PackageService = Depends()
):
    """Changelog eines Pakets"""
    return await service.get_changelog(package_name, from_version)


# apps/flow-navigator/backend/app/api/tenants.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from app.services.tenant_service import TenantService
from app.core.auth import require_admin

router = APIRouter(prefix="/tenants", tags=["Tenants"])

@router.get("", response_model=List[TenantResponse])
async def list_tenants(
    type: Optional[str] = None,
    status: Optional[str] = None,
    current_user = Depends(require_admin),
    service: TenantService = Depends()
):
    """Liste aller Mandanten"""
    return await service.list_tenants(type=type, status=status)

@router.post("", response_model=TenantResponse)
async def create_tenant(
    data: TenantCreate,
    current_user = Depends(require_admin),
    service: TenantService = Depends()
):
    """Neuen Mandanten anlegen"""
    return await service.create_tenant(data, current_user)

@router.get("/{tenant_id}/packages")
async def get_tenant_packages(
    tenant_id: str,
    current_user = Depends(require_admin),
    service: TenantService = Depends()
):
    """Installierte Pakete eines Mandanten"""
    return await service.get_installed_packages(tenant_id)

@router.get("/{tenant_id}/health")
async def get_tenant_health(
    tenant_id: str,
    current_user = Depends(require_admin),
    service: TenantService = Depends()
):
    """Health-Status eines Mandanten"""
    return await service.check_health(tenant_id)


# apps/flow-navigator/backend/app/api/deployments.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List
from app.schemas.deployment import DeploymentCreate, DeploymentResponse
from app.services.deployment_service import DeploymentService
from app.core.auth import require_admin

router = APIRouter(prefix="/deployments", tags=["Deployments"])

@router.get("", response_model=List[DeploymentResponse])
async def list_deployments(
    tenant_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user = Depends(require_admin),
    service: DeploymentService = Depends()
):
    """Liste aller Deployments"""
    return await service.list_deployments(tenant_id=tenant_id, status=status)

@router.post("", response_model=DeploymentResponse)
async def create_deployment(
    data: DeploymentCreate,
    background_tasks: BackgroundTasks,
    current_user = Depends(require_admin),
    service: DeploymentService = Depends()
):
    """Neues Deployment erstellen"""
    deployment = await service.create_deployment(data, current_user)

    # Deployment im Hintergrund ausführen
    if not data.scheduled_at:
        background_tasks.add_task(service.execute_deployment, deployment.id)

    return deployment

@router.post("/{deployment_id}/execute")
async def execute_deployment(
    deployment_id: str,
    background_tasks: BackgroundTasks,
    current_user = Depends(require_admin),
    service: DeploymentService = Depends()
):
    """Geplantes Deployment manuell starten"""
    background_tasks.add_task(service.execute_deployment, deployment_id)
    return {"status": "started"}

@router.post("/{deployment_id}/rollback")
async def rollback_deployment(
    deployment_id: str,
    background_tasks: BackgroundTasks,
    current_user = Depends(require_admin),
    service: DeploymentService = Depends()
):
    """Deployment zurückrollen"""
    rollback = await service.create_rollback(deployment_id, current_user)
    background_tasks.add_task(service.execute_deployment, rollback.id)
    return rollback

@router.get("/{deployment_id}/logs")
async def get_deployment_logs(
    deployment_id: str,
    current_user = Depends(require_admin),
    service: DeploymentService = Depends()
):
    """Deployment-Logs abrufen"""
    return await service.get_logs(deployment_id)
```

### 3.4 Deployment Service

```python
# apps/flow-navigator/backend/app/services/deployment_service.py

import asyncio
from typing import List, Optional
from datetime import datetime
from app.models.deployment import Deployment, DeploymentPackage, DeploymentLog
from app.services.package_service import PackageService
from app.services.tenant_service import TenantService
from app.core.database import AsyncSession

class DeploymentService:
    def __init__(
        self,
        db: AsyncSession,
        package_service: PackageService,
        tenant_service: TenantService
    ):
        self.db = db
        self.package_service = package_service
        self.tenant_service = tenant_service

    async def execute_deployment(self, deployment_id: str) -> None:
        """Führt ein Deployment aus"""
        deployment = await self.get_deployment(deployment_id)

        try:
            await self._update_status(deployment, 'in_progress')
            await self._log(deployment, 'info', 'Deployment gestartet')

            # 1. Validierung
            await self._update_status(deployment, 'validating')
            await self._validate_deployment(deployment)

            # 2. Backup erstellen
            await self._log(deployment, 'info', 'Erstelle Backup...')
            backup_id = await self._create_backup(deployment)

            # 3. Pakete installieren/aktualisieren
            for pkg in deployment.packages:
                await self._deploy_package(deployment, pkg)

            # 4. Migrationen ausführen
            await self._log(deployment, 'info', 'Führe Migrationen aus...')
            await self._run_migrations(deployment)

            # 5. Health Check
            await self._log(deployment, 'info', 'Prüfe System-Health...')
            await self._health_check(deployment)

            # 6. Abschluss
            await self._update_status(deployment, 'completed')
            await self._log(deployment, 'info', 'Deployment erfolgreich abgeschlossen')

        except Exception as e:
            await self._log(deployment, 'error', f'Deployment fehlgeschlagen: {str(e)}')
            await self._update_status(deployment, 'failed')

            # Automatischer Rollback bei kritischen Fehlern
            if deployment.can_rollback:
                await self._log(deployment, 'warning', 'Starte automatischen Rollback...')
                await self._execute_rollback(deployment, backup_id)

    async def _deploy_package(
        self,
        deployment: Deployment,
        pkg: DeploymentPackage
    ) -> None:
        """Einzelnes Paket deployen"""
        try:
            pkg.status = 'installing'
            await self.db.commit()

            await self._log(
                deployment,
                'info',
                f'Installiere {pkg.name}@{pkg.to_version}...'
            )

            tenant = await self.tenant_service.get_tenant(deployment.tenant_id)

            if deployment.type == 'install':
                await self._install_package(tenant, pkg)
            elif deployment.type == 'update':
                await self._update_package(tenant, pkg)
            elif deployment.type == 'uninstall':
                await self._uninstall_package(tenant, pkg)

            pkg.status = 'completed'
            await self.db.commit()

            await self._log(
                deployment,
                'info',
                f'{pkg.name}@{pkg.to_version} erfolgreich installiert'
            )

        except Exception as e:
            pkg.status = 'failed'
            pkg.error = str(e)
            await self.db.commit()
            raise

    async def _install_package(self, tenant, pkg: DeploymentPackage) -> None:
        """Paket neu installieren"""
        # 1. Dependencies prüfen
        dependencies = await self.package_service.get_dependencies(pkg.name)
        for dep in dependencies:
            if not await self._is_installed(tenant, dep):
                raise ValueError(f'Abhängigkeit nicht erfüllt: {dep}')

        # 2. Paket herunterladen
        package_archive = await self.package_service.download_package(
            pkg.name,
            pkg.to_version
        )

        # 3. Auf Mandanten-Server deployen
        if tenant.installation.environment == 'cloud':
            await self._deploy_to_cloud(tenant, package_archive)
        else:
            await self._deploy_to_on_premise(tenant, package_archive)

        # 4. Konfiguration anwenden
        await self._apply_default_config(tenant, pkg.name)

        # 5. In Datenbank registrieren
        await self.tenant_service.register_package(
            tenant.id,
            pkg.name,
            pkg.to_version
        )

    async def _run_migrations(self, deployment: Deployment) -> None:
        """Datenbank-Migrationen ausführen"""
        tenant = await self.tenant_service.get_tenant(deployment.tenant_id)

        for pkg in deployment.packages:
            migrations = await self.package_service.get_migrations(
                pkg.name,
                from_version=pkg.from_version,
                to_version=pkg.to_version
            )

            for migration in migrations:
                await self._log(
                    deployment,
                    'info',
                    f'Migration: {migration.name}'
                )
                await self._execute_migration(tenant, migration)

    async def _health_check(self, deployment: Deployment) -> None:
        """System-Health nach Deployment prüfen"""
        tenant = await self.tenant_service.get_tenant(deployment.tenant_id)
        health = await self.tenant_service.check_health(tenant.id)

        if health.overall == 'critical':
            raise ValueError('Health-Check fehlgeschlagen: System kritisch')

        if health.overall == 'degraded':
            await self._log(
                deployment,
                'warning',
                'System-Health degradiert - bitte prüfen'
            )
```

### 3.5 Vue Dashboard für FlowNavigator

```vue
<!-- apps/flow-navigator/src/views/DashboardView.vue -->
<template>
  <div class="dashboard">
    <PageHeader title="FlowNavigator Dashboard" />

    <!-- System Health -->
    <div class="health-overview">
      <HealthCard
        v-for="service in systemHealth.services"
        :key="service.name"
        :service="service"
      />
    </div>

    <!-- Alerts -->
    <AlertBanner
      v-if="activeAlerts.length > 0"
      :alerts="activeAlerts"
      @acknowledge="acknowledgeAlert"
    />

    <!-- Main Grid -->
    <div class="dashboard-grid">
      <!-- Tenants Overview -->
      <DashboardCard title="Mandanten" icon="Building2">
        <div class="tenant-stats">
          <StatItem label="Gesamt" :value="tenantStats.total" />
          <StatItem label="Aktiv" :value="tenantStats.active" color="green" />
          <StatItem label="Updates" :value="tenantStats.needsUpdate" color="amber" />
        </div>
        <TenantMiniList :tenants="recentTenants" />
      </DashboardCard>

      <!-- Packages -->
      <DashboardCard title="Pakete" icon="Package">
        <div class="package-stats">
          <StatItem label="Verfügbar" :value="packageStats.total" />
          <StatItem label="Updates" :value="packageStats.updatesAvailable" color="blue" />
        </div>
        <PackageUpdateList :updates="pendingUpdates" />
      </DashboardCard>

      <!-- Recent Deployments -->
      <DashboardCard title="Letzte Deployments" icon="Rocket" class="col-span-2">
        <DeploymentTable :deployments="recentDeployments" compact />
      </DashboardCard>

      <!-- Activity Timeline -->
      <DashboardCard title="Aktivitäten" icon="Activity">
        <ActivityTimeline :activities="recentActivities" />
      </DashboardCard>

      <!-- Quick Actions -->
      <DashboardCard title="Schnellaktionen" icon="Zap">
        <div class="quick-actions">
          <QuickActionButton
            icon="Plus"
            label="Neuer Mandant"
            @click="$router.push('/tenants/new')"
          />
          <QuickActionButton
            icon="RefreshCw"
            label="Alle aktualisieren"
            @click="showBulkUpdateDialog = true"
          />
          <QuickActionButton
            icon="Download"
            label="Backup erstellen"
            @click="createGlobalBackup"
          />
          <QuickActionButton
            icon="FileText"
            label="Report generieren"
            @click="generateReport"
          />
        </div>
      </DashboardCard>
    </div>

    <!-- Dialogs -->
    <BulkUpdateDialog
      v-if="showBulkUpdateDialog"
      @close="showBulkUpdateDialog = false"
      @confirm="executeBulkUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useNavigatorStore } from '@/stores/navigator'
import { useSystemHealthStore } from '@/stores/systemHealth'

const navigatorStore = useNavigatorStore()
const healthStore = useSystemHealthStore()

const showBulkUpdateDialog = ref(false)

const systemHealth = computed(() => healthStore.health)
const activeAlerts = computed(() => healthStore.activeAlerts)
const tenantStats = computed(() => navigatorStore.tenantStats)
const packageStats = computed(() => navigatorStore.packageStats)
const recentTenants = computed(() => navigatorStore.recentTenants)
const pendingUpdates = computed(() => navigatorStore.pendingUpdates)
const recentDeployments = computed(() => navigatorStore.recentDeployments)
const recentActivities = computed(() => navigatorStore.recentActivities)

onMounted(async () => {
  await Promise.all([
    navigatorStore.loadDashboardData(),
    healthStore.loadHealth()
  ])
})

async function acknowledgeAlert(alertId: string) {
  await healthStore.acknowledgeAlert(alertId)
}

async function executeBulkUpdate(tenantIds: string[]) {
  showBulkUpdateDialog.value = false
  await navigatorStore.createBulkUpdate(tenantIds)
}

async function createGlobalBackup() {
  await navigatorStore.createGlobalBackup()
}

async function generateReport() {
  const report = await navigatorStore.generateSystemReport()
  // Download report
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `flowaudit-report-${new Date().toISOString().split('T')[0]}.json`
  a.click()
}
</script>
```

---

## Teil 4: Agent-Zuordnung für Implementierung

### 4.1 Implementierungsreihenfolge

```
Phase 1: Basis-Infrastruktur (2-3 Sprints)
├── @database    → Mandanten-Schema erweitern
├── @backend     → Multi-Tenant API-Basis
└── @frontend    → Theme & i18n Setup

Phase 2: Konzernansicht (3-4 Sprints)
├── @database    → GroupQuery, Assignment, Response Models
├── @backend     → GroupQuery Service & API
├── @checklists  → Konzern-Checklisten-Erstellung
├── @frontend    → Group Portal UI
└── @reporting   → Konzern-Auswertungen

Phase 3: Prüfer-Schreibtisch (2-3 Sprints)
├── @database    → DocumentBox Model
├── @backend     → DocumentBox Service
├── @frontend    → Desk UI & Belegkasten
└── @api-client  → FlowInvoice Integration

Phase 4: FlowNavigator (3-4 Sprints)
├── @database    → Package, Tenant, Deployment Models
├── @backend     → Navigator API & Services
├── @frontend    → Navigator Dashboard
└── @backend     → Deployment Engine

Phase 5: FlowInvoice (4-5 Sprints)
├── @backend     → KI-Service Integration
├── @backend     → OCR & Extraktion
├── @backend     → Validierungslogik
└── @frontend    → Verification Panel
```

### 4.2 Agent-Aufgaben pro Feature

```yaml
# Konzernansicht
konzernansicht:
  database:
    - "Erstelle Alembic Migration für GroupQuery, GroupQueryAssignment, GroupQueryResponse"
    - "Füge JSONB Spalten für checklistData und summaryData hinzu"
    - "Erstelle Indices für tenant_id und status Queries"

  backend:
    - "Erstelle GroupQueryService mit create, publish, assign Methoden"
    - "Implementiere Evaluation-Logik mit Aggregation"
    - "Erstelle Reminder-Job für Deadline-Erinnerungen"

  checklists:
    - "Erweitere ChecklistTemplate für Konzern-Nutzung"
    - "Implementiere Response-Validierung"
    - "Erstelle Aggregations-Konfiguration"

  frontend:
    - "Erstelle GroupQueryListView und GroupQueryDetailView"
    - "Implementiere GroupQueryCard Komponente"
    - "Erstelle EvaluationDashboard mit Charts"

  reporting:
    - "Implementiere Konzern-Auswertungsberichte"
    - "Erstelle Vergleichs-Tabellen und Charts"
    - "Export als Excel/PDF"

# Prüfer-Schreibtisch
schreibtisch:
  database:
    - "Erstelle DocumentBox und BoxDocument Models"
    - "Füge AiVerificationResult als JSONB hinzu"
    - "Erstelle Indices für Status-Queries"

  backend:
    - "Erstelle DocumentBoxService"
    - "Implementiere File-Upload mit Thumbnail-Generierung"
    - "Erstelle FlowInvoice-Adapter"

  frontend:
    - "Erstelle AuditDeskView mit Drag & Drop"
    - "Implementiere DocumentBox Komponente"
    - "Erstelle AiVerificationPanel"

  api-client:
    - "Implementiere FlowInvoice API Client"
    - "Erstelle Response-Typen für KI-Ergebnisse"
    - "Error Handling für API-Timeouts"

# FlowNavigator
navigator:
  database:
    - "Erstelle Package, Tenant, Deployment Models"
    - "Füge Installation-JSONB für Mandanten hinzu"
    - "Erstelle DeploymentLog Table"

  backend:
    - "Erstelle PackageService mit npm Registry Integration"
    - "Implementiere TenantService mit Health-Checks"
    - "Erstelle DeploymentService mit Background-Tasks"

  frontend:
    - "Erstelle Navigator Dashboard"
    - "Implementiere PackageList und TenantGrid"
    - "Erstelle DeploymentWizard"

  backend:
    - "Implementiere Deployment-Engine"
    - "Erstelle Rollback-Mechanismus"
    - "Implementiere Backup & Restore"
```

### 4.3 Beispiel-Prompts für Agents

```bash
# Konzernansicht - Datenbank
claude "@database Erstelle eine Alembic Migration für das GroupQuery System:
- GroupQuery Tabelle mit tenant_id, title, deadline, status, checklist_template_id
- GroupQueryAssignment mit query_id, authority_id, status, progress, response_id
- GroupQueryResponse mit assignment_id, checklist_data (JSONB), summary_data (JSONB)
- GroupQueryAttachment für Dateianhänge
Berücksichtige Foreign Keys und Indices."

# Konzernansicht - Backend
claude "@backend Erstelle den GroupQueryService in app/services/group_query_service.py:
- list_queries(tenant_id, status, year)
- create_query(data, user)
- publish_query(query_id, user) - sendet an zugewiesene Behörden
- create_evaluation(query_id, include_pending) - aggregiert Daten
- send_reminders(query_id, authority_ids)
Nutze async/await und das Repository Pattern."

# Schreibtisch - Frontend
claude "@frontend Erstelle die DocumentBox.vue Komponente für den Prüfer-Schreibtisch:
- Drag & Drop Zone für Belege
- Grid-Ansicht mit Thumbnails
- Status-Anzeige (geprüft, abgelehnt, in Prüfung, offen)
- KI-Prüfung Button mit Loading-State
- Statistik-Leiste unten
Nutze Composition API, TypeScript und Tailwind CSS."

# FlowNavigator - Deployment
claude "@backend Implementiere den DeploymentService für FlowNavigator:
- execute_deployment(deployment_id) - Hauptmethode
- _validate_deployment - prüft Dependencies
- _deploy_package - installiert einzelnes Paket
- _run_migrations - führt DB-Migrationen aus
- _health_check - prüft System nach Deployment
- _execute_rollback - rollt bei Fehler zurück
Nutze Background Tasks und detailliertes Logging."
```

---

## Teil 5: npm Package-Struktur

```
@flowaudit/
├── core/
│   ├── common/          # Basis-Utilities, Typen
│   ├── validation/      # Validierungs-Funktionen
│   ├── calculations/    # Statistische Berechnungen
│   └── permissions/     # Berechtigungssystem
│
├── domain/
│   ├── fiscal-year/     # Prüfjahr-Verwaltung
│   ├── operations/      # Vorhaben/Projekte
│   ├── checklists/      # Prüflisten & Designer
│   ├── audit-cases/     # Prüfungsfälle
│   ├── findings/        # Feststellungen & Empfehlungen
│   ├── sampling/        # Stichprobenziehung
│   ├── projection/      # Hochrechnung
│   ├── group-queries/   # Konzern-Abfragen  ← NEU
│   └── system-audit/    # Systemprüfungen
│
├── reporting/
│   ├── report-engine/   # Berichts-Generator
│   ├── templates/       # Word-Templates
│   ├── text-modules/    # Textbausteine
│   ├── jkb/             # Jahreskontrollbericht
│   └── analytics/       # Auswertungen
│
├── documents/
│   ├── file-manager/    # Dateiverwaltung
│   ├── document-box/    # Belegkasten  ← NEU
│   ├── word-export/     # Word-Export
│   ├── excel-import/    # Excel-Import
│   └── flow-invoice/    # KI-Belegprüfung  ← NEU
│
├── adapters/
│   ├── vue-adapter/     # Vue 3 Komponenten
│   └── api-client/      # TypeScript API Client
│
└── navigator/           # FlowNavigator Tool  ← NEU
    ├── core/            # Navigator-Logik
    ├── deployment/      # Deployment-Engine
    └── ui/              # Navigator-UI
```

---

## Zusammenfassung

Diese Implementierungsplanung umfasst:

1. **Konzernansicht** - Vollständiges System für Konzern-Abfragen an Prüfbehörden mit Auswertungen
2. **Prüfer-Schreibtisch** - Belegkasten mit FlowInvoice KI-Integration
3. **FlowNavigator** - Administrations- und Deployment-Tool für npm-Module
4. **Agent-Zuordnung** - Klare Aufgabenverteilung für 8 spezialisierte Agents
5. **npm Package-Struktur** - Erweiterte Modulstruktur mit neuen Paketen

Die Implementierung ist in 5 Phasen unterteilt und nutzt die definierten Agents für eine effiziente Entwicklung.
