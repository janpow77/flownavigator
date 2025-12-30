/**
 * @flowaudit/vue-adapter
 * Vue 3 Komponenten und Composables für FlowAudit
 */

// Composables
export { useChecklist } from './composables/useChecklist'
export { useGroupQuery } from './composables/useGroupQuery'
export { useDocumentBox } from './composables/useDocumentBox'
export { useApi } from './composables/useApi'
export { usePagination } from './composables/usePagination'

// Types re-export
export type {
  ChecklistTemplate,
  ChecklistInstance,
  FieldSchema,
} from '@flowaudit/checklists'

export type {
  GroupQuery,
  GroupQueryAssignment,
  GroupQueryResponse,
} from '@flowaudit/group-queries'

export type {
  DocumentBox,
  BoxDocument,
  AiVerificationResult,
} from '@flowaudit/document-box'
