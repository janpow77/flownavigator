<script setup lang="ts">
/**
 * Module Card Component
 */
import type { Module } from '@/api/vendor'

interface Props {
  module: Module
  compact?: boolean
}

defineProps<Props>()

const statusColors: Record<string, string> = {
  development: 'bg-yellow-100 text-yellow-800',
  testing: 'bg-blue-100 text-blue-800',
  released: 'bg-green-100 text-green-800',
  deprecated: 'bg-gray-100 text-gray-800',
}

const statusLabels: Record<string, string> = {
  development: 'In Entwicklung',
  testing: 'Im Test',
  released: 'Released',
  deprecated: 'Veraltet',
}

const statusIcons: Record<string, string> = {
  development: 'M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z',
  testing: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
  released: 'M5 13l4 4L19 7',
  deprecated: 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
}
</script>

<template>
  <div class="module-card" :class="{ compact }">
    <div class="card-header">
      <div class="flex items-center gap-3">
        <div class="module-icon" :class="statusColors[module.status]">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="statusIcons[module.status]" />
          </svg>
        </div>
        <div>
          <h4 class="card-title">{{ module.name }}</h4>
          <p class="text-sm text-gray-500">v{{ module.version }}</p>
        </div>
      </div>
      <span class="status-badge" :class="statusColors[module.status]">
        {{ statusLabels[module.status] }}
      </span>
    </div>

    <div v-if="!compact && module.description" class="card-body">
      <p class="text-sm text-gray-600 dark:text-gray-300 line-clamp-2">
        {{ module.description }}
      </p>
    </div>

    <div v-if="!compact" class="card-footer">
      <div class="flex items-center gap-4 text-sm text-gray-500">
        <span v-if="module.released_at">
          Released: {{ new Date(module.released_at).toLocaleDateString('de-DE') }}
        </span>
        <span v-if="module.dependencies?.length">
          {{ module.dependencies.length }} Abhängigkeiten
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.module-card {
  @apply bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow cursor-pointer;
}

.module-card.compact {
  @apply p-3;
}

.card-header {
  @apply flex justify-between items-start;
}

.module-icon {
  @apply w-10 h-10 rounded-lg flex items-center justify-center;
}

.card-title {
  @apply font-semibold text-gray-900 dark:text-white;
}

.status-badge {
  @apply px-2 py-1 text-xs font-medium rounded-full;
}

.card-body {
  @apply mt-3;
}

.card-footer {
  @apply mt-3 pt-3 border-t border-gray-100 dark:border-gray-700;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
