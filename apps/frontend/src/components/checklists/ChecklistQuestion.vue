<script setup lang="ts">
import { computed } from 'vue'
import type { Question } from '@/api/checklists'

const props = defineProps<{
  question: Question
  modelValue: unknown
  note?: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: unknown]
  'update:note': [value: string]
}>()

const value = computed({
  get: () => props.modelValue as string | number | string[] | null | undefined,
  set: (v) => emit('update:modelValue', v),
})

const noteValue = computed({
  get: () => props.note || '',
  set: (v) => emit('update:note', v),
})

function getYesNoNaOptions() {
  return [
    { value: 'yes', label: 'Ja', color: 'bg-green-100 text-green-800 border-green-300' },
    { value: 'no', label: 'Nein', color: 'bg-red-100 text-red-800 border-red-300' },
    { value: 'na', label: 'N.A.', color: 'bg-gray-100 text-gray-800 border-gray-300' },
  ]
}

function getYesNoOptions() {
  return [
    { value: 'yes', label: 'Ja', color: 'bg-green-100 text-green-800 border-green-300' },
    { value: 'no', label: 'Nein', color: 'bg-red-100 text-red-800 border-red-300' },
  ]
}
</script>

<template>
  <div class="space-y-2">
    <!-- Label -->
    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
      {{ question.label }}
      <span v-if="question.required" class="text-red-500">*</span>
    </label>

    <!-- Description -->
    <p v-if="question.description" class="text-sm text-gray-500 dark:text-gray-400">
      {{ question.description }}
    </p>

    <!-- Text Input -->
    <input
      v-if="question.type === 'text'"
      v-model="value"
      type="text"
      class="input"
      :placeholder="question.placeholder"
      :disabled="disabled"
      :required="question.required"
    />

    <!-- Textarea -->
    <textarea
      v-else-if="question.type === 'textarea'"
      v-model="value"
      class="input min-h-[100px]"
      :placeholder="question.placeholder"
      :disabled="disabled"
      :required="question.required"
    />

    <!-- Number -->
    <input
      v-else-if="question.type === 'number'"
      v-model.number="value"
      type="number"
      class="input"
      :placeholder="question.placeholder"
      :disabled="disabled"
      :min="question.min_value"
      :max="question.max_value"
      :required="question.required"
    />

    <!-- Currency -->
    <div v-else-if="question.type === 'currency'" class="relative">
      <input
        v-model.number="value"
        type="number"
        class="input pr-12"
        :placeholder="question.placeholder || '0,00'"
        :disabled="disabled"
        step="0.01"
        min="0"
        :required="question.required"
      />
      <span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">€</span>
    </div>

    <!-- Date -->
    <input
      v-else-if="question.type === 'date'"
      v-model="value"
      type="date"
      class="input"
      :disabled="disabled"
      :required="question.required"
    />

    <!-- Yes/No -->
    <div v-else-if="question.type === 'yes_no'" class="flex gap-2">
      <button
        v-for="option in getYesNoOptions()"
        :key="option.value"
        type="button"
        :class="[
          'px-4 py-2 rounded-lg border-2 font-medium transition-all',
          value === option.value
            ? option.color + ' border-current'
            : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-gray-300'
        ]"
        :disabled="disabled"
        @click="value = option.value"
      >
        {{ option.label }}
      </button>
    </div>

    <!-- Yes/No/NA -->
    <div v-else-if="question.type === 'yes_no_na'" class="flex gap-2">
      <button
        v-for="option in getYesNoNaOptions()"
        :key="option.value"
        type="button"
        :class="[
          'px-4 py-2 rounded-lg border-2 font-medium transition-all',
          value === option.value
            ? option.color + ' border-current'
            : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-gray-300'
        ]"
        :disabled="disabled"
        @click="value = option.value"
      >
        {{ option.label }}
      </button>
    </div>

    <!-- Select -->
    <select
      v-else-if="question.type === 'select'"
      v-model="value"
      class="input"
      :disabled="disabled"
      :required="question.required"
    >
      <option value="">Bitte wählen...</option>
      <option
        v-for="option in question.options"
        :key="option.value"
        :value="option.value"
      >
        {{ option.label }}
      </option>
    </select>

    <!-- Multiselect (Checkboxes) -->
    <div v-else-if="question.type === 'multiselect'" class="space-y-2">
      <label
        v-for="option in question.options"
        :key="option.value"
        class="flex items-center gap-2 cursor-pointer"
      >
        <input
          type="checkbox"
          :value="option.value"
          :checked="Array.isArray(value) && value.includes(option.value)"
          :disabled="disabled"
          class="rounded border-gray-300 text-accent-600 focus:ring-accent-500"
          @change="(e) => {
            const checked = (e.target as HTMLInputElement).checked
            const arr = Array.isArray(value) ? [...value] : []
            if (checked) {
              arr.push(option.value)
            } else {
              const idx = arr.indexOf(option.value)
              if (idx > -1) arr.splice(idx, 1)
            }
            value = arr
          }"
        />
        <span class="text-sm text-gray-700 dark:text-gray-300">{{ option.label }}</span>
      </label>
    </div>

    <!-- Rating -->
    <div v-else-if="question.type === 'rating'" class="flex gap-1">
      <button
        v-for="n in 5"
        :key="n"
        type="button"
        :class="[
          'w-10 h-10 rounded-lg border-2 font-medium transition-all',
          value === n
            ? 'bg-accent-100 text-accent-800 border-accent-500'
            : 'bg-white dark:bg-gray-800 text-gray-600 border-gray-200 dark:border-gray-700 hover:border-gray-300'
        ]"
        :disabled="disabled"
        @click="value = n"
      >
        {{ n }}
      </button>
    </div>

    <!-- Note Field -->
    <div class="mt-2">
      <button
        v-if="!noteValue"
        type="button"
        class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
        @click="noteValue = ' '"
      >
        + Bemerkung hinzufügen
      </button>
      <div v-else>
        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Bemerkung</label>
        <textarea
          v-model="noteValue"
          class="input text-sm min-h-[60px]"
          placeholder="Optionale Bemerkung..."
          :disabled="disabled"
        />
      </div>
    </div>
  </div>
</template>
