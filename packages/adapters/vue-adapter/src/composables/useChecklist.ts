/**
 * useChecklist - Composable für Checklisten-Verwaltung
 */

import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type {
  ChecklistTemplate,
  FieldSchema,
  ValidationError,
} from '@flowaudit/checklists'
import {
  calculateCompletionPercentage,
  validateChecklistData,
  isFieldVisible,
} from '@flowaudit/checklists'

export interface UseChecklistOptions {
  template: ChecklistTemplate
  initialData?: Record<string, unknown>
  autoValidate?: boolean
}

export interface UseChecklistReturn {
  data: Ref<Record<string, unknown>>
  errors: Ref<ValidationError[]>
  completionPercentage: ComputedRef<number>
  isComplete: ComputedRef<boolean>
  visibleFields: ComputedRef<FieldSchema[]>

  setValue: (field: string, value: unknown) => void
  getValue: (field: string) => unknown
  validate: () => boolean
  reset: () => void
  getFieldError: (field: string) => string | undefined
}

export function useChecklist(options: UseChecklistOptions): UseChecklistReturn {
  const { template, initialData = {}, autoValidate = true } = options

  const data = ref<Record<string, unknown>>({ ...initialData })
  const errors = ref<ValidationError[]>([])

  const completionPercentage = computed(() =>
    calculateCompletionPercentage(template, data.value)
  )

  const isComplete = computed(() => completionPercentage.value === 100)

  const allFields = computed(() =>
    template.sections.flatMap((s) => s.fields)
  )

  const visibleFields = computed(() =>
    allFields.value.filter((f) => isFieldVisible(f, data.value))
  )

  function setValue(field: string, value: unknown): void {
    data.value[field] = value

    if (autoValidate) {
      validate()
    }
  }

  function getValue(field: string): unknown {
    return data.value[field]
  }

  function validate(): boolean {
    errors.value = validateChecklistData(template, data.value)
    return errors.value.length === 0
  }

  function reset(): void {
    data.value = { ...initialData }
    errors.value = []
  }

  function getFieldError(field: string): string | undefined {
    const error = errors.value.find((e) => e.field === field)
    return error?.message
  }

  return {
    data,
    errors,
    completionPercentage,
    isComplete,
    visibleFields,
    setValue,
    getValue,
    validate,
    reset,
    getFieldError,
  }
}
