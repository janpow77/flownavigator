<script setup lang="ts">
import { ref, computed } from 'vue'
import { useModuleConverterStore } from '@/stores/moduleConverter'

const store = useModuleConverterStore()

const selectedTemplate = computed(() => store.wizardState.selectedTemplate)
const selectedLLMConfig = computed(() => store.wizardState.selectedLLMConfig)
const selectedGitHubIntegration = computed(() => store.wizardState.selectedGitHubIntegration)
const sourceContent = computed({
  get: () => store.wizardState.sourceContent,
  set: (value: string) => store.setSourceContent(value),
})

const isValidContent = computed(() => sourceContent.value.trim().length > 10)

function handleBack() {
  store.previousStep()
}

function handleNext() {
  if (store.canStartConversion) {
    store.nextStep()
  }
}

function formatFileSize(content: string): string {
  const bytes = new Blob([content]).size
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function getLineCount(content: string): number {
  return content.split('\n').length
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h2 class="text-lg font-medium text-gray-900 dark:text-white">
        Prüfen & Validieren
      </h2>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Überprüfen Sie Ihre Eingaben und geben Sie den Quellinhalt ein
      </p>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- Template -->
      <div class="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
        <div class="flex items-center gap-2 mb-2">
          <svg class="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Template</span>
        </div>
        <p class="text-sm font-medium text-gray-900 dark:text-white">
          {{ selectedTemplate?.name }}
        </p>
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {{ selectedTemplate?.source_format }} → {{ selectedTemplate?.target_format }}
        </p>
      </div>

      <!-- LLM Config -->
      <div class="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
        <div class="flex items-center gap-2 mb-2">
          <svg class="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">LLM</span>
        </div>
        <p class="text-sm font-medium text-gray-900 dark:text-white">
          {{ selectedLLMConfig?.name }}
        </p>
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {{ selectedLLMConfig?.provider }} / {{ selectedLLMConfig?.model }}
        </p>
      </div>

      <!-- GitHub -->
      <div class="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
        <div class="flex items-center gap-2 mb-2">
          <svg class="w-4 h-4 text-gray-500" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
          </svg>
          <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">GitHub</span>
        </div>
        <p class="text-sm font-medium text-gray-900 dark:text-white">
          {{ selectedGitHubIntegration?.name || 'Nicht konfiguriert' }}
        </p>
        <p v-if="selectedGitHubIntegration" class="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {{ selectedGitHubIntegration.repository_owner }}/{{ selectedGitHubIntegration.repository_name }}
        </p>
        <p v-else class="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Manueller Download
        </p>
      </div>
    </div>

    <!-- Source Content Input -->
    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Quellinhalt
        </label>
        <div v-if="sourceContent" class="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
          <span>{{ getLineCount(sourceContent) }} Zeilen</span>
          <span>{{ formatFileSize(sourceContent) }}</span>
        </div>
      </div>

      <div class="relative">
        <textarea
          v-model="sourceContent"
          rows="15"
          :class="[
            'w-full px-4 py-3 font-mono text-sm border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-accent-500 focus:border-transparent resize-none',
            isValidContent
              ? 'border-gray-300 dark:border-gray-600'
              : sourceContent.length > 0
                ? 'border-red-300 dark:border-red-600'
                : 'border-gray-300 dark:border-gray-600'
          ]"
          :placeholder="`Fügen Sie hier Ihren ${selectedTemplate?.source_format || 'Quell'}-Inhalt ein...`"
        />

        <!-- Validation Message -->
        <div
          v-if="sourceContent.length > 0 && !isValidContent"
          class="mt-2 text-sm text-red-600 dark:text-red-400"
        >
          Der Inhalt muss mindestens 10 Zeichen lang sein.
        </div>
      </div>

      <!-- File Upload Option -->
      <div class="flex items-center gap-4 pt-2">
        <label class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-accent-600 dark:hover:text-accent-400 cursor-pointer transition-colors">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <span>Datei hochladen</span>
          <input
            type="file"
            accept=".txt,.json,.xml,.yaml,.yml,.md"
            class="hidden"
            @change="(e: Event) => {
              const file = (e.target as HTMLInputElement).files?.[0]
              if (file) {
                const reader = new FileReader()
                reader.onload = () => {
                  sourceContent = reader.result as string
                }
                reader.readAsText(file)
              }
            }"
          />
        </label>

        <button
          v-if="sourceContent"
          class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 transition-colors"
          @click="sourceContent = ''"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          <span>Löschen</span>
        </button>
      </div>
    </div>

    <!-- Validation Summary -->
    <div
      v-if="isValidContent"
      class="flex items-start gap-3 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg"
    >
      <svg class="w-5 h-5 text-green-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <div class="text-sm text-green-700 dark:text-green-300">
        <p class="font-medium">Bereit zur Konvertierung</p>
        <p class="mt-1">
          Alle erforderlichen Daten sind vorhanden. Klicken Sie auf "Weiter", um die Konvertierung zu starten.
        </p>
      </div>
    </div>

    <!-- Navigation -->
    <div class="flex justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
      <button
        class="px-6 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
        @click="handleBack"
      >
        Zurück
      </button>
      <button
        :disabled="!store.canStartConversion"
        :class="[
          'px-6 py-2 rounded-lg text-sm font-medium transition-colors',
          store.canStartConversion
            ? 'bg-accent-600 text-white hover:bg-accent-700'
            : 'bg-gray-100 text-gray-400 dark:bg-gray-700 dark:text-gray-500 cursor-not-allowed'
        ]"
        @click="handleNext"
      >
        Weiter zur Ausführung
      </button>
    </div>
  </div>
</template>
