<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useModuleConverterStore } from '@/stores/moduleConverter'
import WizardStepper from '@/components/module-converter/WizardStepper.vue'
import Step1SelectTemplate from '@/components/module-converter/Step1SelectTemplate.vue'
import Step2ConfigureLLM from '@/components/module-converter/Step2ConfigureLLM.vue'
import Step3GitHubSetup from '@/components/module-converter/Step3GitHubSetup.vue'
import Step4ReviewValidate from '@/components/module-converter/Step4ReviewValidate.vue'
import Step5Execute from '@/components/module-converter/Step5Execute.vue'

const store = useModuleConverterStore()

const currentStep = computed(() => store.wizardState.currentStep)
const isLoading = computed(() => store.isLoading)
const error = computed(() => store.error)

onMounted(async () => {
  await store.initializeWizard()
})

function handleReset() {
  store.resetWizard()
}
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            Module Converter
          </h1>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Konvertieren Sie Module mit KI-Unterstützung
          </p>
        </div>
        <button
          v-if="currentStep > 1"
          class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
          @click="handleReset"
        >
          Neu starten
        </button>
      </div>
    </div>

    <!-- Error Alert -->
    <div
      v-if="error"
      class="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
    >
      <div class="flex items-center gap-3">
        <svg class="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-sm text-red-700 dark:text-red-300">{{ error }}</p>
        <button
          class="ml-auto text-red-500 hover:text-red-700"
          @click="store.clearError()"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div
      v-if="isLoading && !store.wizardState.isProcessing"
      class="flex items-center justify-center py-12"
    >
      <div class="flex items-center gap-3">
        <svg class="w-6 h-6 animate-spin text-accent-600" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <span class="text-gray-600 dark:text-gray-400">Lade Daten...</span>
      </div>
    </div>

    <!-- Wizard Content -->
    <div v-else class="space-y-6">
      <!-- Stepper -->
      <WizardStepper />

      <!-- Step Content -->
      <div class="card">
        <div class="card-body">
          <Step1SelectTemplate v-if="currentStep === 1" />
          <Step2ConfigureLLM v-else-if="currentStep === 2" />
          <Step3GitHubSetup v-else-if="currentStep === 3" />
          <Step4ReviewValidate v-else-if="currentStep === 4" />
          <Step5Execute v-else-if="currentStep === 5" />
        </div>
      </div>
    </div>
  </div>
</template>
