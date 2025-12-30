<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const cases = ref([
  { id: 'PF-2024-0042', project: 'ESF-Vorhaben 2024-123', status: 'in_progress', type: 'system', findings: 2, createdAt: '2024-01-15' },
  { id: 'PF-2024-0041', project: 'EFRE-Vorhaben 2024-089', status: 'completed', type: 'project', findings: 0, createdAt: '2024-01-10' },
  { id: 'PF-2024-0040', project: 'ESF-Vorhaben 2024-078', status: 'review', type: 'project', findings: 3, createdAt: '2024-01-08' },
  { id: 'PF-2024-0039', project: 'EFRE-Vorhaben 2024-056', status: 'open', type: 'system', findings: 0, createdAt: '2024-01-05' },
])

const statusColors: Record<string, string> = {
  open: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
  in_progress: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
  review: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
}

const typeColors: Record<string, string> = {
  system: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
  project: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-300',
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ t('nav.auditCases') }}
        </h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {{ t('auditCases.description') }}
        </p>
      </div>
      <button class="btn-primary">
        <svg class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        {{ t('auditCases.newCase') }}
      </button>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-4">
      <div class="card p-4">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ t('auditCases.totalCases') }}</div>
        <div class="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">24</div>
      </div>
      <div class="card p-4">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ t('auditCases.statusOpen') }}</div>
        <div class="mt-1 text-2xl font-semibold text-blue-600">8</div>
      </div>
      <div class="card p-4">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ t('auditCases.statusInProgress') }}</div>
        <div class="mt-1 text-2xl font-semibold text-yellow-600">6</div>
      </div>
      <div class="card p-4">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ t('auditCases.totalFindings') }}</div>
        <div class="mt-1 text-2xl font-semibold text-red-600">12</div>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="card">
      <div class="card-body flex flex-wrap gap-4">
        <div class="flex-1 min-w-[200px]">
          <input
            type="text"
            class="input"
            :placeholder="t('common.search')"
          />
        </div>
        <select class="input w-auto">
          <option value="">{{ t('auditCases.allStatus') }}</option>
          <option value="open">{{ t('auditCases.statusOpen') }}</option>
          <option value="in_progress">{{ t('auditCases.statusInProgress') }}</option>
          <option value="review">{{ t('auditCases.statusReview') }}</option>
          <option value="completed">{{ t('auditCases.statusCompleted') }}</option>
        </select>
        <select class="input w-auto">
          <option value="">{{ t('auditCases.allTypes') }}</option>
          <option value="system">{{ t('auditCases.typeSystem') }}</option>
          <option value="project">{{ t('auditCases.typeProject') }}</option>
        </select>
      </div>
    </div>

    <!-- Table -->
    <div class="card overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead class="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {{ t('auditCases.caseId') }}
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {{ t('auditCases.project') }}
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {{ t('auditCases.type') }}
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {{ t('auditCases.status') }}
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {{ t('auditCases.findings') }}
            </th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {{ t('common.actions') }}
            </th>
          </tr>
        </thead>
        <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          <tr v-for="auditCase in cases" :key="auditCase.id" class="hover:bg-gray-50 dark:hover:bg-gray-800">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm font-medium text-gray-900 dark:text-white">
                {{ auditCase.id }}
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400">
                {{ auditCase.createdAt }}
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
              {{ auditCase.project }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span :class="['px-2 py-1 text-xs font-medium rounded-full', typeColors[auditCase.type]]">
                {{ t(`auditCases.type${auditCase.type.charAt(0).toUpperCase() + auditCase.type.slice(1)}`) }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span :class="['px-2 py-1 text-xs font-medium rounded-full', statusColors[auditCase.status]]">
                {{ t(`auditCases.status${auditCase.status.split('_').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join('')}`) }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span
                :class="[
                  'text-sm font-medium',
                  auditCase.findings > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'
                ]"
              >
                {{ auditCase.findings }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm">
              <button class="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300">
                {{ t('common.view') }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
