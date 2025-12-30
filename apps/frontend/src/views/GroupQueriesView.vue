<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const queries = ref([
  { id: 1, name: 'Jahresabfrage 2024', status: 'open', dueDate: '2024-03-31', recipients: 12, responses: 8 },
  { id: 2, name: 'Quartalsabfrage Q1', status: 'open', dueDate: '2024-02-15', recipients: 8, responses: 8 },
  { id: 3, name: 'Jahresabfrage 2023', status: 'closed', dueDate: '2023-12-31', recipients: 10, responses: 10 },
  { id: 4, name: 'Sonderabfrage ESF', status: 'draft', dueDate: '2024-04-30', recipients: 5, responses: 0 },
])

const statusColors: Record<string, string> = {
  open: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  closed: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  draft: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ t('nav.groupQueries') }}
        </h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {{ t('groupQueries.description') }}
        </p>
      </div>
      <button class="btn-primary">
        <svg class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        {{ t('groupQueries.newQuery') }}
      </button>
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
          <option value="">{{ t('groupQueries.allStatus') }}</option>
          <option value="open">{{ t('groupQueries.statusOpen') }}</option>
          <option value="closed">{{ t('groupQueries.statusClosed') }}</option>
          <option value="draft">{{ t('groupQueries.statusDraft') }}</option>
        </select>
      </div>
    </div>

    <!-- Table -->
    <div class="card overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead class="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {{ t('groupQueries.name') }}
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {{ t('groupQueries.status') }}
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {{ t('groupQueries.dueDate') }}
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {{ t('groupQueries.progress') }}
            </th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {{ t('common.actions') }}
            </th>
          </tr>
        </thead>
        <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          <tr v-for="query in queries" :key="query.id" class="hover:bg-gray-50 dark:hover:bg-gray-800">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm font-medium text-gray-900 dark:text-white">
                {{ query.name }}
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span :class="['px-2 py-1 text-xs font-medium rounded-full', statusColors[query.status]]">
                {{ t(`groupQueries.status${query.status.charAt(0).toUpperCase() + query.status.slice(1)}`) }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
              {{ query.dueDate }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex items-center gap-2">
                <div class="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-primary-600 rounded-full"
                    :style="{ width: `${(query.responses / query.recipients) * 100}%` }"
                  />
                </div>
                <span class="text-sm text-gray-500 dark:text-gray-400">
                  {{ query.responses }}/{{ query.recipients }}
                </span>
              </div>
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
