<script setup lang="ts">
import { computed } from 'vue'
import { useModuleConverterStore } from '@/stores/moduleConverter'

const store = useModuleConverterStore()

const steps = computed(() => store.wizardSteps)
const currentStep = computed(() => store.wizardState.currentStep)

function getStepStatus(stepNumber: number): 'completed' | 'current' | 'upcoming' {
  if (stepNumber < currentStep.value) return 'completed'
  if (stepNumber === currentStep.value) return 'current'
  return 'upcoming'
}

function canNavigateToStep(stepNumber: number): boolean {
  if (stepNumber === 1) return true
  if (stepNumber === 2) return store.canProceedToStep2
  if (stepNumber === 3) return store.canProceedToStep3
  if (stepNumber === 4) return store.canProceedToStep4
  if (stepNumber === 5) return store.canStartConversion
  return false
}

function navigateToStep(stepNumber: number) {
  if (canNavigateToStep(stepNumber) && stepNumber <= currentStep.value) {
    store.setWizardStep(stepNumber)
  }
}
</script>

<template>
  <nav aria-label="Progress">
    <ol class="flex items-center">
      <li
        v-for="(step, index) in steps"
        :key="step.number"
        :class="[
          'relative',
          index !== steps.length - 1 ? 'flex-1' : ''
        ]"
      >
        <div class="flex items-center">
          <!-- Step Circle -->
          <button
            :disabled="!canNavigateToStep(step.number) || step.number > currentStep"
            :class="[
              'relative flex h-10 w-10 items-center justify-center rounded-full transition-colors',
              getStepStatus(step.number) === 'completed'
                ? 'bg-accent-600 hover:bg-accent-700 cursor-pointer'
                : getStepStatus(step.number) === 'current'
                  ? 'bg-accent-600 ring-4 ring-accent-100 dark:ring-accent-900'
                  : 'bg-gray-200 dark:bg-gray-700'
            ]"
            @click="navigateToStep(step.number)"
          >
            <!-- Completed Check -->
            <svg
              v-if="getStepStatus(step.number) === 'completed'"
              class="h-5 w-5 text-white"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clip-rule="evenodd"
              />
            </svg>
            <!-- Current/Upcoming Number -->
            <span
              v-else
              :class="[
                'text-sm font-medium',
                getStepStatus(step.number) === 'current'
                  ? 'text-white'
                  : 'text-gray-500 dark:text-gray-400'
              ]"
            >
              {{ step.number }}
            </span>
          </button>

          <!-- Connector Line -->
          <div
            v-if="index !== steps.length - 1"
            :class="[
              'ml-4 flex-1 h-0.5',
              getStepStatus(step.number) === 'completed'
                ? 'bg-accent-600'
                : 'bg-gray-200 dark:bg-gray-700'
            ]"
          />
        </div>

        <!-- Step Label (visible on larger screens) -->
        <div class="mt-2 hidden sm:block">
          <p
            :class="[
              'text-xs font-medium',
              getStepStatus(step.number) === 'current'
                ? 'text-accent-600 dark:text-accent-400'
                : getStepStatus(step.number) === 'completed'
                  ? 'text-gray-900 dark:text-white'
                  : 'text-gray-500 dark:text-gray-400'
            ]"
          >
            {{ step.title }}
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            {{ step.description }}
          </p>
        </div>
      </li>
    </ol>
  </nav>
</template>
