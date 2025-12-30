<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  listFindings,
  createFinding,
  updateFinding,
  deleteFinding,
  confirmFinding,
  resolveFinding,
  type Finding,
  type FindingCreate,
  type FindingType,
  type FindingStatus,
  type ErrorCategory,
  FINDING_TYPE_LABELS,
  FINDING_STATUS_LABELS,
  ERROR_CATEGORY_LABELS,
  FINDING_TYPE_COLORS,
  FINDING_STATUS_COLORS,
  formatCurrency,
} from '@/api/findings'

const props = defineProps<{
  caseId: string
}>()

// State
const findings = ref<Finding[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

// Modal State
const showAddModal = ref(false)
const showEditModal = ref(false)
const showDetailModal = ref(false)
const selectedFinding = ref<Finding | null>(null)
const saving = ref(false)

// Form State
const formData = ref<FindingCreate>({
  finding_type: 'deficiency',
  error_category: null,
  title: '',
  description: '',
  financial_impact: null,
  is_systemic: false,
  response_requested: false,
  response_deadline: null,
})

// Filters
const filterStatus = ref<FindingStatus | ''>('')
const filterType = ref<FindingType | ''>('')

// Computed
const filteredFindings = computed(() => {
  return findings.value.filter((f) => {
    if (filterStatus.value && f.status !== filterStatus.value) return false
    if (filterType.value && f.finding_type !== filterType.value) return false
    return true
  })
})

const summary = computed(() => {
  const total = findings.value.length
  const byStatus: Record<string, number> = {}
  const byType: Record<string, number> = {}
  let totalImpact = 0

  for (const f of findings.value) {
    byStatus[f.status] = (byStatus[f.status] || 0) + 1
    byType[f.finding_type] = (byType[f.finding_type] || 0) + 1
    if (f.financial_impact) totalImpact += f.financial_impact
  }

  return { total, byStatus, byType, totalImpact }
})

// Methods
async function loadFindings() {
  loading.value = true
  error.value = null

  try {
    findings.value = await listFindings(props.caseId)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Fehler beim Laden'
    console.error('Error loading findings:', err)
  } finally {
    loading.value = false
  }
}

function resetForm() {
  formData.value = {
    finding_type: 'deficiency',
    error_category: null,
    title: '',
    description: '',
    financial_impact: null,
    is_systemic: false,
    response_requested: false,
    response_deadline: null,
  }
}

function openAddModal() {
  resetForm()
  showAddModal.value = true
}

function openEditModal(finding: Finding) {
  selectedFinding.value = finding
  formData.value = {
    finding_type: finding.finding_type,
    error_category: finding.error_category,
    title: finding.title,
    description: finding.description,
    financial_impact: finding.financial_impact,
    is_systemic: finding.is_systemic,
    response_requested: finding.response_requested,
    response_deadline: finding.response_deadline,
  }
  showEditModal.value = true
}

function openDetailModal(finding: Finding) {
  selectedFinding.value = finding
  showDetailModal.value = true
}

async function handleCreate() {
  if (!formData.value.title || !formData.value.description) return

  saving.value = true
  error.value = null

  try {
    await createFinding(props.caseId, formData.value)
    showAddModal.value = false
    resetForm()
    await loadFindings()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Fehler beim Erstellen'
    console.error('Error creating finding:', err)
  } finally {
    saving.value = false
  }
}

async function handleUpdate() {
  if (!selectedFinding.value) return

  saving.value = true
  error.value = null

  try {
    await updateFinding(props.caseId, selectedFinding.value.id, formData.value)
    showEditModal.value = false
    selectedFinding.value = null
    await loadFindings()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Fehler beim Speichern'
    console.error('Error updating finding:', err)
  } finally {
    saving.value = false
  }
}

async function handleDelete(finding: Finding) {
  if (!confirm(`Möchten Sie die Feststellung "${finding.title}" wirklich löschen?`)) return

  try {
    await deleteFinding(props.caseId, finding.id)
    await loadFindings()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Fehler beim Löschen'
    console.error('Error deleting finding:', err)
  }
}

async function handleConfirm(finding: Finding) {
  try {
    await confirmFinding(props.caseId, finding.id)
    await loadFindings()
    if (showDetailModal.value && selectedFinding.value?.id === finding.id) {
      selectedFinding.value = findings.value.find((f) => f.id === finding.id) || null
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Fehler beim Bestätigen'
    console.error('Error confirming finding:', err)
  }
}

async function handleResolve(finding: Finding) {
  const action = prompt('Korrekturmaßnahme (optional):')
  try {
    await resolveFinding(props.caseId, finding.id, action || undefined)
    await loadFindings()
    if (showDetailModal.value && selectedFinding.value?.id === finding.id) {
      selectedFinding.value = findings.value.find((f) => f.id === finding.id) || null
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Fehler beim Beheben'
    console.error('Error resolving finding:', err)
  }
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

// Lifecycle
onMounted(() => {
  loadFindings()
})
</script>

<template>
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Feststellungen</h3>
      <button class="btn-primary" @click="openAddModal">
        <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 6v6m0 0v6m0-6h6m-6 0H6"
          />
        </svg>
        Feststellung erfassen
      </button>
    </div>

    <!-- Summary Cards -->
    <div v-if="findings.length > 0" class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="card p-4">
        <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ summary.total }}</div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Gesamt</div>
      </div>
      <div class="card p-4">
        <div class="text-2xl font-bold text-red-600 dark:text-red-400">
          {{ summary.byType['irregularity'] || 0 }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Unregelmäßigkeiten</div>
      </div>
      <div class="card p-4">
        <div class="text-2xl font-bold text-green-600 dark:text-green-400">
          {{ summary.byStatus['resolved'] || 0 }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Behoben</div>
      </div>
      <div class="card p-4">
        <div class="text-2xl font-bold text-accent-600 dark:text-accent-400">
          {{ formatCurrency(summary.totalImpact) }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Finanzielle Auswirkung</div>
      </div>
    </div>

    <!-- Filters -->
    <div v-if="findings.length > 0" class="flex gap-4">
      <select v-model="filterType" class="input w-auto">
        <option value="">Alle Typen</option>
        <option v-for="(label, key) in FINDING_TYPE_LABELS" :key="key" :value="key">
          {{ label }}
        </option>
      </select>
      <select v-model="filterStatus" class="input w-auto">
        <option value="">Alle Status</option>
        <option v-for="(label, key) in FINDING_STATUS_LABELS" :key="key" :value="key">
          {{ label }}
        </option>
      </select>
    </div>

    <!-- Error -->
    <div
      v-if="error"
      class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4"
    >
      <p class="text-red-700 dark:text-red-300">{{ error }}</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <svg class="animate-spin h-8 w-8 text-accent-600" fill="none" viewBox="0 0 24 24">
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
    </div>

    <!-- Findings List -->
    <div v-else-if="filteredFindings.length > 0" class="space-y-4">
      <div
        v-for="finding in filteredFindings"
        :key="finding.id"
        class="card p-4 hover:shadow-md transition-shadow cursor-pointer"
        @click="openDetailModal(finding)"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <span class="text-sm font-mono text-gray-500 dark:text-gray-400">
                #{{ finding.finding_number }}
              </span>
              <span
                :class="[
                  'px-2 py-0.5 text-xs font-medium rounded-full',
                  FINDING_TYPE_COLORS[finding.finding_type],
                ]"
              >
                {{ FINDING_TYPE_LABELS[finding.finding_type] }}
              </span>
              <span
                :class="[
                  'px-2 py-0.5 text-xs font-medium rounded-full',
                  FINDING_STATUS_COLORS[finding.status],
                ]"
              >
                {{ FINDING_STATUS_LABELS[finding.status] }}
              </span>
              <span
                v-if="finding.is_systemic"
                class="px-2 py-0.5 text-xs font-medium rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300"
              >
                Systemisch
              </span>
            </div>
            <h4 class="font-medium text-gray-900 dark:text-white">{{ finding.title }}</h4>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
              {{ finding.description }}
            </p>
            <div class="flex items-center gap-4 mt-3 text-sm text-gray-500 dark:text-gray-400">
              <span v-if="finding.financial_impact">
                {{ formatCurrency(finding.financial_impact) }}
              </span>
              <span v-if="finding.error_category">
                {{ ERROR_CATEGORY_LABELS[finding.error_category] }}
              </span>
              <span>Erstellt: {{ formatDate(finding.created_at) }}</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 ml-4" @click.stop>
            <button
              v-if="finding.status === 'draft'"
              class="p-2 text-green-500 hover:text-green-600 rounded-lg hover:bg-green-50 dark:hover:bg-green-900/20"
              title="Bestätigen"
              @click="handleConfirm(finding)"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </button>
            <button
              v-if="finding.status === 'confirmed' || finding.status === 'disputed'"
              class="p-2 text-blue-500 hover:text-blue-600 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20"
              title="Als behoben markieren"
              @click="handleResolve(finding)"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </button>
            <button
              v-if="finding.status === 'draft'"
              class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
              title="Bearbeiten"
              @click="openEditModal(finding)"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
            </button>
            <button
              v-if="finding.status === 'draft'"
              class="p-2 text-red-400 hover:text-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
              title="Löschen"
              @click="handleDelete(finding)"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="card p-12 text-center">
      <svg
        class="mx-auto h-12 w-12 text-gray-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
      <h3 class="mt-4 text-lg font-medium text-gray-900 dark:text-white">Keine Feststellungen</h3>
      <p class="mt-2 text-gray-500 dark:text-gray-400">
        Es wurden noch keine Feststellungen erfasst.
      </p>
      <button class="btn-primary mt-4" @click="openAddModal">Feststellung erfassen</button>
    </div>

    <!-- Add/Edit Modal -->
    <Teleport to="body">
      <div v-if="showAddModal || showEditModal" class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex min-h-screen items-center justify-center p-4">
          <div class="fixed inset-0 bg-black/50" @click="showAddModal = showEditModal = false" />

          <div
            class="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto"
          >
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              {{ showEditModal ? 'Feststellung bearbeiten' : 'Neue Feststellung' }}
            </h2>

            <form class="space-y-4" @submit.prevent="showEditModal ? handleUpdate() : handleCreate()">
              <!-- Type & Category -->
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="label">Typ *</label>
                  <select v-model="formData.finding_type" class="input" required>
                    <option
                      v-for="(label, key) in FINDING_TYPE_LABELS"
                      :key="key"
                      :value="key"
                    >
                      {{ label }}
                    </option>
                  </select>
                </div>
                <div>
                  <label class="label">Fehlerkategorie</label>
                  <select v-model="formData.error_category" class="input">
                    <option :value="null">Keine</option>
                    <option
                      v-for="(label, key) in ERROR_CATEGORY_LABELS"
                      :key="key"
                      :value="key"
                    >
                      {{ label }}
                    </option>
                  </select>
                </div>
              </div>

              <!-- Title -->
              <div>
                <label class="label">Titel *</label>
                <input
                  v-model="formData.title"
                  type="text"
                  class="input"
                  placeholder="Kurze Beschreibung der Feststellung"
                  required
                  maxlength="500"
                />
              </div>

              <!-- Description -->
              <div>
                <label class="label">Beschreibung *</label>
                <textarea
                  v-model="formData.description"
                  class="input"
                  rows="4"
                  placeholder="Ausführliche Beschreibung der Feststellung..."
                  required
                />
              </div>

              <!-- Financial Impact & Systemic -->
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="label">Finanzielle Auswirkung (EUR)</label>
                  <input
                    v-model.number="formData.financial_impact"
                    type="number"
                    step="0.01"
                    min="0"
                    class="input"
                    placeholder="0.00"
                  />
                </div>
                <div class="flex items-center pt-7">
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input
                      v-model="formData.is_systemic"
                      type="checkbox"
                      class="w-4 h-4 rounded border-gray-300 text-accent-600 focus:ring-accent-500"
                    />
                    <span class="text-sm text-gray-700 dark:text-gray-300">
                      Systemischer Fehler
                    </span>
                  </label>
                </div>
              </div>

              <!-- Response Requested -->
              <div class="grid grid-cols-2 gap-4">
                <div class="flex items-center">
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input
                      v-model="formData.response_requested"
                      type="checkbox"
                      class="w-4 h-4 rounded border-gray-300 text-accent-600 focus:ring-accent-500"
                    />
                    <span class="text-sm text-gray-700 dark:text-gray-300">
                      Stellungnahme anfordern
                    </span>
                  </label>
                </div>
                <div v-if="formData.response_requested">
                  <label class="label">Frist</label>
                  <input v-model="formData.response_deadline" type="date" class="input" />
                </div>
              </div>

              <div class="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  class="btn-secondary"
                  @click="showAddModal = showEditModal = false"
                >
                  Abbrechen
                </button>
                <button type="submit" class="btn-primary" :disabled="saving">
                  <svg
                    v-if="saving"
                    class="animate-spin -ml-1 mr-2 h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      class="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      stroke-width="4"
                    />
                    <path
                      class="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  {{ showEditModal ? 'Speichern' : 'Erstellen' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Detail Modal -->
    <Teleport to="body">
      <div v-if="showDetailModal && selectedFinding" class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex min-h-screen items-center justify-center p-4">
          <div class="fixed inset-0 bg-black/50" @click="showDetailModal = false" />

          <div
            class="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto"
          >
            <div class="flex items-start justify-between mb-4">
              <div class="flex items-center gap-3">
                <span class="text-lg font-mono text-gray-500 dark:text-gray-400">
                  #{{ selectedFinding.finding_number }}
                </span>
                <span
                  :class="[
                    'px-2 py-0.5 text-xs font-medium rounded-full',
                    FINDING_TYPE_COLORS[selectedFinding.finding_type],
                  ]"
                >
                  {{ FINDING_TYPE_LABELS[selectedFinding.finding_type] }}
                </span>
                <span
                  :class="[
                    'px-2 py-0.5 text-xs font-medium rounded-full',
                    FINDING_STATUS_COLORS[selectedFinding.status],
                  ]"
                >
                  {{ FINDING_STATUS_LABELS[selectedFinding.status] }}
                </span>
              </div>
              <button
                class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
                @click="showDetailModal = false"
              >
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              {{ selectedFinding.title }}
            </h2>

            <div class="space-y-4">
              <!-- Description -->
              <div>
                <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  Beschreibung
                </h4>
                <p class="text-gray-900 dark:text-white whitespace-pre-wrap">
                  {{ selectedFinding.description }}
                </p>
              </div>

              <!-- Details Grid -->
              <div class="grid grid-cols-2 gap-4">
                <div v-if="selectedFinding.error_category">
                  <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Fehlerkategorie
                  </h4>
                  <p class="text-gray-900 dark:text-white">
                    {{ ERROR_CATEGORY_LABELS[selectedFinding.error_category] }}
                  </p>
                </div>
                <div v-if="selectedFinding.financial_impact">
                  <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Finanzielle Auswirkung
                  </h4>
                  <p class="text-gray-900 dark:text-white font-semibold">
                    {{ formatCurrency(selectedFinding.financial_impact) }}
                  </p>
                </div>
                <div>
                  <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Systemischer Fehler
                  </h4>
                  <p class="text-gray-900 dark:text-white">
                    {{ selectedFinding.is_systemic ? 'Ja' : 'Nein' }}
                  </p>
                </div>
                <div>
                  <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Erstellt am
                  </h4>
                  <p class="text-gray-900 dark:text-white">
                    {{ formatDate(selectedFinding.created_at) }}
                  </p>
                </div>
              </div>

              <!-- Response Section -->
              <div
                v-if="selectedFinding.response_requested"
                class="border-t border-gray-200 dark:border-gray-700 pt-4"
              >
                <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                  Stellungnahme
                </h4>
                <div class="grid grid-cols-2 gap-4">
                  <div v-if="selectedFinding.response_deadline">
                    <span class="text-sm text-gray-500 dark:text-gray-400">Frist:</span>
                    <span class="ml-2 text-gray-900 dark:text-white">
                      {{ formatDate(selectedFinding.response_deadline) }}
                    </span>
                  </div>
                  <div v-if="selectedFinding.response_received_at">
                    <span class="text-sm text-gray-500 dark:text-gray-400">Eingegangen:</span>
                    <span class="ml-2 text-gray-900 dark:text-white">
                      {{ formatDate(selectedFinding.response_received_at) }}
                    </span>
                  </div>
                </div>
                <div v-if="selectedFinding.response_received" class="mt-2">
                  <p class="text-gray-900 dark:text-white whitespace-pre-wrap">
                    {{ selectedFinding.response_received }}
                  </p>
                </div>
              </div>

              <!-- Final Assessment -->
              <div
                v-if="selectedFinding.final_assessment || selectedFinding.corrective_action"
                class="border-t border-gray-200 dark:border-gray-700 pt-4"
              >
                <div v-if="selectedFinding.final_assessment" class="mb-4">
                  <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Abschließende Bewertung
                  </h4>
                  <p class="text-gray-900 dark:text-white whitespace-pre-wrap">
                    {{ selectedFinding.final_assessment }}
                  </p>
                </div>
                <div v-if="selectedFinding.corrective_action">
                  <h4 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Korrekturmaßnahme
                  </h4>
                  <p class="text-gray-900 dark:text-white whitespace-pre-wrap">
                    {{ selectedFinding.corrective_action }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex justify-end gap-3 pt-6 border-t border-gray-200 dark:border-gray-700 mt-6">
              <button
                v-if="selectedFinding.status === 'draft'"
                class="btn-secondary"
                @click="openEditModal(selectedFinding); showDetailModal = false"
              >
                Bearbeiten
              </button>
              <button
                v-if="selectedFinding.status === 'draft'"
                class="btn-primary"
                @click="handleConfirm(selectedFinding)"
              >
                Bestätigen
              </button>
              <button
                v-if="selectedFinding.status === 'confirmed' || selectedFinding.status === 'disputed'"
                class="btn-primary"
                @click="handleResolve(selectedFinding)"
              >
                Als behoben markieren
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
