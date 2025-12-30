<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  listDocuments,
  uploadDocument,
  deleteDocument,
  downloadDocument,
  updateDocument,
  formatFileSize,
  CATEGORY_LABELS,
  STATUS_LABELS,
  STATUS_COLORS,
  type BoxDocument,
  type DocumentCategory,
  type DocumentStatus,
} from '@/api/documentBox'

const props = defineProps<{
  caseId: string
}>()

// State
const documents = ref<BoxDocument[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const uploading = ref(false)
const uploadProgress = ref(0)

// Filters
const categoryFilter = ref<DocumentCategory | ''>('')
const statusFilter = ref<DocumentStatus | ''>('')

// Modal State
const showUploadModal = ref(false)
const selectedCategory = ref<DocumentCategory>('sonstige')
const selectedFile = ref<File | null>(null)
const dragOver = ref(false)

// Detail Modal
const showDetailModal = ref(false)
const selectedDocument = ref<BoxDocument | null>(null)

// Computed
const filteredDocuments = computed(() => {
  return documents.value.filter(doc => {
    if (categoryFilter.value && doc.category !== categoryFilter.value) return false
    if (statusFilter.value && doc.manual_status !== statusFilter.value) return false
    return true
  })
})

const categories: DocumentCategory[] = ['belege', 'bescheide', 'korrespondenz', 'vertraege', 'nachweise', 'sonstige']
const statuses: DocumentStatus[] = ['pending', 'verified', 'rejected', 'unclear']

// Methods
async function loadDocuments() {
  loading.value = true
  error.value = null

  try {
    const response = await listDocuments(props.caseId, { page_size: 100 })
    documents.value = response.items
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Fehler beim Laden'
    console.error('Error loading documents:', err)
  } finally {
    loading.value = false
  }
}

function handleDragOver(e: DragEvent) {
  e.preventDefault()
  dragOver.value = true
}

function handleDragLeave() {
  dragOver.value = false
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  dragOver.value = false

  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    selectedFile.value = files[0]
    showUploadModal.value = true
  }
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    selectedFile.value = input.files[0]
  }
}

async function handleUpload() {
  if (!selectedFile.value) return

  uploading.value = true
  uploadProgress.value = 0
  error.value = null

  try {
    await uploadDocument(props.caseId, selectedFile.value, selectedCategory.value)
    showUploadModal.value = false
    selectedFile.value = null
    selectedCategory.value = 'sonstige'
    await loadDocuments()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Upload fehlgeschlagen'
    console.error('Error uploading document:', err)
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

async function handleDownload(doc: BoxDocument) {
  try {
    const blob = await downloadDocument(props.caseId, doc.id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = doc.file_name
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  } catch (err) {
    console.error('Error downloading document:', err)
    error.value = 'Download fehlgeschlagen'
  }
}

async function handleDelete(doc: BoxDocument) {
  if (!confirm(`Dokument "${doc.file_name}" wirklich l\u00f6schen?`)) return

  try {
    await deleteDocument(props.caseId, doc.id)
    await loadDocuments()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'L\u00f6schen fehlgeschlagen'
    console.error('Error deleting document:', err)
  }
}

async function handleVerify(doc: BoxDocument, status: DocumentStatus) {
  try {
    await updateDocument(props.caseId, doc.id, { manual_status: status })
    await loadDocuments()
    if (selectedDocument.value?.id === doc.id) {
      selectedDocument.value = { ...doc, manual_status: status }
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Aktualisierung fehlgeschlagen'
    console.error('Error updating document:', err)
  }
}

function openDetail(doc: BoxDocument) {
  selectedDocument.value = doc
  showDetailModal.value = true
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getFileTypeIcon(mimeType: string): string {
  if (mimeType.startsWith('image/')) return 'M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z'
  if (mimeType === 'application/pdf') return 'M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z'
  return 'M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13'
}

// Lifecycle
onMounted(() => {
  loadDocuments()
})
</script>

<template>
  <div
    class="h-full flex flex-col"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
    @drop="handleDrop"
  >
    <!-- Header -->
    <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
        Dokumente
        <span v-if="documents.length > 0" class="text-sm font-normal text-gray-500">
          ({{ documents.length }})
        </span>
      </h3>
      <button class="btn-primary" @click="showUploadModal = true">
        <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
        Hochladen
      </button>
    </div>

    <!-- Filters -->
    <div class="flex gap-4 p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
      <div>
        <select v-model="categoryFilter" class="input text-sm py-1.5">
          <option value="">Alle Kategorien</option>
          <option v-for="cat in categories" :key="cat" :value="cat">
            {{ CATEGORY_LABELS[cat] }}
          </option>
        </select>
      </div>
      <div>
        <select v-model="statusFilter" class="input text-sm py-1.5">
          <option value="">Alle Status</option>
          <option v-for="status in statuses" :key="status" :value="status">
            {{ STATUS_LABELS[status] }}
          </option>
        </select>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mx-4 mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
      <p class="text-sm text-red-700 dark:text-red-300">{{ error }}</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <svg class="animate-spin h-8 w-8 text-accent-600" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <!-- Document Grid -->
    <div v-else-if="filteredDocuments.length > 0" class="flex-1 overflow-y-auto p-4">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="doc in filteredDocuments"
          :key="doc.id"
          class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow cursor-pointer"
          @click="openDetail(doc)"
        >
          <!-- Icon and Name -->
          <div class="flex items-start gap-3">
            <div class="flex-shrink-0 w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" :d="getFileTypeIcon(doc.mime_type)" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-medium text-gray-900 dark:text-white truncate">
                {{ doc.file_name }}
              </h4>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                {{ formatFileSize(doc.file_size) }}
              </p>
            </div>
          </div>

          <!-- Meta -->
          <div class="mt-3 flex items-center gap-2 flex-wrap">
            <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
              {{ CATEGORY_LABELS[doc.category] }}
            </span>
            <span
              v-if="doc.manual_status"
              :class="['px-2 py-0.5 text-xs font-medium rounded-full', STATUS_COLORS[doc.manual_status]]"
            >
              {{ STATUS_LABELS[doc.manual_status] }}
            </span>
          </div>

          <!-- Date -->
          <p class="mt-2 text-xs text-gray-400 dark:text-gray-500">
            {{ formatDate(doc.uploaded_at) }}
          </p>

          <!-- Actions -->
          <div class="mt-3 flex gap-2" @click.stop>
            <button
              class="p-1.5 text-gray-400 hover:text-accent-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Herunterladen"
              @click="handleDownload(doc)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </button>
            <button
              class="p-1.5 text-gray-400 hover:text-green-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Verifizieren"
              @click="handleVerify(doc, 'verified')"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </button>
            <button
              class="p-1.5 text-gray-400 hover:text-red-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="L\u00f6schen"
              @click="handleDelete(doc)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else
      :class="[
        'flex-1 flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-lg m-4 transition-colors',
        dragOver ? 'border-accent-500 bg-accent-50 dark:bg-accent-900/20' : 'border-gray-300 dark:border-gray-700'
      ]"
    >
      <svg class="w-12 h-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 class="text-lg font-medium text-gray-900 dark:text-white">Keine Dokumente</h3>
      <p class="mt-1 text-gray-500 dark:text-gray-400">
        Dateien hierher ziehen oder Hochladen klicken
      </p>
      <button class="btn-primary mt-4" @click="showUploadModal = true">
        Dokument hochladen
      </button>
    </div>

    <!-- Upload Modal -->
    <Teleport to="body">
      <div v-if="showUploadModal" class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex min-h-screen items-center justify-center p-4">
          <div class="fixed inset-0 bg-black/50" @click="showUploadModal = false" />

          <div class="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-lg w-full p-6">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Dokument hochladen
            </h2>

            <div class="space-y-4">
              <!-- File Selection -->
              <div
                :class="[
                  'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
                  selectedFile ? 'border-accent-500 bg-accent-50 dark:bg-accent-900/20' : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
                ]"
                @click="($refs.fileInput as HTMLInputElement)?.click()"
              >
                <input
                  ref="fileInput"
                  type="file"
                  class="hidden"
                  @change="handleFileSelect"
                />
                <div v-if="selectedFile">
                  <svg class="mx-auto h-8 w-8 text-accent-500 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <p class="text-sm font-medium text-gray-900 dark:text-white">{{ selectedFile.name }}</p>
                  <p class="text-xs text-gray-500">{{ formatFileSize(selectedFile.size) }}</p>
                </div>
                <div v-else>
                  <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
                    Klicken oder Datei hierher ziehen
                  </p>
                </div>
              </div>

              <!-- Category Selection -->
              <div>
                <label class="label">Kategorie</label>
                <select v-model="selectedCategory" class="input">
                  <option v-for="cat in categories" :key="cat" :value="cat">
                    {{ CATEGORY_LABELS[cat] }}
                  </option>
                </select>
              </div>
            </div>

            <!-- Progress -->
            <div v-if="uploading" class="mt-4">
              <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  class="h-full bg-accent-500 transition-all"
                  :style="{ width: `${uploadProgress}%` }"
                />
              </div>
            </div>

            <div class="flex justify-end gap-3 mt-6">
              <button
                type="button"
                class="btn-secondary"
                :disabled="uploading"
                @click="showUploadModal = false; selectedFile = null"
              >
                Abbrechen
              </button>
              <button
                type="button"
                class="btn-primary"
                :disabled="!selectedFile || uploading"
                @click="handleUpload"
              >
                <svg v-if="uploading" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Hochladen
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Detail Modal -->
    <Teleport to="body">
      <div v-if="showDetailModal && selectedDocument" class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex min-h-screen items-center justify-center p-4">
          <div class="fixed inset-0 bg-black/50" @click="showDetailModal = false" />

          <div class="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-2xl w-full p-6">
            <div class="flex items-start justify-between mb-4">
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
                {{ selectedDocument.file_name }}
              </h2>
              <button
                class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                @click="showDetailModal = false"
              >
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400">Gr\u00f6\u00dfe</p>
                <p class="font-medium text-gray-900 dark:text-white">{{ formatFileSize(selectedDocument.file_size) }}</p>
              </div>
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400">Typ</p>
                <p class="font-medium text-gray-900 dark:text-white">{{ selectedDocument.mime_type }}</p>
              </div>
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400">Kategorie</p>
                <p class="font-medium text-gray-900 dark:text-white">{{ CATEGORY_LABELS[selectedDocument.category] }}</p>
              </div>
              <div>
                <p class="text-sm text-gray-500 dark:text-gray-400">Hochgeladen am</p>
                <p class="font-medium text-gray-900 dark:text-white">{{ formatDate(selectedDocument.uploaded_at) }}</p>
              </div>
              <div class="col-span-2">
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-2">Status</p>
                <div class="flex gap-2">
                  <button
                    v-for="status in statuses"
                    :key="status"
                    :class="[
                      'px-3 py-1.5 text-sm font-medium rounded-lg border-2 transition-colors',
                      selectedDocument.manual_status === status
                        ? STATUS_COLORS[status] + ' border-current'
                        : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    ]"
                    @click="handleVerify(selectedDocument!, status)"
                  >
                    {{ STATUS_LABELS[status] }}
                  </button>
                </div>
              </div>
            </div>

            <div class="flex justify-end gap-3 mt-6">
              <button class="btn-secondary" @click="handleDownload(selectedDocument!)">
                <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Herunterladen
              </button>
              <button class="btn-primary" @click="showDetailModal = false">
                Schlie\u00dfen
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
