<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  listAuditLogs,
  addComment,
  type AuditLogEntry,
  type AuditAction,
  ACTION_LABELS,
  ACTION_COLORS,
  formatDateTime,
  formatRelativeTime,
  getLogDescription,
} from '@/api/auditLogs'

const props = defineProps<{
  caseId: string
}>()

// State
const logs = ref<AuditLogEntry[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const page = ref(1)
const pageSize = ref(50)
const totalPages = ref(0)
const total = ref(0)

// Filter
const filterAction = ref<AuditAction | ''>('')

// Comment
const showCommentForm = ref(false)
const newComment = ref('')
const savingComment = ref(false)

// Computed
const actionOptions = computed(() => {
  return Object.entries(ACTION_LABELS).map(([key, label]) => ({
    value: key as AuditAction,
    label,
  }))
})

// Methods
async function loadLogs() {
  loading.value = true
  error.value = null

  try {
    const response = await listAuditLogs(props.caseId, {
      action: filterAction.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    logs.value = response.items
    total.value = response.total
    totalPages.value = response.pages
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Fehler beim Laden'
    console.error('Error loading audit logs:', err)
  } finally {
    loading.value = false
  }
}

async function handleAddComment() {
  if (!newComment.value.trim()) return

  savingComment.value = true
  error.value = null

  try {
    await addComment(props.caseId, newComment.value.trim())
    newComment.value = ''
    showCommentForm.value = false
    await loadLogs()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Fehler beim Speichern'
    console.error('Error adding comment:', err)
  } finally {
    savingComment.value = false
  }
}

function handleFilterChange() {
  page.value = 1
  loadLogs()
}

function handlePageChange(newPage: number) {
  page.value = newPage
  loadLogs()
}

function getActionIcon(action: AuditAction): string {
  const icons: Record<AuditAction, string> = {
    create: 'M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z',
    update: 'M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125',
    delete: 'M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0',
    status_change: 'M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99',
    assign: 'M18 7.5v3m0 0v3m0-3h3m-3 0h-3m-2.25-4.125a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zM3 19.235v-.11a6.375 6.375 0 0112.75 0v.109A12.318 12.318 0 019.374 21c-2.331 0-4.512-.645-6.374-1.766z',
    unassign: 'M22 10.5h-6m-2.25-4.125a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zM4 19.235v-.11a6.375 6.375 0 0112.75 0v.109A12.318 12.318 0 0110.374 21c-2.331 0-4.512-.645-6.374-1.766z',
    upload: 'M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5',
    download: 'M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3',
    verify: 'M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z',
    confirm: 'M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    resolve: 'M4.5 12.75l6 6 9-13.5',
    comment: 'M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z',
  }
  return icons[action] || icons.update
}

// Lifecycle
onMounted(() => {
  loadLogs()
})
</script>

<template>
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Verlauf</h3>
      <button class="btn-primary" @click="showCommentForm = true">
        <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"
          />
        </svg>
        Kommentar hinzufügen
      </button>
    </div>

    <!-- Comment Form -->
    <div
      v-if="showCommentForm"
      class="card p-4 border-2 border-accent-500 dark:border-accent-400"
    >
      <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Neuer Kommentar
      </h4>
      <textarea
        v-model="newComment"
        class="input"
        rows="3"
        placeholder="Kommentar eingeben..."
        :disabled="savingComment"
      />
      <div class="flex justify-end gap-2 mt-3">
        <button
          type="button"
          class="btn-secondary"
          :disabled="savingComment"
          @click="showCommentForm = false; newComment = ''"
        >
          Abbrechen
        </button>
        <button
          type="button"
          class="btn-primary"
          :disabled="!newComment.trim() || savingComment"
          @click="handleAddComment"
        >
          <svg
            v-if="savingComment"
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
          Speichern
        </button>
      </div>
    </div>

    <!-- Filter -->
    <div class="flex items-center gap-4">
      <select v-model="filterAction" class="input w-auto" @change="handleFilterChange">
        <option value="">Alle Aktionen</option>
        <option v-for="option in actionOptions" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </select>
      <span v-if="total > 0" class="text-sm text-gray-500 dark:text-gray-400">
        {{ total }} Einträge
      </span>
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

    <!-- Timeline -->
    <div v-else-if="logs.length > 0" class="relative">
      <!-- Timeline line -->
      <div
        class="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700"
      />

      <!-- Log entries -->
      <div class="space-y-4">
        <div
          v-for="log in logs"
          :key="log.id"
          class="relative flex items-start gap-4 pl-10"
        >
          <!-- Icon -->
          <div
            :class="[
              'absolute left-0 w-8 h-8 rounded-full flex items-center justify-center',
              ACTION_COLORS[log.action],
            ]"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                :d="getActionIcon(log.action)"
              />
            </svg>
          </div>

          <!-- Content -->
          <div class="flex-1 card p-4">
            <div class="flex items-start justify-between">
              <div>
                <span
                  :class="[
                    'inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full mr-2',
                    ACTION_COLORS[log.action],
                  ]"
                >
                  {{ ACTION_LABELS[log.action] }}
                </span>
                <span class="text-sm text-gray-500 dark:text-gray-400">
                  {{ formatRelativeTime(log.created_at) }}
                </span>
              </div>
              <span
                class="text-xs text-gray-400 dark:text-gray-500"
                :title="formatDateTime(log.created_at)"
              >
                {{ formatDateTime(log.created_at) }}
              </span>
            </div>

            <p class="mt-2 text-gray-900 dark:text-white">
              {{ getLogDescription(log) }}
            </p>

            <!-- Field change details -->
            <div
              v-if="log.field_name && log.old_value && log.new_value"
              class="mt-2 text-sm"
            >
              <div class="flex items-center gap-2">
                <span class="text-gray-500 dark:text-gray-400">{{ log.field_name }}:</span>
                <span
                  class="px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded line-through"
                >
                  {{ log.old_value }}
                </span>
                <svg class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
                <span
                  class="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded"
                >
                  {{ log.new_value }}
                </span>
              </div>
            </div>

            <!-- User info -->
            <div
              v-if="log.user_name || log.user_email"
              class="mt-2 flex items-center text-sm text-gray-500 dark:text-gray-400"
            >
              <svg class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
              {{ log.user_name || log.user_email }}
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex justify-center gap-2 mt-6">
        <button
          class="btn-secondary px-3 py-1 text-sm"
          :disabled="page <= 1"
          @click="handlePageChange(page - 1)"
        >
          Zurück
        </button>
        <span class="px-3 py-1 text-sm text-gray-500 dark:text-gray-400">
          Seite {{ page }} von {{ totalPages }}
        </span>
        <button
          class="btn-secondary px-3 py-1 text-sm"
          :disabled="page >= totalPages"
          @click="handlePageChange(page + 1)"
        >
          Weiter
        </button>
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
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <h3 class="mt-4 text-lg font-medium text-gray-900 dark:text-white">Kein Verlauf</h3>
      <p class="mt-2 text-gray-500 dark:text-gray-400">
        Es wurden noch keine Änderungen protokolliert.
      </p>
      <button class="btn-primary mt-4" @click="showCommentForm = true">
        Ersten Kommentar hinzufügen
      </button>
    </div>
  </div>
</template>
