<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getAuditCase, updateAuditCase, type AuditCase } from '@/api/auditCases'
import ChecklistPanel from '@/components/checklists/ChecklistPanel.vue'
import DocumentBoxPanel from '@/components/documents/DocumentBoxPanel.vue'

const props = defineProps<{
  id: string
}>()

const router = useRouter()

// State
const auditCase = ref<AuditCase | null>(null)
const loading = ref(true)
const saving = ref(false)
const error = ref<string | null>(null)

// Tabs
const activeTab = ref('overview')
const tabs = [
  { id: 'overview', label: 'Übersicht', icon: 'info' },
  { id: 'checklists', label: 'Checklisten', icon: 'checklist' },
  { id: 'findings', label: 'Feststellungen', icon: 'alert' },
  { id: 'documents', label: 'Dokumente', icon: 'folder' },
  { id: 'history', label: 'Verlauf', icon: 'clock' },
]

// Status/Type labels
const statusLabels: Record<string, string> = {
  draft: 'Entwurf',
  in_progress: 'In Bearbeitung',
  review: 'Prüfung',
  completed: 'Abgeschlossen',
  archived: 'Archiviert',
}

const typeLabels: Record<string, string> = {
  operation: 'Vorhabenprüfung',
  system: 'Systemprüfung',
  accounts: 'Rechnungslegung',
}

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
  in_progress: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
  review: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  archived: 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300',
}

// Methods
async function loadCase() {
  loading.value = true
  error.value = null

  try {
    auditCase.value = await getAuditCase(props.id)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Fehler beim Laden'
    console.error('Error loading audit case:', err)
  } finally {
    loading.value = false
  }
}

async function updateStatus(newStatus: string) {
  if (!auditCase.value) return

  saving.value = true
  try {
    auditCase.value = await updateAuditCase(props.id, { status: newStatus })
  } catch (err) {
    console.error('Error updating status:', err)
  } finally {
    saving.value = false
  }
}

function goBack() {
  router.push({ name: 'audit-cases' })
}

function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

function formatAmount(amount: number | string | null): string {
  if (amount === null) return '-'
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
  }).format(num)
}

onMounted(() => {
  loadCase()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Back Button & Header -->
    <div class="flex items-center gap-4">
      <button
        class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        @click="goBack"
      >
        <svg class="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
      </button>

      <div v-if="auditCase" class="flex-1">
        <div class="flex items-center gap-3">
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            {{ auditCase.case_number }}
          </h1>
          <span :class="['px-3 py-1 text-sm font-medium rounded-full', statusColors[auditCase.status]]">
            {{ statusLabels[auditCase.status] }}
          </span>
        </div>
        <p class="mt-1 text-gray-500 dark:text-gray-400">
          {{ auditCase.project_name }}
        </p>
      </div>

      <!-- Actions -->
      <div v-if="auditCase" class="flex items-center gap-2">
        <div class="relative">
          <select
            :value="auditCase.status"
            class="input w-auto pr-8"
            :disabled="saving"
            @change="updateStatus(($event.target as HTMLSelectElement).value)"
          >
            <option value="draft">Entwurf</option>
            <option value="in_progress">In Bearbeitung</option>
            <option value="review">Prüfung</option>
            <option value="completed">Abgeschlossen</option>
            <option value="archived">Archiviert</option>
          </select>
        </div>
        <button class="btn-primary">
          <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          Bearbeiten
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <svg class="animate-spin h-8 w-8 text-accent-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
      <p class="text-red-700 dark:text-red-300">{{ error }}</p>
      <button class="mt-2 text-sm text-red-600 hover:text-red-800" @click="goBack">
        Zurück zur Übersicht
      </button>
    </div>

    <!-- Content -->
    <template v-else-if="auditCase">
      <!-- Tabs -->
      <div class="border-b border-gray-200 dark:border-gray-700">
        <nav class="flex gap-6">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            :class="[
              'py-3 px-1 text-sm font-medium border-b-2 transition-colors',
              activeTab === tab.id
                ? 'border-accent-500 text-accent-600 dark:text-accent-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
            ]"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <!-- Tab Content: Overview -->
      <div v-if="activeTab === 'overview'" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Main Info -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Project Info -->
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Vorhaben</h3>
            </div>
            <div class="card-body">
              <dl class="grid grid-cols-2 gap-4">
                <div>
                  <dt class="text-sm text-gray-500 dark:text-gray-400">Projektname</dt>
                  <dd class="mt-1 text-gray-900 dark:text-white">{{ auditCase.project_name }}</dd>
                </div>
                <div>
                  <dt class="text-sm text-gray-500 dark:text-gray-400">Begünstigter</dt>
                  <dd class="mt-1 text-gray-900 dark:text-white">{{ auditCase.beneficiary_name }}</dd>
                </div>
                <div>
                  <dt class="text-sm text-gray-500 dark:text-gray-400">Prüfungsart</dt>
                  <dd class="mt-1 text-gray-900 dark:text-white">{{ typeLabels[auditCase.audit_type] }}</dd>
                </div>
                <div>
                  <dt class="text-sm text-gray-500 dark:text-gray-400">Externe ID</dt>
                  <dd class="mt-1 text-gray-900 dark:text-white">{{ auditCase.external_id || '-' }}</dd>
                </div>
              </dl>
            </div>
          </div>

          <!-- Financial Info -->
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Finanzdaten</h3>
            </div>
            <div class="card-body">
              <dl class="grid grid-cols-3 gap-4">
                <div>
                  <dt class="text-sm text-gray-500 dark:text-gray-400">Bewilligung</dt>
                  <dd class="mt-1 text-xl font-semibold text-gray-900 dark:text-white">
                    {{ formatAmount(auditCase.approved_amount) }}
                  </dd>
                </div>
                <div>
                  <dt class="text-sm text-gray-500 dark:text-gray-400">Geprüft</dt>
                  <dd class="mt-1 text-xl font-semibold text-gray-900 dark:text-white">
                    {{ formatAmount(auditCase.audited_amount) }}
                  </dd>
                </div>
                <div>
                  <dt class="text-sm text-gray-500 dark:text-gray-400">Fehlerhaft</dt>
                  <dd class="mt-1 text-xl font-semibold" :class="auditCase.irregular_amount ? 'text-red-600' : 'text-gray-900 dark:text-white'">
                    {{ formatAmount(auditCase.irregular_amount) }}
                  </dd>
                </div>
              </dl>
            </div>
          </div>

          <!-- Notes -->
          <div v-if="auditCase.internal_notes" class="card">
            <div class="card-header">
              <h3 class="card-title">Interne Notizen</h3>
            </div>
            <div class="card-body">
              <p class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                {{ auditCase.internal_notes }}
              </p>
            </div>
          </div>
        </div>

        <!-- Sidebar -->
        <div class="space-y-6">
          <!-- Dates -->
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Zeitraum</h3>
            </div>
            <div class="card-body space-y-3">
              <div class="flex justify-between">
                <span class="text-sm text-gray-500 dark:text-gray-400">Prüfungsbeginn</span>
                <span class="text-gray-900 dark:text-white">{{ formatDate(auditCase.audit_start_date) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-500 dark:text-gray-400">Prüfungsende</span>
                <span class="text-gray-900 dark:text-white">{{ formatDate(auditCase.audit_end_date) }}</span>
              </div>
              <div class="border-t border-gray-200 dark:border-gray-700 pt-3">
                <div class="flex justify-between">
                  <span class="text-sm text-gray-500 dark:text-gray-400">Erstellt</span>
                  <span class="text-gray-900 dark:text-white">{{ formatDate(auditCase.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Flags -->
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Kennzeichnungen</h3>
            </div>
            <div class="card-body space-y-2">
              <div class="flex items-center gap-2">
                <span :class="['w-3 h-3 rounded-full', auditCase.is_sample ? 'bg-blue-500' : 'bg-gray-300']" />
                <span class="text-sm text-gray-700 dark:text-gray-300">Stichprobe</span>
              </div>
              <div class="flex items-center gap-2">
                <span :class="['w-3 h-3 rounded-full', auditCase.requires_follow_up ? 'bg-amber-500' : 'bg-gray-300']" />
                <span class="text-sm text-gray-700 dark:text-gray-300">Nachverfolgung erforderlich</span>
              </div>
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Aktionen</h3>
            </div>
            <div class="card-body space-y-2">
              <button class="btn-secondary w-full justify-start">
                <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                </svg>
                Checkliste starten
              </button>
              <button class="btn-secondary w-full justify-start">
                <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Feststellung hinzufügen
              </button>
              <button class="btn-secondary w-full justify-start">
                <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                Dokument hochladen
              </button>
              <button class="btn-secondary w-full justify-start">
                <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                </svg>
                Bericht generieren
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab Content: Checklists -->
      <div v-else-if="activeTab === 'checklists'" class="card overflow-hidden" style="min-height: 500px;">
        <ChecklistPanel :case-id="id" />
      </div>

      <!-- Tab Content: Findings -->
      <div v-else-if="activeTab === 'findings'" class="card p-8 text-center">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h3 class="mt-4 text-lg font-medium text-gray-900 dark:text-white">Keine Feststellungen</h3>
        <p class="mt-2 text-gray-500 dark:text-gray-400">
          Es wurden noch keine Feststellungen erfasst.
        </p>
        <button class="btn-primary mt-4">
          Feststellung erfassen
        </button>
      </div>

      <!-- Tab Content: Documents -->
      <div v-else-if="activeTab === 'documents'" class="card overflow-hidden" style="min-height: 500px;">
        <DocumentBoxPanel :case-id="id" />
      </div>

      <!-- Tab Content: History -->
      <div v-else-if="activeTab === 'history'" class="card p-8 text-center">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="mt-4 text-lg font-medium text-gray-900 dark:text-white">Verlauf</h3>
        <p class="mt-2 text-gray-500 dark:text-gray-400">
          Die Änderungshistorie wird hier angezeigt.
        </p>
      </div>
    </template>
  </div>
</template>
