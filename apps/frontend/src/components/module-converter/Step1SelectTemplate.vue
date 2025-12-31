<script setup lang="ts">
import { computed } from 'vue'
import { useModuleConverterStore } from '@/stores/moduleConverter'
import type { ModuleTemplate } from '@/types/moduleConverter'

const store = useModuleConverterStore()

const templates = computed(() => store.activeTemplates)
const selectedTemplate = computed(() => store.wizardState.selectedTemplate)

function selectTemplate(template: ModuleTemplate) {
  store.selectTemplate(template)
}

function handleNext() {
  if (store.canProceedToStep2) {
    store.nextStep()
  }
}

function getModuleTypeIcon(type: string): string {
  const icons: Record<string, string> = {
    checklist: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
    questionnaire: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    workflow: 'M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z',
    report: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    form: 'M4 6h16M4 10h16M4 14h16M4 18h16',
  }
  return icons[type] || icons.form
}

function getModuleTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    checklist: 'Checkliste',
    questionnaire: 'Fragebogen',
    workflow: 'Workflow',
    report: 'Bericht',
    form: 'Formular',
  }
  return labels[type] || type
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h2 class="text-lg font-medium text-gray-900 dark:text-white">
        Template auswählen
      </h2>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Wählen Sie eine Konvertierungsvorlage für Ihr Modul
      </p>
    </div>

    <!-- Templates Grid -->
    <div v-if="templates.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <button
        v-for="template in templates"
        :key="template.id"
        :class="[
          'relative flex flex-col items-start p-4 rounded-xl border-2 text-left transition-all',
          selectedTemplate?.id === template.id
            ? 'border-accent-500 bg-accent-50 dark:bg-accent-900/20 ring-2 ring-accent-500'
            : 'border-gray-200 dark:border-gray-700 hover:border-accent-300 dark:hover:border-accent-700'
        ]"
        @click="selectTemplate(template)"
      >
        <!-- Icon -->
        <div
          :class="[
            'flex h-12 w-12 items-center justify-center rounded-lg',
            selectedTemplate?.id === template.id
              ? 'bg-accent-100 dark:bg-accent-800'
              : 'bg-gray-100 dark:bg-gray-700'
          ]"
        >
          <svg
            :class="[
              'h-6 w-6',
              selectedTemplate?.id === template.id
                ? 'text-accent-600 dark:text-accent-400'
                : 'text-gray-500 dark:text-gray-400'
            ]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              :d="getModuleTypeIcon(template.module_type)"
            />
          </svg>
        </div>

        <!-- Content -->
        <div class="mt-4 flex-1">
          <h3 class="text-sm font-medium text-gray-900 dark:text-white">
            {{ template.name }}
          </h3>
          <p class="mt-1 text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
            {{ template.description }}
          </p>
        </div>

        <!-- Tags -->
        <div class="mt-3 flex flex-wrap gap-2">
          <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
            {{ getModuleTypeLabel(template.module_type) }}
          </span>
          <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
            {{ template.source_format }} → {{ template.target_format }}
          </span>
        </div>

        <!-- Selected Indicator -->
        <div
          v-if="selectedTemplate?.id === template.id"
          class="absolute top-2 right-2"
        >
          <svg class="h-5 w-5 text-accent-600" viewBox="0 0 20 20" fill="currentColor">
            <path
              fill-rule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clip-rule="evenodd"
            />
          </svg>
        </div>
      </button>
    </div>

    <!-- Empty State -->
    <div
      v-else
      class="text-center py-12 bg-gray-50 dark:bg-gray-800/50 rounded-lg"
    >
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
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">
        Keine Templates verfügbar
      </h3>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Erstellen Sie zuerst ein Konvertierungs-Template.
      </p>
    </div>

    <!-- Navigation -->
    <div class="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
      <button
        :disabled="!store.canProceedToStep2"
        :class="[
          'px-6 py-2 rounded-lg text-sm font-medium transition-colors',
          store.canProceedToStep2
            ? 'bg-accent-600 text-white hover:bg-accent-700'
            : 'bg-gray-100 text-gray-400 dark:bg-gray-700 dark:text-gray-500 cursor-not-allowed'
        ]"
        @click="handleNext"
      >
        Weiter
      </button>
    </div>
  </div>
</template>
