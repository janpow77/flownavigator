<script setup lang="ts">
import { usePreferences } from '@/composables/usePreferences'
import type { ViewType } from '@/types/preferences'
import { viewTypes } from '@/types/preferences'

const { currentView, setView } = usePreferences()

const views: { type: ViewType; icon: string }[] = [
  { type: 'tiles', icon: 'grid' },
  { type: 'list', icon: 'list' },
  { type: 'tree', icon: 'sidebar' },
  { type: 'radial', icon: 'circle' },
  { type: 'minimal', icon: 'minimal' }
]

function selectView(view: ViewType): void {
  setView(view)
}
</script>

<template>
  <div class="flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
    <button
      v-for="view in views"
      :key="view.type"
      :title="viewTypes[view.type].name"
      :class="[
        'p-2 rounded-md transition-all duration-200',
        currentView === view.type
          ? 'bg-white dark:bg-gray-700 shadow-sm text-accent-600'
          : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
      ]"
      @click="selectView(view.type)"
    >
      <!-- Grid Icon -->
      <svg v-if="view.icon === 'grid'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
      </svg>

      <!-- List Icon -->
      <svg v-else-if="view.icon === 'list'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>

      <!-- Sidebar Icon -->
      <svg v-else-if="view.icon === 'sidebar'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h6M4 12h6m-6 6h6m4-12h6m-6 6h6m-6 6h6" />
      </svg>

      <!-- Circle/Radial Icon -->
      <svg v-else-if="view.icon === 'circle'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <circle cx="12" cy="12" r="3" stroke-width="2" />
        <circle cx="12" cy="12" r="8" stroke-width="2" stroke-dasharray="4 2" />
      </svg>

      <!-- Minimal Icon -->
      <svg v-else-if="view.icon === 'minimal'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14" />
      </svg>
    </button>
  </div>
</template>
