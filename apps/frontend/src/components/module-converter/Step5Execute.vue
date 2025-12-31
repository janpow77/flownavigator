<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useModuleConverterStore } from '@/stores/moduleConverter'

const store = useModuleConverterStore()

const wizardState = computed(() => store.wizardState)
const progress = computed(() => store.conversionProgress)
const conversion = computed(() => wizardState.value.conversion)
const isProcessing = computed(() => wizardState.value.isProcessing)
const error = computed(() => wizardState.value.error)

const showOutput = ref(false)

onMounted(async () => {
  if (!conversion.value) {
    await store.startConversion()
  }
})

function handleBack() {
  if (!isProcessing.value) {
    store.previousStep()
  }
}

async function handleRetry() {
  if (conversion.value) {
    await store.retryConversion(conversion.value.id)
  }
}

async function handleCancel() {
  if (conversion.value) {
    await store.cancelConversion(conversion.value.id)
  }
}

function handleNewConversion() {
  store.resetWizard()
}

function downloadResult() {
  if (conversion.value?.converted_content) {
    const blob = new Blob([conversion.value.converted_content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `converted_${new Date().toISOString().slice(0, 10)}.${store.wizardState.selectedTemplate?.target_format || 'txt'}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
}

function copyToClipboard() {
  if (conversion.value?.converted_content) {
    navigator.clipboard.writeText(conversion.value.converted_content)
  }
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'text-gray-500',
    analyzing: 'text-blue-500',
    converting: 'text-purple-500',
    validating: 'text-orange-500',
    staging: 'text-cyan-500',
    completed: 'text-green-500',
    failed: 'text-red-500',
  }
  return colors[status] || 'text-gray-500'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h2 class="text-lg font-medium text-gray-900 dark:text-white">
        Konvertierung ausführen
      </h2>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
        {{ isProcessing ? 'Die Konvertierung wird ausgeführt...' : 'Status der Konvertierung' }}
      </p>
    </div>

    <!-- Progress Section -->
    <div class="space-y-4">
      <!-- Progress Bar -->
      <div class="relative">
        <div class="overflow-hidden h-3 rounded-full bg-gray-200 dark:bg-gray-700">
          <div
            :class="[
              'h-full rounded-full transition-all duration-500',
              progress.currentStep === 'failed'
                ? 'bg-red-500'
                : progress.currentStep === 'completed'
                  ? 'bg-green-500'
                  : 'bg-accent-600'
            ]"
            :style="{ width: `${progress.progress}%` }"
          />
        </div>
        <div class="flex justify-between mt-1">
          <span class="text-xs text-gray-500 dark:text-gray-400">{{ progress.progress }}%</span>
          <span :class="['text-xs font-medium', getStatusColor(progress.currentStep)]">
            {{ progress.message }}
          </span>
        </div>
      </div>

      <!-- Status Steps -->
      <div class="grid grid-cols-5 gap-2">
        <div
          v-for="step in ['analyzing', 'converting', 'validating', 'staging', 'completed']"
          :key="step"
          :class="[
            'text-center py-2 rounded-lg text-xs font-medium transition-all',
            progress.currentStep === step
              ? 'bg-accent-100 dark:bg-accent-900/30 text-accent-700 dark:text-accent-300 ring-2 ring-accent-500'
              : progress.progress > (['analyzing', 'converting', 'validating', 'staging', 'completed'].indexOf(step) + 1) * 20
                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'
          ]"
        >
          {{ step === 'analyzing' ? 'Analyse' : step === 'converting' ? 'KI' : step === 'validating' ? 'Validierung' : step === 'staging' ? 'Staging' : 'Fertig' }}
        </div>
      </div>
    </div>

    <!-- Processing Indicator -->
    <div v-if="isProcessing" class="flex items-center justify-center py-8">
      <div class="flex flex-col items-center gap-4">
        <div class="relative">
          <div class="w-16 h-16 border-4 border-accent-200 dark:border-accent-800 rounded-full" />
          <div class="absolute top-0 left-0 w-16 h-16 border-4 border-accent-600 rounded-full animate-spin border-t-transparent" />
        </div>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          {{ progress.message }}
        </p>
        <button
          class="text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
          @click="handleCancel"
        >
          Abbrechen
        </button>
      </div>
    </div>

    <!-- Error State -->
    <div
      v-else-if="error"
      class="p-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
    >
      <div class="flex items-start gap-4">
        <div class="flex-shrink-0">
          <svg class="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div class="flex-1">
          <h3 class="text-sm font-medium text-red-800 dark:text-red-200">
            Konvertierung fehlgeschlagen
          </h3>
          <p class="mt-1 text-sm text-red-700 dark:text-red-300">
            {{ error }}
          </p>
          <div class="mt-4 flex gap-3">
            <button
              class="px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 bg-red-100 dark:bg-red-900/30 hover:bg-red-200 dark:hover:bg-red-900/50 rounded-lg transition-colors"
              @click="handleRetry"
            >
              Erneut versuchen
            </button>
            <button
              class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
              @click="handleBack"
            >
              Zurück
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Success State -->
    <div
      v-else-if="conversion?.status === 'completed'"
      class="space-y-6"
    >
      <!-- Success Message -->
      <div class="p-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
        <div class="flex items-start gap-4">
          <div class="flex-shrink-0">
            <svg class="w-6 h-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="flex-1">
            <h3 class="text-sm font-medium text-green-800 dark:text-green-200">
              Konvertierung erfolgreich
            </h3>
            <p class="mt-1 text-sm text-green-700 dark:text-green-300">
              Das Modul wurde erfolgreich konvertiert.
              <span v-if="conversion.pr_url">
                <a :href="conversion.pr_url" target="_blank" class="underline hover:no-underline">
                  Pull Request anzeigen
                </a>
              </span>
            </p>
          </div>
        </div>
      </div>

      <!-- Result Preview -->
      <div class="space-y-2">
        <div class="flex items-center justify-between">
          <button
            class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300"
            @click="showOutput = !showOutput"
          >
            <svg
              :class="['w-4 h-4 transition-transform', showOutput ? 'rotate-90' : '']"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
            Ergebnis anzeigen
          </button>

          <div class="flex gap-2">
            <button
              class="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-accent-600 dark:hover:text-accent-400 transition-colors"
              @click="copyToClipboard"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Kopieren
            </button>
            <button
              class="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-accent-600 dark:hover:text-accent-400 transition-colors"
              @click="downloadResult"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download
            </button>
          </div>
        </div>

        <div v-if="showOutput" class="relative">
          <pre class="p-4 bg-gray-900 text-gray-100 rounded-lg overflow-x-auto text-sm max-h-96 overflow-y-auto"><code>{{ conversion.converted_content }}</code></pre>
        </div>
      </div>

      <!-- GitHub Info -->
      <div v-if="conversion.pr_url || conversion.branch_name" class="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
        <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-3">
          GitHub Details
        </h4>
        <dl class="grid grid-cols-2 gap-4 text-sm">
          <div v-if="conversion.branch_name">
            <dt class="text-gray-500 dark:text-gray-400">Branch</dt>
            <dd class="font-medium text-gray-900 dark:text-white">{{ conversion.branch_name }}</dd>
          </div>
          <div v-if="conversion.pr_url">
            <dt class="text-gray-500 dark:text-gray-400">Pull Request</dt>
            <dd>
              <a :href="conversion.pr_url" target="_blank" class="font-medium text-accent-600 hover:text-accent-700">
                Öffnen
              </a>
            </dd>
          </div>
        </dl>
      </div>

      <!-- Actions -->
      <div class="flex justify-center pt-4">
        <button
          class="px-6 py-2 rounded-lg text-sm font-medium bg-accent-600 text-white hover:bg-accent-700 transition-colors"
          @click="handleNewConversion"
        >
          Neue Konvertierung starten
        </button>
      </div>
    </div>

    <!-- Navigation (only visible when not processing and not completed) -->
    <div
      v-if="!isProcessing && conversion?.status !== 'completed' && !error"
      class="flex justify-between pt-4 border-t border-gray-200 dark:border-gray-700"
    >
      <button
        class="px-6 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
        @click="handleBack"
      >
        Zurück
      </button>
    </div>
  </div>
</template>
