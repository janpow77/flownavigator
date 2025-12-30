<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import ChecklistQuestion from './ChecklistQuestion.vue'
import type { ChecklistInstance, ChecklistStructure } from '@/api/checklists'
import { updateChecklist } from '@/api/checklists'

const props = defineProps<{
  checklist: ChecklistInstance
  caseId: string
}>()

const emit = defineEmits<{
  'updated': [checklist: ChecklistInstance]
  'close': []
}>()

// Local state
const responses = ref<Record<string, unknown>>({})
const notes = ref<Record<string, string>>({})
const saving = ref(false)
const error = ref<string | null>(null)
const activeSection = ref<string>('')

// Computed
const structure = computed<ChecklistStructure | null>(() => {
  return props.checklist.structure || null
})

const sections = computed(() => {
  if (!structure.value) return []
  return [...structure.value.sections].sort((a, b) => a.order - b.order)
})

const progress = computed(() => {
  if (!structure.value) return 0
  let answered = 0
  let total = 0

  for (const section of structure.value.sections) {
    for (const question of section.questions) {
      if (question.type !== 'section') {
        total++
        const response = responses.value[question.id]
        if (response !== undefined && response !== null && response !== '') {
          answered++
        }
      }
    }
  }

  return total > 0 ? Math.round((answered / total) * 100) : 0
})

const canComplete = computed(() => {
  if (!structure.value) return false

  // Check if all required questions are answered
  for (const section of structure.value.sections) {
    for (const question of section.questions) {
      if (question.required) {
        const response = responses.value[question.id]
        if (response === undefined || response === null || response === '') {
          return false
        }
      }
    }
  }

  return true
})

// Methods
function initializeResponses() {
  // Load existing responses
  if (props.checklist.responses) {
    for (const [questionId, responseData] of Object.entries(props.checklist.responses)) {
      if (typeof responseData === 'object' && responseData !== null && 'value' in responseData) {
        responses.value[questionId] = (responseData as { value: unknown }).value
        if ('note' in responseData && (responseData as { note?: string }).note) {
          notes.value[questionId] = (responseData as { note: string }).note
        }
      }
    }
  }

  // Set active section
  if (sections.value.length > 0) {
    activeSection.value = sections.value[0].id
  }
}

async function saveResponses(complete = false) {
  saving.value = true
  error.value = null

  try {
    const data: {
      responses: Record<string, unknown>
      notes: Record<string, string>
      status?: string
    } = {
      responses: responses.value,
      notes: notes.value,
    }

    if (complete) {
      data.status = 'completed'
    }

    const updated = await updateChecklist(props.caseId, props.checklist.id, data)
    emit('updated', updated)

    if (complete) {
      emit('close')
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Fehler beim Speichern'
    console.error('Error saving checklist:', err)
  } finally {
    saving.value = false
  }
}

function getSectionProgress(sectionId: string): { answered: number; total: number } {
  const section = sections.value.find(s => s.id === sectionId)
  if (!section) return { answered: 0, total: 0 }

  let answered = 0
  let total = 0

  for (const question of section.questions) {
    if (question.type !== 'section') {
      total++
      const response = responses.value[question.id]
      if (response !== undefined && response !== null && response !== '') {
        answered++
      }
    }
  }

  return { answered, total }
}

// Lifecycle
onMounted(() => {
  initializeResponses()
})

watch(() => props.checklist, () => {
  initializeResponses()
})
</script>

<template>
  <div class="flex h-full">
    <!-- Sidebar: Sections Navigation -->
    <div class="w-64 border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 p-4 overflow-y-auto">
      <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
        Abschnitte
      </h3>
      <nav class="space-y-1">
        <button
          v-for="section in sections"
          :key="section.id"
          :class="[
            'w-full text-left px-3 py-2 rounded-lg transition-colors',
            activeSection === section.id
              ? 'bg-accent-100 dark:bg-accent-900/30 text-accent-700 dark:text-accent-300'
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
          ]"
          @click="activeSection = section.id"
        >
          <div class="font-medium text-sm">{{ section.title }}</div>
          <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {{ getSectionProgress(section.id).answered }} / {{ getSectionProgress(section.id).total }} beantwortet
          </div>
        </button>
      </nav>

      <!-- Overall Progress -->
      <div class="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
        <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Gesamtfortschritt
        </div>
        <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            class="h-full bg-accent-500 transition-all duration-300"
            :style="{ width: `${progress}%` }"
          />
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {{ progress }}% abgeschlossen
        </div>
      </div>
    </div>

    <!-- Main Content: Questions -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ checklist.template_name || 'Checkliste' }}
          </h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            {{ sections.find(s => s.id === activeSection)?.title }}
          </p>
        </div>
        <div class="flex items-center gap-3">
          <button
            class="btn-secondary"
            :disabled="saving"
            @click="saveResponses(false)"
          >
            <svg v-if="saving" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Zwischenspeichern
          </button>
          <button
            class="btn-primary"
            :disabled="saving || !canComplete"
            @click="saveResponses(true)"
          >
            Abschließen
          </button>
        </div>
      </div>

      <!-- Error -->
      <div v-if="error" class="mx-6 mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
        <p class="text-sm text-red-700 dark:text-red-300">{{ error }}</p>
      </div>

      <!-- Questions -->
      <div class="flex-1 overflow-y-auto p-6">
        <div
          v-for="section in sections"
          v-show="activeSection === section.id"
          :key="section.id"
          class="space-y-6"
        >
          <p v-if="section.description" class="text-gray-600 dark:text-gray-400 mb-6">
            {{ section.description }}
          </p>

          <div
            v-for="question in section.questions.sort((a, b) => a.order - b.order)"
            :key="question.id"
            class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4"
          >
            <ChecklistQuestion
              v-model="responses[question.id]"
              :question="question"
              :note="notes[question.id]"
              :disabled="checklist.status === 'completed'"
              @update:note="notes[question.id] = $event"
            />
          </div>
        </div>
      </div>

      <!-- Footer Navigation -->
      <div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-between">
        <button
          class="btn-secondary"
          :disabled="sections.findIndex(s => s.id === activeSection) === 0"
          @click="activeSection = sections[sections.findIndex(s => s.id === activeSection) - 1]?.id || activeSection"
        >
          ← Vorheriger Abschnitt
        </button>
        <button
          class="btn-secondary"
          :disabled="sections.findIndex(s => s.id === activeSection) === sections.length - 1"
          @click="activeSection = sections[sections.findIndex(s => s.id === activeSection) + 1]?.id || activeSection"
        >
          Nächster Abschnitt →
        </button>
      </div>
    </div>
  </div>
</template>
