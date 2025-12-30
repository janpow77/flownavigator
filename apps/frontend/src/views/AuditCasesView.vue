<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  listAuditCases,
  getAuditStatistics,
  createAuditCase,
  type AuditCase,
  type AuditCaseStatistics,
} from '@/api/auditCases'

const router = useRouter()

// State
const cases = ref<AuditCase[]>([])
const statistics = ref<AuditCaseStatistics | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

// Pagination
const currentPage = ref(1)
const pageSize = ref(20)
const totalPages = ref(1)
const totalItems = ref(0)

// Filters
const searchQuery = ref('')
const statusFilter = ref('')
const typeFilter = ref('')

// Modal
const showCreateModal = ref(false)
const createLoading = ref(false)
const newCase = ref({
  case_number: '',
  project_name: '',
  beneficiary_name: '',
  audit_type: 'operation',
  approved_amount: undefined as number | undefined,
})

// Status colors
const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
  in_progress: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
  review: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  archived: 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300',
}

const typeColors: Record<string, string> = {
  operation: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
  system: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
  accounts: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-300',
}

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

// Computed
const filteredStats = computed(() => {
  if (!statistics.value) return { total: 0, draft: 0, in_progress: 0, completed: 0 }
  return {
    total: statistics.value.total,
    draft: statistics.value.by_status.draft || 0,
    in_progress: statistics.value.by_status.in_progress || 0,
    completed: statistics.value.by_status.completed || 0,
  }
})

// Methods
async function loadData() {
  loading.value = true
  error.value = null

  try {
    const [casesResponse, statsResponse] = await Promise.all([
      listAuditCases({
        page: currentPage.value,
        page_size: pageSize.value,
        status: statusFilter.value || undefined,
        audit_type: typeFilter.value || undefined,
        search: searchQuery.value || undefined,
      }),
      getAuditStatistics(),
    ])

    cases.value = casesResponse.items
    totalPages.value = casesResponse.pages
    totalItems.value = casesResponse.total
    statistics.value = statsResponse
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Fehler beim Laden der Daten'
    console.error('Error loading audit cases:', err)
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!newCase.value.case_number || !newCase.value.project_name || !newCase.value.beneficiary_name) {
    return
  }

  createLoading.value = true
  try {
    await createAuditCase({
      case_number: newCase.value.case_number,
      project_name: newCase.value.project_name,
      beneficiary_name: newCase.value.beneficiary_name,
      audit_type: newCase.value.audit_type,
      approved_amount: newCase.value.approved_amount,
    })

    showCreateModal.value = false
    newCase.value = {
      case_number: '',
      project_name: '',
      beneficiary_name: '',
      audit_type: 'operation',
      approved_amount: undefined,
    }
    await loadData()
  } catch (err) {
    console.error('Error creating audit case:', err)
    error.value = err instanceof Error ? err.message : 'Fehler beim Erstellen'
  } finally {
    createLoading.value = false
  }
}

function viewCase(caseId: string) {
  router.push({ name: 'audit-case-detail', params: { id: caseId } })
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

function formatAmount(amount: number | null): string {
  if (amount === null) return '-'
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
  }).format(amount)
}

// Watch filters
watch([searchQuery, statusFilter, typeFilter], () => {
  currentPage.value = 1
  loadData()
})

watch(currentPage, () => {
  loadData()
})

// Load on mount
onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Prüfungsfälle
        </h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Übersicht aller Vorhabenprüfungen
        </p>
      </div>
      <button class="btn-primary" @click="showCreateModal = true">
        <svg class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        Neuer Prüfungsfall
      </button>
    </div>

    <!-- Error Alert -->
    <div v-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
      <div class="flex">
        <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
        </svg>
        <div class="ml-3">
          <p class="text-sm text-red-700 dark:text-red-300">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-4">
      <div class="card p-4">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Gesamt</div>
        <div class="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
          {{ filteredStats.total }}
        </div>
      </div>
      <div class="card p-4">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Entwurf</div>
        <div class="mt-1 text-2xl font-semibold text-gray-600">
          {{ filteredStats.draft }}
        </div>
      </div>
      <div class="card p-4">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">In Bearbeitung</div>
        <div class="mt-1 text-2xl font-semibold text-yellow-600">
          {{ filteredStats.in_progress }}
        </div>
      </div>
      <div class="card p-4">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Abgeschlossen</div>
        <div class="mt-1 text-2xl font-semibold text-green-600">
          {{ filteredStats.completed }}
        </div>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="card">
      <div class="card-body flex flex-wrap gap-4">
        <div class="flex-1 min-w-[200px]">
          <input
            v-model="searchQuery"
            type="text"
            class="input"
            placeholder="Suche nach Fallnummer, Projekt oder Begünstigtem..."
          />
        </div>
        <select v-model="statusFilter" class="input w-auto">
          <option value="">Alle Status</option>
          <option value="draft">Entwurf</option>
          <option value="in_progress">In Bearbeitung</option>
          <option value="review">Prüfung</option>
          <option value="completed">Abgeschlossen</option>
          <option value="archived">Archiviert</option>
        </select>
        <select v-model="typeFilter" class="input w-auto">
          <option value="">Alle Typen</option>
          <option value="operation">Vorhabenprüfung</option>
          <option value="system">Systemprüfung</option>
          <option value="accounts">Rechnungslegung</option>
        </select>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <svg class="animate-spin h-8 w-8 text-accent-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
    </div>

    <!-- Table -->
    <div v-else-if="cases.length > 0" class="card overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead class="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Fallnummer
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Projekt / Begünstigter
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Typ
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Status
            </th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Betrag
            </th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Aktionen
            </th>
          </tr>
        </thead>
        <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          <tr
            v-for="auditCase in cases"
            :key="auditCase.id"
            class="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
            @click="viewCase(auditCase.id)"
          >
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm font-medium text-gray-900 dark:text-white">
                {{ auditCase.case_number }}
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400">
                {{ formatDate(auditCase.created_at) }}
              </div>
            </td>
            <td class="px-6 py-4">
              <div class="text-sm font-medium text-gray-900 dark:text-white">
                {{ auditCase.project_name }}
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400">
                {{ auditCase.beneficiary_name }}
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span :class="['px-2 py-1 text-xs font-medium rounded-full', typeColors[auditCase.audit_type] || 'bg-gray-100']">
                {{ typeLabels[auditCase.audit_type] || auditCase.audit_type }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span :class="['px-2 py-1 text-xs font-medium rounded-full', statusColors[auditCase.status] || 'bg-gray-100']">
                {{ statusLabels[auditCase.status] || auditCase.status }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right">
              <div class="text-sm text-gray-900 dark:text-white">
                {{ formatAmount(auditCase.approved_amount ? Number(auditCase.approved_amount) : null) }}
              </div>
              <div v-if="auditCase.irregular_amount" class="text-xs text-red-600 dark:text-red-400">
                {{ formatAmount(Number(auditCase.irregular_amount)) }} fehlerhaft
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm" @click.stop>
              <button
                class="text-accent-600 hover:text-accent-900 dark:text-accent-400 dark:hover:text-accent-300"
                @click="viewCase(auditCase.id)"
              >
                Öffnen
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="bg-gray-50 dark:bg-gray-800 px-4 py-3 flex items-center justify-between border-t border-gray-200 dark:border-gray-700">
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, totalItems) }} von {{ totalItems }}
        </div>
        <div class="flex gap-2">
          <button
            :disabled="currentPage <= 1"
            class="btn-secondary text-sm"
            :class="{ 'opacity-50 cursor-not-allowed': currentPage <= 1 }"
            @click="currentPage--"
          >
            Zurück
          </button>
          <button
            :disabled="currentPage >= totalPages"
            class="btn-secondary text-sm"
            :class="{ 'opacity-50 cursor-not-allowed': currentPage >= totalPages }"
            @click="currentPage++"
          >
            Weiter
          </button>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="card p-12 text-center">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
      <h3 class="mt-4 text-lg font-medium text-gray-900 dark:text-white">Keine Prüfungsfälle</h3>
      <p class="mt-2 text-gray-500 dark:text-gray-400">
        Erstellen Sie Ihren ersten Prüfungsfall.
      </p>
      <button class="btn-primary mt-4" @click="showCreateModal = true">
        Neuer Prüfungsfall
      </button>
    </div>

    <!-- Create Modal -->
    <Teleport to="body">
      <div v-if="showCreateModal" class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex min-h-screen items-center justify-center p-4">
          <!-- Backdrop -->
          <div class="fixed inset-0 bg-black/50" @click="showCreateModal = false" />

          <!-- Modal -->
          <div class="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-lg w-full p-6">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Neuer Prüfungsfall
            </h2>

            <form class="space-y-4" @submit.prevent="handleCreate">
              <div>
                <label class="label">Fallnummer *</label>
                <input
                  v-model="newCase.case_number"
                  type="text"
                  class="input"
                  placeholder="z.B. VH-2024-0001"
                  required
                />
              </div>

              <div>
                <label class="label">Projektname *</label>
                <input
                  v-model="newCase.project_name"
                  type="text"
                  class="input"
                  placeholder="Name des Vorhabens"
                  required
                />
              </div>

              <div>
                <label class="label">Begünstigter *</label>
                <input
                  v-model="newCase.beneficiary_name"
                  type="text"
                  class="input"
                  placeholder="Name des Begünstigten"
                  required
                />
              </div>

              <div>
                <label class="label">Prüfungsart</label>
                <select v-model="newCase.audit_type" class="input">
                  <option value="operation">Vorhabenprüfung</option>
                  <option value="system">Systemprüfung</option>
                  <option value="accounts">Rechnungslegungsprüfung</option>
                </select>
              </div>

              <div>
                <label class="label">Bewilligter Betrag</label>
                <input
                  v-model="newCase.approved_amount"
                  type="number"
                  class="input"
                  placeholder="0.00"
                  step="0.01"
                  min="0"
                />
              </div>

              <div class="flex justify-end gap-3 mt-6">
                <button
                  type="button"
                  class="btn-secondary"
                  @click="showCreateModal = false"
                >
                  Abbrechen
                </button>
                <button
                  type="submit"
                  class="btn-primary"
                  :disabled="createLoading"
                >
                  <svg v-if="createLoading" class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Erstellen
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
