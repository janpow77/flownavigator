<script setup lang="ts">
import { usePreferences } from '@/composables/usePreferences'
import { useAuthStore } from '@/stores/auth'

const { animationsEnabled, hoverEffectsEnabled } = usePreferences()
const authStore = useAuthStore()

interface Module {
  id: string
  name: string
  icon: string
  route: string
  stats?: { label: string; value: string | number; warning?: boolean }[]
  color: string
  locked?: boolean
}

const modules: Module[] = [
  {
    id: 'audits',
    name: 'Prüfungen',
    icon: 'clipboard',
    route: '/audit-cases',
    stats: [
      { label: 'aktiv', value: 12 },
      { label: 'fällig', value: 2, warning: true }
    ],
    color: 'blue'
  },
  {
    id: 'reports',
    name: 'Auswertungen',
    icon: 'chart',
    route: '/reports',
    stats: [{ label: 'neu', value: 3 }],
    color: 'purple'
  },
  {
    id: 'group',
    name: 'Konzern',
    icon: 'building',
    route: '/group-queries',
    stats: [{ label: 'offen', value: 2 }],
    color: 'cyan'
  },
  {
    id: 'checklists',
    name: 'Checklisten',
    icon: 'checklist',
    route: '/checklists',
    stats: [{ label: 'Vorlagen', value: 8 }],
    color: 'green'
  },
  {
    id: 'documents',
    name: 'Dokumente',
    icon: 'folder',
    route: '/documents',
    stats: [{ label: 'verwendet', value: '1.2 GB' }],
    color: 'orange'
  },
  {
    id: 'flowinvoice',
    name: 'FlowInvoice',
    icon: 'lock',
    route: '/flowinvoice',
    color: 'gray',
    locked: true
  }
]

const colorClasses: Record<string, { bg: string; icon: string }> = {
  blue: { bg: 'bg-blue-100 dark:bg-blue-900/30', icon: 'text-blue-600 dark:text-blue-400' },
  purple: { bg: 'bg-purple-100 dark:bg-purple-900/30', icon: 'text-purple-600 dark:text-purple-400' },
  cyan: { bg: 'bg-cyan-100 dark:bg-cyan-900/30', icon: 'text-cyan-600 dark:text-cyan-400' },
  green: { bg: 'bg-green-100 dark:bg-green-900/30', icon: 'text-green-600 dark:text-green-400' },
  orange: { bg: 'bg-orange-100 dark:bg-orange-900/30', icon: 'text-orange-600 dark:text-orange-400' },
  gray: { bg: 'bg-gray-100 dark:bg-gray-800', icon: 'text-gray-400' }
}

function formatDate(): string {
  return new Date().toLocaleDateString('de-DE', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })
}

function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Guten Morgen'
  if (hour < 18) return 'Guten Tag'
  return 'Guten Abend'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Welcome Header -->
    <div
      :class="[
        'card p-6',
        animationsEnabled ? 'animate-fade-in-up' : ''
      ]"
    >
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-semibold text-gray-900 dark:text-white">
            {{ getGreeting() }}, {{ authStore.user?.firstName }}
          </h1>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Was möchtest du heute erledigen?
          </p>
        </div>
        <span class="text-sm text-gray-400">{{ formatDate() }}</span>
      </div>
    </div>

    <!-- Module Grid -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <router-link
        v-for="(module, index) in modules"
        :key="module.id"
        :to="module.locked ? '#' : module.route"
        :class="[
          'card p-6 group',
          animationsEnabled ? 'stagger-item' : '',
          hoverEffectsEnabled && !module.locked ? 'hover-lift cursor-pointer' : '',
          module.locked ? 'opacity-60 cursor-not-allowed border-dashed' : ''
        ]"
        :style="animationsEnabled ? { animationDelay: `${index * 0.05}s` } : {}"
        @click.prevent="module.locked ? null : undefined"
      >
        <!-- Icon -->
        <div :class="['w-12 h-12 rounded-xl flex items-center justify-center mb-4', colorClasses[module.color].bg]">
          <!-- Clipboard Icon -->
          <svg v-if="module.icon === 'clipboard'" :class="['w-6 h-6', colorClasses[module.color].icon]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
          </svg>

          <!-- Chart Icon -->
          <svg v-else-if="module.icon === 'chart'" :class="['w-6 h-6', colorClasses[module.color].icon]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>

          <!-- Building Icon -->
          <svg v-else-if="module.icon === 'building'" :class="['w-6 h-6', colorClasses[module.color].icon]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>

          <!-- Checklist Icon -->
          <svg v-else-if="module.icon === 'checklist'" :class="['w-6 h-6', colorClasses[module.color].icon]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>

          <!-- Folder Icon -->
          <svg v-else-if="module.icon === 'folder'" :class="['w-6 h-6', colorClasses[module.color].icon]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>

          <!-- Lock Icon -->
          <svg v-else-if="module.icon === 'lock'" :class="['w-6 h-6', colorClasses[module.color].icon]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>

        <!-- Module Name -->
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">
          {{ module.name }}
        </h3>

        <!-- Stats -->
        <div v-if="module.stats" class="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
          <div class="flex items-center gap-3 text-sm">
            <span
              v-for="stat in module.stats"
              :key="stat.label"
              :class="[
                stat.warning ? 'text-amber-600 dark:text-amber-400' : 'text-gray-500 dark:text-gray-400'
              ]"
            >
              {{ stat.value }} {{ stat.label }}
              <span v-if="stat.warning" class="ml-0.5">⚠️</span>
            </span>
          </div>
        </div>

        <!-- Locked Badge -->
        <div v-if="module.locked" class="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
          <span class="text-xs text-gray-400">Lizenz erforderlich</span>
        </div>
      </router-link>
    </div>
  </div>
</template>
