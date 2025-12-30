<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const route = useRoute()
const { t } = useI18n()
const authStore = useAuthStore()

const navigation = computed(() => [
  {
    name: t('nav.dashboard'),
    to: { name: 'dashboard' },
    icon: 'dashboard',
  },
  {
    name: t('nav.groupQueries'),
    to: { name: 'group-queries' },
    icon: 'folder',
  },
  {
    name: t('nav.auditCases'),
    to: { name: 'audit-cases' },
    icon: 'document',
  },
  {
    name: t('nav.settings'),
    to: { name: 'settings' },
    icon: 'cog',
  },
])

function isActive(routeName: string): boolean {
  return route.name === routeName
}
</script>

<template>
  <!-- Mobile sidebar -->
  <aside
    :class="[
      'fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:z-auto',
      open ? 'translate-x-0' : '-translate-x-full'
    ]"
  >
    <div class="flex h-full flex-col">
      <!-- Logo -->
      <div class="flex h-16 items-center gap-3 px-6 border-b border-gray-200 dark:border-gray-700">
        <div class="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
          <svg class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <span class="text-lg font-semibold text-gray-900 dark:text-white">FlowAudit</span>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 space-y-1 px-3 py-4">
        <RouterLink
          v-for="item in navigation"
          :key="item.name"
          :to="item.to"
          :class="[
            'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
            isActive(item.to.name as string)
              ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/50 dark:text-primary-300'
              : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
          ]"
          @click="emit('close')"
        >
          <!-- Dashboard Icon -->
          <svg v-if="item.icon === 'dashboard'" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          <!-- Folder Icon -->
          <svg v-else-if="item.icon === 'folder'" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          <!-- Document Icon -->
          <svg v-else-if="item.icon === 'document'" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <!-- Cog Icon -->
          <svg v-else-if="item.icon === 'cog'" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>

          {{ item.name }}
        </RouterLink>
      </nav>

      <!-- User info -->
      <div class="border-t border-gray-200 dark:border-gray-700 p-4">
        <div class="flex items-center gap-3">
          <div class="h-9 w-9 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
            <span class="text-sm font-medium text-primary-700 dark:text-primary-300">
              {{ authStore.user?.firstName?.charAt(0) }}{{ authStore.user?.lastName?.charAt(0) }}
            </span>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
              {{ authStore.userName }}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400 truncate">
              {{ t(`roles.${authStore.user?.role}`) }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>
