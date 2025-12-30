<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ChecklistForm from './ChecklistForm.vue'
import {
  listCaseChecklists,
  listTemplates,
  addChecklistToCase,
  getChecklist,
  deleteChecklist,
  type ChecklistSummary,
  type ChecklistTemplate,
  type ChecklistInstance,
} from '@/api/checklists'

const props = defineProps<{
  caseId: string
}>()

// State
const checklists = ref<ChecklistSummary[]>([])
const templates = ref<ChecklistTemplate[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

// Modal State
const showAddModal = ref(false)
const selectedTemplateId = ref<string>('')
const addingChecklist = ref(false)

// Active Checklist
const activeChecklist = ref<ChecklistInstance | null>(null)
const loadingChecklist = ref(false)

// Status labels
const statusLabels: Record<string, string> = {
  not_started: 'Nicht begonnen',
  in_progress: 'In Bearbeitung',
  completed: 'Abgeschlossen',
}

const statusColors: Record<string, string> = {
  not_started: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
  in_progress: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
}

const typeLabels: Record<string, string> = {
  main: 'Hauptcheckliste',
  procurement: 'Vergabeprüfung',
  subsidy: 'Beihilfeprüfung',
  eligibility: 'Förderfähigkeit',
  custom: 'Benutzerdefiniert',
}

// Methods
async function loadChecklists() {
  loading.value = true
  error.value = null

  try {
    checklists.value = await listCaseChecklists(props.caseId)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Fehler beim Laden'
    console.error('Error loading checklists:', err)
  } finally {
    loading.value = false
  }
}

async function loadTemplates() {
  try {
    const result = await listTemplates({ status: 'published' })
    templates.value = result.items
  } catch (err) {
    console.error('Error loading templates:', err)
  }
}

async function handleAddChecklist() {
  if (!selectedTemplateId.value) return

  addingChecklist.value = true
  error.value = null

  try {
    await addChecklistToCase(props.caseId, selectedTemplateId.value)
    showAddModal.value = false
    selectedTemplateId.value = ''
    await loadChecklists()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Fehler beim Hinzufügen'
    console.error('Error adding checklist:', err)
  } finally {
    addingChecklist.value = false
  }
}

async function openChecklist(checklistId: string) {
  loadingChecklist.value = true
  error.value = null

  try {
    activeChecklist.value = await getChecklist(props.caseId, checklistId)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Fehler beim Laden'
    console.error('Error loading checklist:', err)
  } finally {
    loadingChecklist.value = false
  }
}

function closeChecklist() {
  activeChecklist.value = null
  loadChecklists()
}

async function handleDelete(checklistId: string) {
  if (!confirm('Möchten Sie diese Checkliste wirklich löschen?')) return

  try {
    await deleteChecklist(props.caseId, checklistId)
    await loadChecklists()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Fehler beim Löschen'
    console.error('Error deleting checklist:', err)
  }
}

function handleChecklistUpdated(updated: ChecklistInstance) {
  activeChecklist.value = updated
  loadChecklists()
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
  loadChecklists()
  loadTemplates()
})
</script>

<template>
  <div class="h-full">
    <!-- Active Checklist View -->
    <div v-if="activeChecklist" class="h-full flex flex-col">
      <div class="flex items-center gap-4 p-4 border-b border-gray-200 dark:border-gray-700">
        <button
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
          @click="closeChecklist"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <span class="text-gray-500 dark:text-gray-400">Zurück zur Übersicht</span>
      </div>
      <div class="flex-1 overflow-hidden">
        <ChecklistForm
          :checklist="activeChecklist"
          :case-id="caseId"
          @updated="handleChecklistUpdated"
          @close="closeChecklist"
        />
      </div>
    </div>

    <!-- Checklist List View -->
    <div v-else class="p-6 space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          Checklisten
        </h3>
        <button class="btn-primary" @click="showAddModal = true; loadTemplates()">
          <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Checkliste hinzufügen
        </button>
      </div>

      <!-- Error -->
      <div v-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p class="text-red-700 dark:text-red-300">{{ error }}</p>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-12">
        <svg class="animate-spin h-8 w-8 text-accent-600" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>

      <!-- Checklist List -->
      <div v-else-if="checklists.length > 0" class="space-y-4">
        <div
          v-for="checklist in checklists"
          :key="checklist.id"
          class="card p-4 hover:shadow-md transition-shadow cursor-pointer"
          @click="openChecklist(checklist.id)"
        >
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-3">
                <h4 class="font-medium text-gray-900 dark:text-white">
                  {{ checklist.template_name || typeLabels[checklist.checklist_type] || checklist.checklist_type }}
                </h4>
                <span :class="['px-2 py-0.5 text-xs font-medium rounded-full', statusColors[checklist.status]]">
                  {{ statusLabels[checklist.status] }}
                </span>
              </div>
              <div class="flex items-center gap-4 mt-2 text-sm text-gray-500 dark:text-gray-400">
                <span>{{ checklist.answered_questions }} / {{ checklist.total_questions }} Fragen</span>
                <span>Erstellt: {{ formatDate(checklist.created_at) }}</span>
              </div>
            </div>

            <!-- Progress -->
            <div class="flex items-center gap-4">
              <div class="w-32">
                <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-accent-500 transition-all"
                    :style="{ width: `${checklist.progress}%` }"
                  />
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400 mt-1 text-right">
                  {{ checklist.progress }}%
                </div>
              </div>

              <!-- Actions -->
              <div class="flex items-center gap-2" @click.stop>
                <button
                  class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
                  title="Öffnen"
                  @click="openChecklist(checklist.id)"
                >
                  <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </button>
                <button
                  v-if="checklist.status !== 'completed'"
                  class="p-2 text-red-400 hover:text-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
                  title="Löschen"
                  @click="handleDelete(checklist.id)"
                >
                  <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="card p-12 text-center">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
        <h3 class="mt-4 text-lg font-medium text-gray-900 dark:text-white">Keine Checklisten</h3>
        <p class="mt-2 text-gray-500 dark:text-gray-400">
          Fügen Sie eine Checkliste hinzu, um mit der Prüfung zu beginnen.
        </p>
        <button class="btn-primary mt-4" @click="showAddModal = true; loadTemplates()">
          Checkliste hinzufügen
        </button>
      </div>
    </div>

    <!-- Add Checklist Modal -->
    <Teleport to="body">
      <div v-if="showAddModal" class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex min-h-screen items-center justify-center p-4">
          <div class="fixed inset-0 bg-black/50" @click="showAddModal = false" />

          <div class="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-lg w-full p-6">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Checkliste hinzufügen
            </h2>

            <div class="space-y-4">
              <div>
                <label class="label">Vorlage auswählen</label>
                <select v-model="selectedTemplateId" class="input">
                  <option value="">Bitte wählen...</option>
                  <option
                    v-for="template in templates"
                    :key="template.id"
                    :value="template.id"
                  >
                    {{ template.name }} ({{ typeLabels[template.checklist_type] || template.checklist_type }})
                  </option>
                </select>
              </div>

              <div v-if="templates.length === 0" class="text-sm text-gray-500 dark:text-gray-400">
                Keine Vorlagen verfügbar. Bitte erstellen Sie zuerst Checklisten-Vorlagen.
              </div>
            </div>

            <div class="flex justify-end gap-3 mt-6">
              <button
                type="button"
                class="btn-secondary"
                @click="showAddModal = false"
              >
                Abbrechen
              </button>
              <button
                type="button"
                class="btn-primary"
                :disabled="!selectedTemplateId || addingChecklist"
                @click="handleAddChecklist"
              >
                <svg v-if="addingChecklist" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Hinzufügen
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
