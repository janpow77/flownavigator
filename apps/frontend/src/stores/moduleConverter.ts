/**
 * Module Converter Pinia Store
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  LLMConfiguration,
  ModuleTemplate,
  ModuleConversion,
  GitHubIntegration,
  WizardState,
  ConversionProgress,
} from '@/types/moduleConverter'
import * as api from '@/api/moduleConverter'

export const useModuleConverterStore = defineStore('moduleConverter', () => {
  // =============================================================================
  // State
  // =============================================================================

  const templates = ref<ModuleTemplate[]>([])
  const llmConfigs = ref<LLMConfiguration[]>([])
  const githubIntegrations = ref<GitHubIntegration[]>([])
  const conversions = ref<ModuleConversion[]>([])
  const currentConversion = ref<ModuleConversion | null>(null)

  const wizardState = ref<WizardState>({
    currentStep: 1,
    selectedTemplate: null,
    selectedLLMConfig: null,
    selectedGitHubIntegration: null,
    sourceContent: '',
    metadata: {},
    conversion: null,
    isProcessing: false,
    error: null,
  })

  const conversionProgress = ref<ConversionProgress>({
    currentStep: '',
    progress: 0,
    message: '',
  })

  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // =============================================================================
  // Computed
  // =============================================================================

  const activeTemplates = computed(() =>
    templates.value.filter(t => t.is_active)
  )

  const activeLLMConfigs = computed(() =>
    llmConfigs.value.filter(c => c.is_active)
  )

  const defaultLLMConfig = computed(() =>
    llmConfigs.value.find(c => c.is_default && c.is_active)
  )

  const activeGitHubIntegrations = computed(() =>
    githubIntegrations.value.filter(g => g.is_active)
  )

  const canProceedToStep2 = computed(() =>
    wizardState.value.selectedTemplate !== null
  )

  const canProceedToStep3 = computed(() =>
    canProceedToStep2.value && wizardState.value.selectedLLMConfig !== null
  )

  const canProceedToStep4 = computed(() =>
    canProceedToStep3.value && wizardState.value.sourceContent.trim().length > 0
  )

  const canStartConversion = computed(() =>
    canProceedToStep4.value
  )

  const wizardSteps = computed(() => [
    { number: 1, title: 'Template auswählen', description: 'Konvertierungsvorlage wählen' },
    { number: 2, title: 'LLM konfigurieren', description: 'KI-Provider auswählen' },
    { number: 3, title: 'GitHub einrichten', description: 'Repository verbinden (optional)' },
    { number: 4, title: 'Prüfen & Validieren', description: 'Eingaben überprüfen' },
    { number: 5, title: 'Ausführen', description: 'Konvertierung starten' },
  ])

  // =============================================================================
  // Actions - Data Fetching
  // =============================================================================

  async function fetchTemplates() {
    try {
      isLoading.value = true
      templates.value = await api.listModuleTemplates()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Fehler beim Laden der Templates'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function fetchLLMConfigs() {
    try {
      isLoading.value = true
      llmConfigs.value = await api.listLLMConfigurations()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Fehler beim Laden der LLM-Konfigurationen'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function fetchGitHubIntegrations() {
    try {
      isLoading.value = true
      githubIntegrations.value = await api.listGitHubIntegrations()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Fehler beim Laden der GitHub-Integrationen'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function fetchConversions() {
    try {
      isLoading.value = true
      const result = await api.listConversions()
      conversions.value = result.items
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Fehler beim Laden der Konvertierungen'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function fetchConversion(id: string) {
    try {
      isLoading.value = true
      currentConversion.value = await api.getConversion(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Fehler beim Laden der Konvertierung'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function initializeWizard() {
    await Promise.all([
      fetchTemplates(),
      fetchLLMConfigs(),
      fetchGitHubIntegrations(),
    ])

    // Auto-select default LLM config
    if (defaultLLMConfig.value) {
      wizardState.value.selectedLLMConfig = defaultLLMConfig.value
    }
  }

  // =============================================================================
  // Actions - Wizard Navigation
  // =============================================================================

  function setWizardStep(step: number) {
    if (step >= 1 && step <= 5) {
      wizardState.value.currentStep = step
    }
  }

  function nextStep() {
    if (wizardState.value.currentStep < 5) {
      wizardState.value.currentStep++
    }
  }

  function previousStep() {
    if (wizardState.value.currentStep > 1) {
      wizardState.value.currentStep--
    }
  }

  function selectTemplate(template: ModuleTemplate) {
    wizardState.value.selectedTemplate = template
  }

  function selectLLMConfig(config: LLMConfiguration) {
    wizardState.value.selectedLLMConfig = config
  }

  function selectGitHubIntegration(integration: GitHubIntegration | null) {
    wizardState.value.selectedGitHubIntegration = integration
  }

  function setSourceContent(content: string) {
    wizardState.value.sourceContent = content
  }

  function setMetadata(metadata: Record<string, unknown>) {
    wizardState.value.metadata = metadata
  }

  function resetWizard() {
    wizardState.value = {
      currentStep: 1,
      selectedTemplate: null,
      selectedLLMConfig: defaultLLMConfig.value || null,
      selectedGitHubIntegration: null,
      sourceContent: '',
      metadata: {},
      conversion: null,
      isProcessing: false,
      error: null,
    }
    conversionProgress.value = {
      currentStep: '',
      progress: 0,
      message: '',
    }
  }

  // =============================================================================
  // Actions - Conversion
  // =============================================================================

  async function startConversion() {
    if (!canStartConversion.value) {
      throw new Error('Nicht alle erforderlichen Daten vorhanden')
    }

    const { selectedTemplate, selectedLLMConfig, selectedGitHubIntegration, sourceContent, metadata } = wizardState.value

    wizardState.value.isProcessing = true
    wizardState.value.error = null
    conversionProgress.value = {
      currentStep: 'analyzing',
      progress: 10,
      message: 'Analysiere Quelldaten...',
    }

    try {
      const conversion = await api.startConversion({
        template_id: selectedTemplate!.id,
        llm_config_id: selectedLLMConfig!.id,
        source_content: sourceContent,
        github_integration_id: selectedGitHubIntegration?.id,
        metadata,
      })

      wizardState.value.conversion = conversion
      currentConversion.value = conversion

      // Start polling for status updates
      pollConversionStatus(conversion.id)

      return conversion
    } catch (e) {
      wizardState.value.error = e instanceof Error ? e.message : 'Konvertierung fehlgeschlagen'
      conversionProgress.value = {
        currentStep: 'failed',
        progress: 0,
        message: wizardState.value.error,
      }
      throw e
    }
  }

  async function pollConversionStatus(conversionId: string) {
    const pollInterval = 2000 // 2 seconds
    const maxPolls = 60 // 2 minutes max

    let pollCount = 0

    const poll = async () => {
      if (pollCount >= maxPolls) {
        wizardState.value.error = 'Timeout bei der Konvertierung'
        wizardState.value.isProcessing = false
        return
      }

      try {
        const conversion = await api.getConversion(conversionId)
        wizardState.value.conversion = conversion
        currentConversion.value = conversion

        // Update progress based on status
        updateProgressFromStatus(conversion.status)

        if (conversion.status === 'completed') {
          wizardState.value.isProcessing = false
          conversionProgress.value = {
            currentStep: 'completed',
            progress: 100,
            message: 'Konvertierung erfolgreich abgeschlossen!',
          }
          return
        }

        if (conversion.status === 'failed') {
          wizardState.value.isProcessing = false
          wizardState.value.error = conversion.error_message || 'Konvertierung fehlgeschlagen'
          conversionProgress.value = {
            currentStep: 'failed',
            progress: 0,
            message: wizardState.value.error,
          }
          return
        }

        // Continue polling
        pollCount++
        setTimeout(poll, pollInterval)
      } catch (e) {
        wizardState.value.error = e instanceof Error ? e.message : 'Statusabfrage fehlgeschlagen'
        wizardState.value.isProcessing = false
      }
    }

    await poll()
  }

  function updateProgressFromStatus(status: string) {
    const statusProgress: Record<string, { progress: number; message: string }> = {
      pending: { progress: 5, message: 'Warte auf Verarbeitung...' },
      analyzing: { progress: 20, message: 'Analysiere Quelldaten...' },
      converting: { progress: 50, message: 'Konvertiere mit KI...' },
      validating: { progress: 75, message: 'Validiere Ergebnis...' },
      staging: { progress: 90, message: 'Stage zu GitHub...' },
      completed: { progress: 100, message: 'Abgeschlossen!' },
      failed: { progress: 0, message: 'Fehlgeschlagen' },
    }

    const info = statusProgress[status] || { progress: 0, message: status }
    conversionProgress.value = {
      currentStep: status,
      progress: info.progress,
      message: info.message,
    }
  }

  async function retryConversion(id: string) {
    try {
      wizardState.value.isProcessing = true
      wizardState.value.error = null
      const conversion = await api.retryConversion(id)
      wizardState.value.conversion = conversion
      currentConversion.value = conversion
      pollConversionStatus(id)
      return conversion
    } catch (e) {
      wizardState.value.error = e instanceof Error ? e.message : 'Wiederholung fehlgeschlagen'
      wizardState.value.isProcessing = false
      throw e
    }
  }

  async function cancelConversion(id: string) {
    try {
      const conversion = await api.cancelConversion(id)
      wizardState.value.conversion = conversion
      currentConversion.value = conversion
      wizardState.value.isProcessing = false
      return conversion
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Abbruch fehlgeschlagen'
      throw e
    }
  }

  // =============================================================================
  // Actions - LLM Configuration Management
  // =============================================================================

  async function createLLMConfig(data: api.CreateLLMConfiguration) {
    try {
      isLoading.value = true
      const config = await api.createLLMConfiguration(data)
      llmConfigs.value.push(config)
      return config
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erstellung fehlgeschlagen'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function testLLMConnection(id: string) {
    try {
      return await api.testLLMConnection(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Verbindungstest fehlgeschlagen'
      throw e
    }
  }

  async function deleteLLMConfig(id: string) {
    try {
      await api.deleteLLMConfiguration(id)
      llmConfigs.value = llmConfigs.value.filter(c => c.id !== id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Löschen fehlgeschlagen'
      throw e
    }
  }

  // =============================================================================
  // Actions - GitHub Integration Management
  // =============================================================================

  async function createGitHubIntegration(data: api.CreateGitHubIntegration) {
    try {
      isLoading.value = true
      const integration = await api.createGitHubIntegration(data)
      githubIntegrations.value.push(integration)
      return integration
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erstellung fehlgeschlagen'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function testGitHubConnection(id: string) {
    try {
      return await api.testGitHubConnection(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Verbindungstest fehlgeschlagen'
      throw e
    }
  }

  async function deleteGitHubIntegration(id: string) {
    try {
      await api.deleteGitHubIntegration(id)
      githubIntegrations.value = githubIntegrations.value.filter(g => g.id !== id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Löschen fehlgeschlagen'
      throw e
    }
  }

  // =============================================================================
  // Actions - Staging
  // =============================================================================

  async function stageToGitHub(files: Array<{ path: string; content: string }>, options: {
    commitMessage: string
    branchName?: string
    createPR?: boolean
    prTitle?: string
    prBody?: string
  }) {
    if (!wizardState.value.conversion || !wizardState.value.selectedGitHubIntegration) {
      throw new Error('Konvertierung oder GitHub-Integration nicht vorhanden')
    }

    try {
      isLoading.value = true
      return await api.stageFiles({
        conversion_id: wizardState.value.conversion.id,
        github_integration_id: wizardState.value.selectedGitHubIntegration.id,
        files,
        commit_message: options.commitMessage,
        branch_name: options.branchName,
        create_pr: options.createPR,
        pr_title: options.prTitle,
        pr_body: options.prBody,
      })
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Staging fehlgeschlagen'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  function clearError() {
    error.value = null
    wizardState.value.error = null
  }

  // =============================================================================
  // Return
  // =============================================================================

  return {
    // State
    templates,
    llmConfigs,
    githubIntegrations,
    conversions,
    currentConversion,
    wizardState,
    conversionProgress,
    isLoading,
    error,

    // Computed
    activeTemplates,
    activeLLMConfigs,
    defaultLLMConfig,
    activeGitHubIntegrations,
    canProceedToStep2,
    canProceedToStep3,
    canProceedToStep4,
    canStartConversion,
    wizardSteps,

    // Actions - Data
    fetchTemplates,
    fetchLLMConfigs,
    fetchGitHubIntegrations,
    fetchConversions,
    fetchConversion,
    initializeWizard,

    // Actions - Wizard
    setWizardStep,
    nextStep,
    previousStep,
    selectTemplate,
    selectLLMConfig,
    selectGitHubIntegration,
    setSourceContent,
    setMetadata,
    resetWizard,

    // Actions - Conversion
    startConversion,
    retryConversion,
    cancelConversion,

    // Actions - LLM
    createLLMConfig,
    testLLMConnection,
    deleteLLMConfig,

    // Actions - GitHub
    createGitHubIntegration,
    testGitHubConnection,
    deleteGitHubIntegration,

    // Actions - Staging
    stageToGitHub,

    // Utilities
    clearError,
  }
})
