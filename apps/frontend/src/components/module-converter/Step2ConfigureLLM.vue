<script setup lang="ts">
import { ref, computed } from 'vue'
import { useModuleConverterStore } from '@/stores/moduleConverter'
import type { LLMConfiguration, LLMProvider } from '@/types/moduleConverter'

const store = useModuleConverterStore()

const llmConfigs = computed(() => store.activeLLMConfigs)
const selectedConfig = computed(() => store.wizardState.selectedLLMConfig)

const showCreateForm = ref(false)
const isCreating = ref(false)
const isTesting = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)

const newConfig = ref({
  name: '',
  provider: 'openai' as LLMProvider,
  model: '',
  api_key: '',
  temperature: 0.7,
  max_tokens: 4096,
})

const providerModels: Record<LLMProvider, string[]> = {
  openai: ['gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
  anthropic: ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
  ollama: ['llama2', 'codellama', 'mistral', 'mixtral'],
  azure: ['gpt-4', 'gpt-35-turbo'],
}

const availableModels = computed(() => providerModels[newConfig.value.provider] || [])

function selectConfig(config: LLMConfiguration) {
  store.selectLLMConfig(config)
  testResult.value = null
}

async function testConnection() {
  if (!selectedConfig.value) return

  isTesting.value = true
  testResult.value = null

  try {
    testResult.value = await store.testLLMConnection(selectedConfig.value.id)
  } catch (e) {
    testResult.value = {
      success: false,
      message: e instanceof Error ? e.message : 'Verbindungstest fehlgeschlagen',
    }
  } finally {
    isTesting.value = false
  }
}

async function createConfig() {
  if (!newConfig.value.name || !newConfig.value.api_key) return

  isCreating.value = true
  try {
    const config = await store.createLLMConfig(newConfig.value)
    store.selectLLMConfig(config)
    showCreateForm.value = false
    newConfig.value = {
      name: '',
      provider: 'openai',
      model: '',
      api_key: '',
      temperature: 0.7,
      max_tokens: 4096,
    }
  } catch (e) {
    // Error handled by store
  } finally {
    isCreating.value = false
  }
}

function handleBack() {
  store.previousStep()
}

function handleNext() {
  if (store.canProceedToStep3) {
    store.nextStep()
  }
}

function getProviderLabel(provider: LLMProvider): string {
  const labels: Record<LLMProvider, string> = {
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    ollama: 'Ollama (Lokal)',
    azure: 'Azure OpenAI',
  }
  return labels[provider]
}

function getProviderColor(provider: LLMProvider): string {
  const colors: Record<LLMProvider, string> = {
    openai: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
    anthropic: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
    ollama: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    azure: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  }
  return colors[provider]
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h2 class="text-lg font-medium text-gray-900 dark:text-white">
        LLM konfigurieren
      </h2>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Wählen oder erstellen Sie eine KI-Konfiguration
      </p>
    </div>

    <!-- Configuration List -->
    <div v-if="!showCreateForm" class="space-y-4">
      <!-- Existing Configs -->
      <div v-if="llmConfigs.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          v-for="config in llmConfigs"
          :key="config.id"
          :class="[
            'relative flex flex-col items-start p-4 rounded-xl border-2 text-left transition-all',
            selectedConfig?.id === config.id
              ? 'border-accent-500 bg-accent-50 dark:bg-accent-900/20 ring-2 ring-accent-500'
              : 'border-gray-200 dark:border-gray-700 hover:border-accent-300 dark:hover:border-accent-700'
          ]"
          @click="selectConfig(config)"
        >
          <div class="flex items-center gap-3 w-full">
            <div
              :class="[
                'flex h-10 w-10 items-center justify-center rounded-lg',
                selectedConfig?.id === config.id
                  ? 'bg-accent-100 dark:bg-accent-800'
                  : 'bg-gray-100 dark:bg-gray-700'
              ]"
            >
              <svg class="h-5 w-5 text-gray-600 dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="text-sm font-medium text-gray-900 dark:text-white truncate">
                {{ config.name }}
              </h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                {{ config.model }}
              </p>
            </div>
            <span
              v-if="config.is_default"
              class="px-2 py-0.5 text-xs font-medium bg-accent-100 text-accent-700 dark:bg-accent-900/30 dark:text-accent-300 rounded"
            >
              Standard
            </span>
          </div>

          <div class="mt-3 flex flex-wrap gap-2">
            <span :class="['px-2 py-0.5 rounded text-xs font-medium', getProviderColor(config.provider)]">
              {{ getProviderLabel(config.provider) }}
            </span>
            <span class="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
              Temp: {{ config.temperature }}
            </span>
          </div>

          <!-- Selected Indicator -->
          <div v-if="selectedConfig?.id === config.id" class="absolute top-2 right-2">
            <svg class="h-5 w-5 text-accent-600" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
          </div>
        </button>
      </div>

      <!-- Test Connection -->
      <div v-if="selectedConfig" class="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-900 dark:text-white">
              Verbindung testen
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              Prüfen Sie, ob die Verbindung zum LLM-Provider funktioniert
            </p>
          </div>
          <button
            :disabled="isTesting"
            class="px-4 py-2 text-sm font-medium text-accent-600 hover:text-accent-700 hover:bg-accent-50 dark:hover:bg-accent-900/20 rounded-lg transition-colors"
            @click="testConnection"
          >
            <span v-if="isTesting" class="flex items-center gap-2">
              <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Teste...
            </span>
            <span v-else>Testen</span>
          </button>
        </div>

        <!-- Test Result -->
        <div
          v-if="testResult"
          :class="[
            'mt-3 p-3 rounded-lg text-sm',
            testResult.success
              ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
              : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'
          ]"
        >
          <div class="flex items-center gap-2">
            <svg v-if="testResult.success" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            {{ testResult.message }}
          </div>
        </div>
      </div>

      <!-- Add New Button -->
      <button
        class="w-full p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-accent-400 dark:hover:border-accent-500 transition-colors"
        @click="showCreateForm = true"
      >
        <div class="flex items-center justify-center gap-2 text-gray-600 dark:text-gray-400">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span class="text-sm font-medium">Neue Konfiguration erstellen</span>
        </div>
      </button>
    </div>

    <!-- Create Form -->
    <div v-else class="space-y-4 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
      <h3 class="text-sm font-medium text-gray-900 dark:text-white">
        Neue LLM-Konfiguration
      </h3>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Name
          </label>
          <input
            v-model="newConfig.name"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-accent-500 focus:border-transparent"
            placeholder="Meine OpenAI Config"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Provider
          </label>
          <select
            v-model="newConfig.provider"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-accent-500 focus:border-transparent"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="ollama">Ollama (Lokal)</option>
            <option value="azure">Azure OpenAI</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Modell
          </label>
          <select
            v-model="newConfig.model"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-accent-500 focus:border-transparent"
          >
            <option value="">Modell wählen...</option>
            <option v-for="model in availableModels" :key="model" :value="model">
              {{ model }}
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            API Key
          </label>
          <input
            v-model="newConfig.api_key"
            type="password"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-accent-500 focus:border-transparent"
            placeholder="sk-..."
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Temperatur: {{ newConfig.temperature }}
          </label>
          <input
            v-model.number="newConfig.temperature"
            type="range"
            min="0"
            max="1"
            step="0.1"
            class="w-full"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Max Tokens
          </label>
          <input
            v-model.number="newConfig.max_tokens"
            type="number"
            min="256"
            max="32000"
            step="256"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-accent-500 focus:border-transparent"
          />
        </div>
      </div>

      <div class="flex justify-end gap-3 pt-2">
        <button
          class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
          @click="showCreateForm = false"
        >
          Abbrechen
        </button>
        <button
          :disabled="isCreating || !newConfig.name || !newConfig.api_key"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            !isCreating && newConfig.name && newConfig.api_key
              ? 'bg-accent-600 text-white hover:bg-accent-700'
              : 'bg-gray-100 text-gray-400 dark:bg-gray-700 dark:text-gray-500 cursor-not-allowed'
          ]"
          @click="createConfig"
        >
          <span v-if="isCreating" class="flex items-center gap-2">
            <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Erstelle...
          </span>
          <span v-else>Erstellen</span>
        </button>
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
        :disabled="!store.canProceedToStep3"
        :class="[
          'px-6 py-2 rounded-lg text-sm font-medium transition-colors',
          store.canProceedToStep3
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
