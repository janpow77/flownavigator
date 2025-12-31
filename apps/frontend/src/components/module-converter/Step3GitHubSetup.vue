<script setup lang="ts">
import { ref, computed } from 'vue'
import { useModuleConverterStore } from '@/stores/moduleConverter'
import type { GitHubIntegration } from '@/types/moduleConverter'

const store = useModuleConverterStore()

const integrations = computed(() => store.activeGitHubIntegrations)
const selectedIntegration = computed(() => store.wizardState.selectedGitHubIntegration)

const showCreateForm = ref(false)
const isCreating = ref(false)
const isTesting = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)

const newIntegration = ref({
  name: '',
  repository_owner: '',
  repository_name: '',
  access_token: '',
  default_branch: 'main',
})

function selectIntegration(integration: GitHubIntegration | null) {
  store.selectGitHubIntegration(integration)
  testResult.value = null
}

async function testConnection() {
  if (!selectedIntegration.value) return

  isTesting.value = true
  testResult.value = null

  try {
    testResult.value = await store.testGitHubConnection(selectedIntegration.value.id)
  } catch (e) {
    testResult.value = {
      success: false,
      message: e instanceof Error ? e.message : 'Verbindungstest fehlgeschlagen',
    }
  } finally {
    isTesting.value = false
  }
}

async function createIntegration() {
  if (!newIntegration.value.name || !newIntegration.value.access_token) return

  isCreating.value = true
  try {
    const integration = await store.createGitHubIntegration(newIntegration.value)
    store.selectGitHubIntegration(integration)
    showCreateForm.value = false
    newIntegration.value = {
      name: '',
      repository_owner: '',
      repository_name: '',
      access_token: '',
      default_branch: 'main',
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
  store.nextStep()
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h2 class="text-lg font-medium text-gray-900 dark:text-white">
        GitHub einrichten
      </h2>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Verbinden Sie ein GitHub-Repository (optional)
      </p>
    </div>

    <!-- Optional Info -->
    <div class="flex items-start gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
      <svg class="w-5 h-5 text-blue-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <div class="text-sm text-blue-700 dark:text-blue-300">
        <p class="font-medium">Dieser Schritt ist optional</p>
        <p class="mt-1">
          Wenn Sie ein Repository verbinden, werden konvertierte Module automatisch als Branch/PR staged.
          Sie können diesen Schritt überspringen und Ergebnisse manuell herunterladen.
        </p>
      </div>
    </div>

    <!-- Integration List -->
    <div v-if="!showCreateForm" class="space-y-4">
      <!-- Skip Option -->
      <button
        :class="[
          'w-full flex items-center justify-between p-4 rounded-xl border-2 text-left transition-all',
          selectedIntegration === null
            ? 'border-accent-500 bg-accent-50 dark:bg-accent-900/20 ring-2 ring-accent-500'
            : 'border-gray-200 dark:border-gray-700 hover:border-accent-300 dark:hover:border-accent-700'
        ]"
        @click="selectIntegration(null)"
      >
        <div class="flex items-center gap-3">
          <div
            :class="[
              'flex h-10 w-10 items-center justify-center rounded-lg',
              selectedIntegration === null
                ? 'bg-accent-100 dark:bg-accent-800'
                : 'bg-gray-100 dark:bg-gray-700'
            ]"
          >
            <svg class="h-5 w-5 text-gray-600 dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </div>
          <div>
            <h3 class="text-sm font-medium text-gray-900 dark:text-white">
              Kein GitHub verwenden
            </h3>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              Ergebnisse manuell herunterladen
            </p>
          </div>
        </div>
        <div v-if="selectedIntegration === null">
          <svg class="h-5 w-5 text-accent-600" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
        </div>
      </button>

      <!-- Existing Integrations -->
      <div v-if="integrations.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          v-for="integration in integrations"
          :key="integration.id"
          :class="[
            'relative flex flex-col items-start p-4 rounded-xl border-2 text-left transition-all',
            selectedIntegration?.id === integration.id
              ? 'border-accent-500 bg-accent-50 dark:bg-accent-900/20 ring-2 ring-accent-500'
              : 'border-gray-200 dark:border-gray-700 hover:border-accent-300 dark:hover:border-accent-700'
          ]"
          @click="selectIntegration(integration)"
        >
          <div class="flex items-center gap-3 w-full">
            <div
              :class="[
                'flex h-10 w-10 items-center justify-center rounded-lg',
                selectedIntegration?.id === integration.id
                  ? 'bg-accent-100 dark:bg-accent-800'
                  : 'bg-gray-100 dark:bg-gray-700'
              ]"
            >
              <!-- GitHub Icon -->
              <svg class="h-5 w-5 text-gray-600 dark:text-gray-300" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="text-sm font-medium text-gray-900 dark:text-white truncate">
                {{ integration.name }}
              </h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                {{ integration.repository_owner }}/{{ integration.repository_name }}
              </p>
            </div>
          </div>

          <div class="mt-3 flex flex-wrap gap-2">
            <span class="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
              Branch: {{ integration.default_branch }}
            </span>
            <span v-if="integration.last_sync_at" class="px-2 py-0.5 rounded text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300">
              Synchronisiert
            </span>
          </div>

          <!-- Selected Indicator -->
          <div v-if="selectedIntegration?.id === integration.id" class="absolute top-2 right-2">
            <svg class="h-5 w-5 text-accent-600" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
          </div>
        </button>
      </div>

      <!-- Test Connection -->
      <div v-if="selectedIntegration" class="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-900 dark:text-white">
              Verbindung testen
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              Prüfen Sie den Zugriff auf das Repository
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
          <span class="text-sm font-medium">GitHub-Repository verbinden</span>
        </div>
      </button>
    </div>

    <!-- Create Form -->
    <div v-else class="space-y-4 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
      <h3 class="text-sm font-medium text-gray-900 dark:text-white">
        GitHub-Repository verbinden
      </h3>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Name
          </label>
          <input
            v-model="newIntegration.name"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-accent-500 focus:border-transparent"
            placeholder="Mein Projekt"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Repository Owner
          </label>
          <input
            v-model="newIntegration.repository_owner"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-accent-500 focus:border-transparent"
            placeholder="username oder organization"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Repository Name
          </label>
          <input
            v-model="newIntegration.repository_name"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-accent-500 focus:border-transparent"
            placeholder="my-repo"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Default Branch
          </label>
          <input
            v-model="newIntegration.default_branch"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-accent-500 focus:border-transparent"
            placeholder="main"
          />
        </div>

        <div class="md:col-span-2">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Personal Access Token
          </label>
          <input
            v-model="newIntegration.access_token"
            type="password"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-accent-500 focus:border-transparent"
            placeholder="ghp_..."
          />
          <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Erstellen Sie einen PAT mit "repo" Berechtigungen unter GitHub Settings &gt; Developer settings &gt; Personal access tokens
          </p>
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
          :disabled="isCreating || !newIntegration.name || !newIntegration.access_token"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            !isCreating && newIntegration.name && newIntegration.access_token
              ? 'bg-accent-600 text-white hover:bg-accent-700'
              : 'bg-gray-100 text-gray-400 dark:bg-gray-700 dark:text-gray-500 cursor-not-allowed'
          ]"
          @click="createIntegration"
        >
          <span v-if="isCreating" class="flex items-center gap-2">
            <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Verbinde...
          </span>
          <span v-else>Verbinden</span>
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
        class="px-6 py-2 rounded-lg text-sm font-medium bg-accent-600 text-white hover:bg-accent-700 transition-colors"
        @click="handleNext"
      >
        Weiter
      </button>
    </div>
  </div>
</template>
