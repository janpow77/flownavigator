<script setup lang="ts">
import { ref } from 'vue'
import { usePreferences } from '@/composables/usePreferences'

const { animationsEnabled } = usePreferences()

const searchQuery = ref('')

interface Module {
  id: string
  name: string
  icon: string
  route: string
  description: string
  locked?: boolean
}

const modules: Module[] = [
  { id: 'audits', name: 'Prüfungen', icon: 'clipboard', route: '/audit-cases', description: '12 aktiv • 2 fällig' },
  { id: 'reports', name: 'Auswertungen', icon: 'chart', route: '/reports', description: '3 neue Berichte' },
  { id: 'group', name: 'Konzern', icon: 'building', route: '/group-queries', description: '2 Abfragen offen' },
  { id: 'checklists', name: 'Checklisten', icon: 'checklist', route: '/checklists', description: '8 Vorlagen' },
  { id: 'documents', name: 'Dokumente', icon: 'folder', route: '/documents', description: '1.2 GB verwendet' },
  { id: 'sampling', name: 'Stichproben', icon: 'random', route: '/sampling', description: 'MUS, Random, Stratified' },
  { id: 'jkb', name: 'Berichte', icon: 'file', route: '/jkb', description: 'JKB 2024 in Arbeit' },
  { id: 'admin', name: 'Administration', icon: 'cog', route: '/admin', description: 'Nur Administratoren' },
  { id: 'flowinvoice', name: 'FlowInvoice', icon: 'lock', route: '/flowinvoice', description: 'KI-Belegprüfung • Lizenz erforderlich', locked: true }
]

const filteredModules = ref(modules)

function filterModules(): void {
  if (!searchQuery.value) {
    filteredModules.value = modules
    return
  }
  const query = searchQuery.value.toLowerCase()
  filteredModules.value = modules.filter(m =>
    m.name.toLowerCase().includes(query) ||
    m.description.toLowerCase().includes(query)
  )
}
</script>

<template>
  <div class="space-y-4">
    <!-- Search Bar -->
    <div class="flex items-center gap-4">
      <h1 class="text-lg font-medium text-gray-900 dark:text-white">Module</h1>
      <div class="flex-1 max-w-md">
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            class="input pl-10"
            placeholder="Schnellsuche..."
            @input="filterModules"
          />
        </div>
      </div>
    </div>

    <!-- Module List -->
    <div
      :class="[
        'card overflow-hidden divide-y divide-gray-200 dark:divide-gray-700',
        animationsEnabled ? 'animate-fade-in' : ''
      ]"
    >
      <router-link
        v-for="(module, index) in filteredModules"
        :key="module.id"
        :to="module.locked ? '#' : module.route"
        :class="[
          'flex items-center gap-4 px-4 py-3 transition-colors',
          module.locked
            ? 'opacity-60 cursor-not-allowed border-l-2 border-dashed border-gray-300 dark:border-gray-600'
            : 'hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer',
          animationsEnabled ? 'stagger-item' : ''
        ]"
        :style="animationsEnabled ? { animationDelay: `${index * 0.03}s` } : {}"
        @click.prevent="module.locked ? null : undefined"
      >
        <!-- Icon -->
        <div class="flex-shrink-0 w-8 h-8 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
          <svg v-if="module.icon === 'clipboard'" class="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <svg v-else-if="module.icon === 'chart'" class="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <svg v-else-if="module.icon === 'building'" class="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          <svg v-else-if="module.icon === 'checklist'" class="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
          <svg v-else-if="module.icon === 'folder'" class="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          <svg v-else-if="module.icon === 'random'" class="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <svg v-else-if="module.icon === 'file'" class="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <svg v-else-if="module.icon === 'cog'" class="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <svg v-else-if="module.icon === 'lock'" class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-gray-900 dark:text-white">{{ module.name }}</p>
          <p class="text-sm text-gray-500 dark:text-gray-400 truncate">{{ module.description }}</p>
        </div>

        <!-- Arrow -->
        <svg class="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </router-link>
    </div>

    <!-- Keyboard Hint -->
    <p class="text-xs text-gray-400 text-center">
      Tipp: Nutze <kbd class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs">/</kbd> für die Schnellsuche
    </p>
  </div>
</template>
