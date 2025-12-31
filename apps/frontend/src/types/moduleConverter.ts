/**
 * Module Converter Types
 */

export type LLMProvider = 'openai' | 'anthropic' | 'ollama' | 'azure'
export type ConversionStatus = 'pending' | 'analyzing' | 'converting' | 'validating' | 'staging' | 'completed' | 'failed'
export type ModuleType = 'checklist' | 'questionnaire' | 'workflow' | 'report' | 'form'

export interface LLMConfiguration {
  id: string
  name: string
  provider: LLMProvider
  model: string
  is_active: boolean
  is_default: boolean
  temperature: number
  max_tokens: number
  requests_per_minute: number
  created_at: string
  updated_at: string
}

export interface CreateLLMConfiguration {
  name: string
  provider: LLMProvider
  model: string
  api_key: string
  api_base_url?: string
  temperature?: number
  max_tokens?: number
  requests_per_minute?: number
  is_default?: boolean
}

export interface ModuleTemplate {
  id: string
  name: string
  description: string
  module_type: ModuleType
  source_format: string
  target_format: string
  prompt_template: string
  validation_rules: Record<string, unknown>
  is_active: boolean
  version: string
  created_at: string
  updated_at: string
}

export interface CreateModuleTemplate {
  name: string
  description: string
  module_type: ModuleType
  source_format: string
  target_format: string
  prompt_template: string
  validation_rules?: Record<string, unknown>
}

export interface ConversionStep {
  id: string
  conversion_id: string
  step_name: string
  step_order: number
  status: ConversionStatus
  input_data: Record<string, unknown>
  output_data: Record<string, unknown>
  error_message?: string
  started_at?: string
  completed_at?: string
  duration_ms?: number
}

export interface ModuleConversion {
  id: string
  template_id: string
  llm_config_id: string
  github_integration_id?: string
  source_content: string
  converted_content?: string
  status: ConversionStatus
  error_message?: string
  validation_result?: Record<string, unknown>
  metadata: Record<string, unknown>
  branch_name?: string
  pr_url?: string
  created_by: string
  created_at: string
  updated_at: string
  completed_at?: string
  steps?: ConversionStep[]
}

export interface StartConversionRequest {
  template_id: string
  llm_config_id: string
  source_content: string
  github_integration_id?: string
  metadata?: Record<string, unknown>
}

export interface GitHubIntegration {
  id: string
  name: string
  repository_owner: string
  repository_name: string
  default_branch: string
  is_active: boolean
  last_sync_at?: string
  created_at: string
  updated_at: string
}

export interface CreateGitHubIntegration {
  name: string
  repository_owner: string
  repository_name: string
  access_token: string
  default_branch?: string
}

export interface GitHubRepository {
  name: string
  full_name: string
  default_branch: string
  private: boolean
  url: string
}

export interface GitHubBranch {
  name: string
  sha: string
  protected: boolean
}

export interface StageFilesRequest {
  conversion_id: string
  github_integration_id: string
  files: Array<{
    path: string
    content: string
  }>
  commit_message: string
  branch_name?: string
  create_pr?: boolean
  pr_title?: string
  pr_body?: string
}

export interface StageFilesResponse {
  branch_name: string
  commit_sha: string
  pr_url?: string
  pr_number?: number
}

export interface WizardState {
  currentStep: number
  selectedTemplate: ModuleTemplate | null
  selectedLLMConfig: LLMConfiguration | null
  selectedGitHubIntegration: GitHubIntegration | null
  sourceContent: string
  metadata: Record<string, unknown>
  conversion: ModuleConversion | null
  isProcessing: boolean
  error: string | null
}

export interface ValidationError {
  field: string
  message: string
  code: string
}

export interface ConversionProgress {
  currentStep: string
  progress: number
  message: string
}
