# Prüfer-Dashboard Design

> Übersicht über Prüfungen, Termine und Aufgaben für den angemeldeten Prüfer

## Layout-Struktur

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FlowAudit                              🔔 3   👤 Max Mustermann   ⚙️  🌙   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Guten Morgen, Max! 👋                                   📅 30. Dezember 2025│
│                                                                             │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐│
│  │  📋 Aktive     │ │  ⏰ Fällig     │ │  ⚠️ Überfällig │ │  ✅ Abgeschl.  ││
│  │     Prüfungen  │ │     diese Woche│ │     Termine    │ │     diesen Mon.││
│  │                │ │                │ │                │ │                ││
│  │      12        │ │       4        │ │       2        │ │       8        ││
│  └────────────────┘ └────────────────┘ └────────────────┘ └────────────────┘│
│                                                                             │
│  ┌──────────────────────────────────────────┐ ┌─────────────────────────────┐│
│  │  📅 Anstehende Termine                   │ │  📌 Meine Aufgaben          ││
│  │  ──────────────────────                  │ │  ──────────────────         ││
│  │                                          │ │                             ││
│  │  HEUTE                                   │ │  ☐ Bericht abschließen      ││
│  │  ┌────────────────────────────────────┐  │ │    → VH-2024-0234           ││
│  │  │ 10:00  Vor-Ort-Prüfung             │  │ │    ⏰ Fällig: Morgen        ││
│  │  │        Projekt ABC, München         │  │ │                             ││
│  │  │        📍 Musterstraße 123          │  │ │  ☐ Stellungnahme prüfen    ││
│  │  └────────────────────────────────────┘  │ │    → VH-2024-0189           ││
│  │                                          │ │    ⏰ Fällig: 02.01.2025    ││
│  │  ┌────────────────────────────────────┐  │ │                             ││
│  │  │ 14:00  Teambesprechung             │  │ │  ⚠️ Checkliste vervollst.  ││
│  │  │        Prüfungsplanung Q1/2025      │  │ │    → VH-2024-0156           ││
│  │  │        📍 Raum 4.12                 │  │ │    ⏰ Überfällig: 28.12.   ││
│  │  └────────────────────────────────────┘  │ │                             ││
│  │                                          │ │  + 5 weitere Aufgaben       ││
│  │  MORGEN                                  │ │                             ││
│  │  ┌────────────────────────────────────┐  │ └─────────────────────────────┘│
│  │  │ 09:00  Dokumentenprüfung           │  │                               │
│  │  │        Projekt XYZ                  │  │                               │
│  │  └────────────────────────────────────┘  │                               │
│  │                                          │                               │
│  │  [Alle Termine anzeigen →]               │                               │
│  └──────────────────────────────────────────┘                               │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────────┐│
│  │  📋 Meine aktiven Prüfungen                              [Filter ▼] [+] ││
│  │  ────────────────────────────────────────────────────────────────────────││
│  │                                                                          ││
│  │  ┌─────────────────────────────────────────────────────────────────────┐ ││
│  │  │ VH-2024-0234                                           In Arbeit 🟡 │ ││
│  │  │ Projekt: Digitalisierung Handwerk GmbH                              │ ││
│  │  │ Betrag: 125.000,00 €      Fonds: EFRE      Programm: OP Bayern      │ ││
│  │  │ ─────────────────────────────────────────────────────────────────── │ ││
│  │  │ Fortschritt: ████████████░░░░░░░░ 65%                               │ ││
│  │  │ 📝 Checkliste: 18/28    📄 Belege: 45/52    📁 Dokumente: 12       │ ││
│  │  │ ─────────────────────────────────────────────────────────────────── │ ││
│  │  │ 👤 1. Prüfer: Max Mustermann    👤 2. Prüfer: Anna Schmidt          │ ││
│  │  │ ⏰ Fällig: 15.01.2025                                               │ ││
│  │  │                                              [Öffnen →]             │ ││
│  │  └─────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                          ││
│  │  ┌─────────────────────────────────────────────────────────────────────┐ ││
│  │  │ VH-2024-0189                                         Stellungnahme 🟠│ ││
│  │  │ Projekt: Schulungszentrums Bayern e.V.                              │ ││
│  │  │ Betrag: 89.500,00 €       Fonds: ESF+     Programm: ESF+ Bayern     │ ││
│  │  │ ─────────────────────────────────────────────────────────────────── │ ││
│  │  │ Fortschritt: ████████████████████ 100%                              │ ││
│  │  │ ⚠️ Feststellungen: 2 offen    📝 Stellungnahme eingegangen          │ ││
│  │  │ ─────────────────────────────────────────────────────────────────── │ ││
│  │  │ 👤 1. Prüfer: Max Mustermann    👤 PTL: Peter Meier                 │ ││
│  │  │ ⏰ Stellungnahmefrist: 02.01.2025                                   │ ││
│  │  │                                              [Öffnen →]             │ ││
│  │  └─────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                          ││
│  │  [Alle 12 Prüfungen anzeigen →]                                         ││
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  ┌─────────────────────────────────────┐ ┌─────────────────────────────────┐│
│  │  📊 Meine Statistik                 │ │  🔔 Letzte Aktivitäten          ││
│  │  ─────────────────────              │ │  ────────────────────           ││
│  │                                     │ │                                 ││
│  │  Dieses Jahr                        │ │  vor 2 Std.                     ││
│  │  ├─ Abgeschlossen: 24               │ │  Anna Schmidt hat Stellungnahme ││
│  │  ├─ In Arbeit: 12                   │ │  zu VH-2024-0189 hochgeladen    ││
│  │  └─ Gesamt-Prüfvolumen: 3,2 Mio €   │ │                                 ││
│  │                                     │ │  vor 5 Std.                     ││
│  │  Durchschnittliche Fehlerquote      │ │  Neue Dokumente für VH-2024-0234││
│  │  ├─ Meine Prüfungen: 2,4%           │ │  verfügbar                      ││
│  │  └─ Team-Durchschnitt: 2,8%         │ │                                 ││
│  │                                     │ │  Gestern                        ││
│  │  [Detailstatistik →]                │ │  PTL Peter Meier hat Bericht    ││
│  │                                     │ │  VH-2024-0201 freigegeben       ││
│  └─────────────────────────────────────┘ └─────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Komponenten-Struktur

### DashboardView.vue

```vue
<template>
  <div class="dashboard">
    <!-- Header mit Begrüßung -->
    <DashboardHeader />

    <!-- KPI-Karten -->
    <div class="kpi-grid">
      <KpiCard
        :value="activeAudits"
        :label="$t('dashboard.activeAudits')"
        icon="clipboard-list"
        color="primary"
      />
      <KpiCard
        :value="dueThisWeek"
        :label="$t('dashboard.dueThisWeek')"
        icon="clock"
        color="warning"
      />
      <KpiCard
        :value="overdueCount"
        :label="$t('dashboard.overdue')"
        icon="alert-triangle"
        color="danger"
      />
      <KpiCard
        :value="completedThisMonth"
        :label="$t('dashboard.completedThisMonth')"
        icon="check-circle"
        color="success"
      />
    </div>

    <!-- Hauptbereich -->
    <div class="dashboard-main">
      <!-- Linke Spalte: Termine & Prüfungen -->
      <div class="dashboard-left">
        <UpcomingAppointments :appointments="appointments" />
        <ActiveAuditsTable :audits="activeAudits" />
      </div>

      <!-- Rechte Spalte: Aufgaben & Aktivitäten -->
      <div class="dashboard-right">
        <TaskList :tasks="myTasks" />
        <MyStatistics :stats="userStats" />
        <ActivityFeed :activities="recentActivities" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const dashboardStore = useDashboardStore()

onMounted(() => {
  dashboardStore.loadDashboardData()
})

const activeAudits = computed(() => dashboardStore.activeAudits)
const appointments = computed(() => dashboardStore.appointments)
const myTasks = computed(() => dashboardStore.tasks)
const userStats = computed(() => dashboardStore.statistics)
const recentActivities = computed(() => dashboardStore.activities)
</script>
```

### KpiCard.vue

```vue
<template>
  <div :class="['kpi-card', `kpi-card--${color}`]">
    <div class="kpi-card__icon">
      <component :is="iconComponent" />
    </div>
    <div class="kpi-card__content">
      <span class="kpi-card__value">{{ formattedValue }}</span>
      <span class="kpi-card__label">{{ label }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import * as LucideIcons from 'lucide-vue-next'

interface Props {
  value: number
  label: string
  icon: string
  color?: 'primary' | 'success' | 'warning' | 'danger'
}

const props = withDefaults(defineProps<Props>(), {
  color: 'primary'
})

const iconComponent = computed(() => {
  const iconName = props.icon
    .split('-')
    .map(s => s.charAt(0).toUpperCase() + s.slice(1))
    .join('')
  return LucideIcons[iconName as keyof typeof LucideIcons]
})

const formattedValue = computed(() => {
  return props.value.toLocaleString('de-DE')
})
</script>

<style scoped>
.kpi-card {
  @apply flex items-center gap-4 p-6 bg-white dark:bg-slate-800 rounded-xl shadow-sm;
  @apply border border-slate-200 dark:border-slate-700;
  @apply transition-all duration-200 hover:shadow-md;
}

.kpi-card__icon {
  @apply w-12 h-12 rounded-xl flex items-center justify-center;
}

.kpi-card--primary .kpi-card__icon {
  @apply bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400;
}

.kpi-card--success .kpi-card__icon {
  @apply bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400;
}

.kpi-card--warning .kpi-card__icon {
  @apply bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400;
}

.kpi-card--danger .kpi-card__icon {
  @apply bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400;
}

.kpi-card__value {
  @apply text-3xl font-bold text-slate-900 dark:text-white;
}

.kpi-card__label {
  @apply text-sm text-slate-500 dark:text-slate-400;
}
</style>
```

### AuditCard.vue

```vue
<template>
  <div class="audit-card" @click="openAudit">
    <!-- Header -->
    <div class="audit-card__header">
      <span class="audit-card__id">{{ audit.caseNumber }}</span>
      <StatusBadge :status="audit.status" />
    </div>

    <!-- Projektname -->
    <h3 class="audit-card__title">{{ audit.operationName }}</h3>

    <!-- Metadaten -->
    <div class="audit-card__meta">
      <span class="audit-card__amount">{{ formatCurrency(audit.amount) }}</span>
      <span class="audit-card__fund">{{ audit.fund }}</span>
      <span class="audit-card__program">{{ audit.program }}</span>
    </div>

    <!-- Fortschritt -->
    <div class="audit-card__progress">
      <ProgressBar :value="audit.progress" :showLabel="true" />
    </div>

    <!-- Statistiken -->
    <div class="audit-card__stats">
      <div class="stat">
        <ClipboardList class="stat-icon" />
        <span>{{ audit.checklistProgress }}</span>
      </div>
      <div class="stat">
        <FileText class="stat-icon" />
        <span>{{ audit.documentsProgress }}</span>
      </div>
      <div class="stat">
        <Folder class="stat-icon" />
        <span>{{ audit.filesCount }}</span>
      </div>
    </div>

    <!-- Footer -->
    <div class="audit-card__footer">
      <div class="audit-card__team">
        <UserAvatar :user="audit.primaryAuditor" size="sm" />
        <UserAvatar :user="audit.secondaryAuditor" size="sm" />
      </div>
      <div class="audit-card__due">
        <Clock class="w-4 h-4" />
        <span :class="{ 'text-red-500': isOverdue }">
          {{ formatDate(audit.dueDate) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ClipboardList, FileText, Folder, Clock } from 'lucide-vue-next'
import type { AuditCase } from '@/types'

interface Props {
  audit: AuditCase
}

const props = defineProps<Props>()
const router = useRouter()

const isOverdue = computed(() => {
  return new Date(props.audit.dueDate) < new Date()
})

function openAudit() {
  router.push({
    name: 'audit-desk',
    params: { id: props.audit.id }
  })
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR'
  }).format(amount)
}

function formatDate(date: string): string {
  return new Intl.DateTimeFormat('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  }).format(new Date(date))
}
</script>

<style scoped>
.audit-card {
  @apply p-5 bg-white dark:bg-slate-800 rounded-xl;
  @apply border border-slate-200 dark:border-slate-700;
  @apply cursor-pointer transition-all duration-200;
  @apply hover:shadow-lg hover:border-primary-300 dark:hover:border-primary-600;
}

.audit-card__header {
  @apply flex justify-between items-center mb-2;
}

.audit-card__id {
  @apply text-sm font-mono text-slate-500 dark:text-slate-400;
}

.audit-card__title {
  @apply text-lg font-semibold text-slate-900 dark:text-white mb-3;
  @apply line-clamp-2;
}

.audit-card__meta {
  @apply flex gap-3 text-sm text-slate-500 dark:text-slate-400 mb-4;
}

.audit-card__stats {
  @apply flex gap-4 text-sm text-slate-600 dark:text-slate-300 mb-4;
}

.stat {
  @apply flex items-center gap-1.5;
}

.stat-icon {
  @apply w-4 h-4 text-slate-400;
}

.audit-card__footer {
  @apply flex justify-between items-center pt-4;
  @apply border-t border-slate-100 dark:border-slate-700;
}

.audit-card__team {
  @apply flex -space-x-2;
}

.audit-card__due {
  @apply flex items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400;
}
</style>
```

### UpcomingAppointments.vue

```vue
<template>
  <div class="appointments-card">
    <div class="appointments-card__header">
      <h2 class="appointments-card__title">
        <Calendar class="w-5 h-5" />
        {{ $t('dashboard.upcomingAppointments') }}
      </h2>
    </div>

    <div class="appointments-list">
      <template v-for="(dayGroup, date) in groupedAppointments" :key="date">
        <div class="day-header">
          <span class="day-label">{{ formatDayLabel(date) }}</span>
          <span class="day-date">{{ formatDate(date) }}</span>
        </div>

        <div
          v-for="appointment in dayGroup"
          :key="appointment.id"
          class="appointment-item"
          :class="[`appointment-item--${appointment.type}`]"
        >
          <div class="appointment-time">
            {{ formatTime(appointment.startTime) }}
          </div>
          <div class="appointment-content">
            <span class="appointment-title">{{ appointment.title }}</span>
            <span class="appointment-subtitle">{{ appointment.subtitle }}</span>
            <div v-if="appointment.location" class="appointment-location">
              <MapPin class="w-3.5 h-3.5" />
              {{ appointment.location }}
            </div>
          </div>
          <div class="appointment-actions">
            <button class="btn-icon" @click="viewDetails(appointment)">
              <ChevronRight class="w-4 h-4" />
            </button>
          </div>
        </div>
      </template>
    </div>

    <router-link to="/calendar" class="view-all-link">
      {{ $t('dashboard.viewAllAppointments') }}
      <ArrowRight class="w-4 h-4" />
    </router-link>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Calendar, MapPin, ChevronRight, ArrowRight } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import type { Appointment } from '@/types'

interface Props {
  appointments: Appointment[]
}

const props = defineProps<Props>()
const { t, d } = useI18n()

const groupedAppointments = computed(() => {
  const groups: Record<string, Appointment[]> = {}

  for (const apt of props.appointments) {
    const date = apt.startTime.split('T')[0]
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(apt)
  }

  return groups
})

function formatDayLabel(dateStr: string): string {
  const date = new Date(dateStr)
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)

  if (date.toDateString() === today.toDateString()) {
    return t('common.today')
  }
  if (date.toDateString() === tomorrow.toDateString()) {
    return t('common.tomorrow')
  }

  return d(date, 'weekday')
}

function formatDate(dateStr: string): string {
  return new Intl.DateTimeFormat('de-DE', {
    day: '2-digit',
    month: '2-digit'
  }).format(new Date(dateStr))
}

function formatTime(datetime: string): string {
  return new Intl.DateTimeFormat('de-DE', {
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(datetime))
}
</script>

<style scoped>
.appointments-card {
  @apply bg-white dark:bg-slate-800 rounded-xl;
  @apply border border-slate-200 dark:border-slate-700;
  @apply overflow-hidden;
}

.appointments-card__header {
  @apply px-6 py-4 border-b border-slate-100 dark:border-slate-700;
}

.appointments-card__title {
  @apply flex items-center gap-2 text-lg font-semibold;
  @apply text-slate-900 dark:text-white;
}

.appointments-list {
  @apply p-4 space-y-2;
}

.day-header {
  @apply flex justify-between items-center px-2 py-2;
  @apply text-xs font-medium text-slate-500 dark:text-slate-400 uppercase;
}

.appointment-item {
  @apply flex gap-3 p-3 rounded-lg;
  @apply bg-slate-50 dark:bg-slate-700/50;
  @apply border-l-4 transition-colors;
}

.appointment-item--site-visit {
  @apply border-l-blue-500;
}

.appointment-item--meeting {
  @apply border-l-purple-500;
}

.appointment-item--deadline {
  @apply border-l-red-500;
}

.appointment-item--document-review {
  @apply border-l-green-500;
}

.appointment-time {
  @apply text-sm font-medium text-slate-700 dark:text-slate-300;
  @apply w-12 flex-shrink-0;
}

.appointment-content {
  @apply flex-1 min-w-0;
}

.appointment-title {
  @apply block font-medium text-slate-900 dark:text-white;
}

.appointment-subtitle {
  @apply block text-sm text-slate-500 dark:text-slate-400;
}

.appointment-location {
  @apply flex items-center gap-1 text-xs text-slate-400 mt-1;
}

.view-all-link {
  @apply flex items-center justify-center gap-2 px-6 py-3;
  @apply text-sm font-medium text-primary-600 dark:text-primary-400;
  @apply border-t border-slate-100 dark:border-slate-700;
  @apply hover:bg-slate-50 dark:hover:bg-slate-700/50;
  @apply transition-colors;
}
</style>
```

## Datenmodell

### Dashboard Types

```typescript
// types/dashboard.ts

export interface DashboardData {
  kpis: DashboardKpis
  appointments: Appointment[]
  tasks: Task[]
  audits: AuditSummary[]
  statistics: UserStatistics
  activities: Activity[]
}

export interface DashboardKpis {
  activeAudits: number
  dueThisWeek: number
  overdueCount: number
  completedThisMonth: number
}

export interface Appointment {
  id: string
  type: 'site_visit' | 'meeting' | 'deadline' | 'document_review'
  title: string
  subtitle?: string
  startTime: string
  endTime?: string
  location?: string
  auditCaseId?: string
  isAllDay: boolean
}

export interface Task {
  id: string
  type: 'checklist' | 'report' | 'response' | 'review' | 'follow_up'
  title: string
  description?: string
  auditCaseId: string
  auditCaseNumber: string
  dueDate: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  isOverdue: boolean
  completedAt?: string
}

export interface AuditSummary {
  id: string
  caseNumber: string
  operationName: string
  amount: number
  fund: string
  program: string
  status: AuditStatus
  progress: number
  checklistProgress: string // z.B. "18/28"
  documentsProgress: string // z.B. "45/52"
  filesCount: number
  primaryAuditor: UserSummary
  secondaryAuditor?: UserSummary
  teamLeader?: UserSummary
  dueDate: string
  findingsCount: number
  openFindingsCount: number
}

export type AuditStatus =
  | 'planned'           // Geplant
  | 'in_progress'       // In Arbeit
  | 'awaiting_response' // Stellungnahme ausstehend
  | 'review'            // In Prüfung (PTL)
  | 'approval'          // Zur Freigabe (PBL)
  | 'completed'         // Abgeschlossen
  | 'follow_up'         // Nachverfolgung

export interface UserStatistics {
  currentYear: {
    completed: number
    inProgress: number
    totalVolume: number
  }
  errorRates: {
    own: number
    teamAverage: number
  }
  trend: {
    completedLastMonth: number
    completedThisMonth: number
  }
}

export interface Activity {
  id: string
  type: 'document_upload' | 'status_change' | 'comment' | 'finding' | 'approval'
  message: string
  timestamp: string
  user: UserSummary
  auditCaseId?: string
  auditCaseNumber?: string
}

export interface UserSummary {
  id: string
  name: string
  initials: string
  avatarUrl?: string
  role: 'auditor' | 'team_leader' | 'authority_head'
}
```

## API Endpoints

```python
# backend/app/api/dashboard.py

from fastapi import APIRouter, Depends
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService
from app.core.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    current_user = Depends(get_current_user),
    service: DashboardService = Depends()
):
    """
    Lädt alle Dashboard-Daten für den angemeldeten Prüfer:
    - KPIs (aktive, fällige, überfällige, abgeschlossene Prüfungen)
    - Anstehende Termine (7 Tage)
    - Offene Aufgaben
    - Aktive Prüfungen (max. 10)
    - Statistiken
    - Letzte Aktivitäten
    """
    return await service.get_dashboard_data(current_user.id)

@router.get("/appointments")
async def get_appointments(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user = Depends(get_current_user),
    service: DashboardService = Depends()
):
    """Termine für Datumsbereich laden"""
    return await service.get_appointments(
        current_user.id,
        start_date,
        end_date
    )

@router.get("/tasks")
async def get_tasks(
    status: Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    service: DashboardService = Depends()
):
    """Aufgabenliste laden"""
    return await service.get_tasks(current_user.id, status)

@router.patch("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    current_user = Depends(get_current_user),
    service: DashboardService = Depends()
):
    """Aufgabe als erledigt markieren"""
    return await service.complete_task(task_id, current_user.id)
```

## Pinia Store

```typescript
// stores/dashboard.ts

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { dashboardService } from '@/services/dashboardService'
import type { DashboardData, Task, Appointment } from '@/types'

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const data = ref<DashboardData | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdated = ref<Date | null>(null)

  // Getters
  const kpis = computed(() => data.value?.kpis)
  const appointments = computed(() => data.value?.appointments ?? [])
  const tasks = computed(() => data.value?.tasks ?? [])
  const audits = computed(() => data.value?.audits ?? [])
  const statistics = computed(() => data.value?.statistics)
  const activities = computed(() => data.value?.activities ?? [])

  const overdueTasks = computed(() =>
    tasks.value.filter(t => t.isOverdue && !t.completedAt)
  )

  const todayAppointments = computed(() => {
    const today = new Date().toISOString().split('T')[0]
    return appointments.value.filter(a =>
      a.startTime.startsWith(today)
    )
  })

  // Actions
  async function loadDashboardData() {
    isLoading.value = true
    error.value = null

    try {
      data.value = await dashboardService.getDashboard()
      lastUpdated.value = new Date()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Fehler beim Laden'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function refreshData() {
    await loadDashboardData()
  }

  async function completeTask(taskId: string) {
    await dashboardService.completeTask(taskId)

    // Optimistic update
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      task.completedAt = new Date().toISOString()
    }
  }

  // Auto-refresh alle 5 Minuten
  let refreshInterval: number | null = null

  function startAutoRefresh() {
    refreshInterval = window.setInterval(() => {
      refreshData()
    }, 5 * 60 * 1000)
  }

  function stopAutoRefresh() {
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  }

  return {
    // State
    data,
    isLoading,
    error,
    lastUpdated,

    // Getters
    kpis,
    appointments,
    tasks,
    audits,
    statistics,
    activities,
    overdueTasks,
    todayAppointments,

    // Actions
    loadDashboardData,
    refreshData,
    completeTask,
    startAutoRefresh,
    stopAutoRefresh
  }
})
```

## Internationalisierung

```typescript
// locales/de.ts
export default {
  dashboard: {
    greeting: 'Guten {timeOfDay}, {name}!',
    activeAudits: 'Aktive Prüfungen',
    dueThisWeek: 'Fällig diese Woche',
    overdue: 'Überfällig',
    completedThisMonth: 'Abgeschlossen diesen Monat',
    upcomingAppointments: 'Anstehende Termine',
    viewAllAppointments: 'Alle Termine anzeigen',
    myTasks: 'Meine Aufgaben',
    myAudits: 'Meine aktiven Prüfungen',
    viewAllAudits: 'Alle {count} Prüfungen anzeigen',
    myStatistics: 'Meine Statistik',
    recentActivities: 'Letzte Aktivitäten',
    thisYear: 'Dieses Jahr',
    completed: 'Abgeschlossen',
    inProgress: 'In Arbeit',
    totalVolume: 'Gesamt-Prüfvolumen',
    errorRate: 'Durchschnittliche Fehlerquote',
    myAudits: 'Meine Prüfungen',
    teamAverage: 'Team-Durchschnitt',
    detailedStats: 'Detailstatistik'
  },
  audit: {
    status: {
      planned: 'Geplant',
      in_progress: 'In Arbeit',
      awaiting_response: 'Stellungnahme',
      review: 'In Prüfung',
      approval: 'Zur Freigabe',
      completed: 'Abgeschlossen',
      follow_up: 'Nachverfolgung'
    }
  },
  common: {
    today: 'Heute',
    tomorrow: 'Morgen',
    due: 'Fällig',
    overdue: 'Überfällig',
    open: 'Öffnen'
  }
}

// locales/en.ts
export default {
  dashboard: {
    greeting: 'Good {timeOfDay}, {name}!',
    activeAudits: 'Active Audits',
    dueThisWeek: 'Due This Week',
    overdue: 'Overdue',
    completedThisMonth: 'Completed This Month',
    upcomingAppointments: 'Upcoming Appointments',
    viewAllAppointments: 'View All Appointments',
    myTasks: 'My Tasks',
    myAudits: 'My Active Audits',
    viewAllAudits: 'View All {count} Audits',
    myStatistics: 'My Statistics',
    recentActivities: 'Recent Activities',
    thisYear: 'This Year',
    completed: 'Completed',
    inProgress: 'In Progress',
    totalVolume: 'Total Audit Volume',
    errorRate: 'Average Error Rate',
    myAudits: 'My Audits',
    teamAverage: 'Team Average',
    detailedStats: 'Detailed Statistics'
  },
  audit: {
    status: {
      planned: 'Planned',
      in_progress: 'In Progress',
      awaiting_response: 'Awaiting Response',
      review: 'Under Review',
      approval: 'Pending Approval',
      completed: 'Completed',
      follow_up: 'Follow-Up'
    }
  },
  common: {
    today: 'Today',
    tomorrow: 'Tomorrow',
    due: 'Due',
    overdue: 'Overdue',
    open: 'Open'
  }
}
```
