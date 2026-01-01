<script setup lang="ts">
/**
 * Skeleton Table Component
 * Pre-built skeleton for table loading states
 */
import SkeletonLoader from './SkeletonLoader.vue'

interface Props {
  rows?: number
  columns?: number
  hasHeader?: boolean
  hasActions?: boolean
}

withDefaults(defineProps<Props>(), {
  rows: 5,
  columns: 4,
  hasHeader: true,
  hasActions: true,
})
</script>

<template>
  <div class="skeleton-table">
    <!-- Header -->
    <div v-if="hasHeader" class="table-header">
      <div
        v-for="col in columns"
        :key="`header-${col}`"
        class="header-cell"
      >
        <SkeletonLoader type="text" size="sm" :delay="0" />
      </div>
      <div v-if="hasActions" class="header-cell actions" />
    </div>

    <!-- Rows -->
    <div
      v-for="row in rows"
      :key="`row-${row}`"
      class="table-row"
    >
      <div
        v-for="col in columns"
        :key="`cell-${row}-${col}`"
        class="table-cell"
      >
        <SkeletonLoader
          :type="col === 1 ? 'avatar' : 'text'"
          :size="col === 1 ? 'sm' : 'md'"
          :delay="0"
        />
      </div>
      <div v-if="hasActions" class="table-cell actions">
        <SkeletonLoader type="button" size="sm" :delay="0" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.skeleton-table {
  @apply bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden;
}

.table-header {
  @apply flex gap-4 p-4 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700;
}

.header-cell {
  @apply flex-1;
}

.header-cell.actions {
  @apply w-24 flex-none;
}

.table-row {
  @apply flex gap-4 p-4 border-b border-gray-100 dark:border-gray-700 last:border-b-0;
}

.table-cell {
  @apply flex-1 flex items-center;
}

.table-cell.actions {
  @apply w-24 flex-none justify-end;
}
</style>
