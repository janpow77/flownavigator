<script setup lang="ts">
/**
 * Skeleton Card Component
 * Pre-built skeleton for card loading states
 */
import SkeletonLoader from './SkeletonLoader.vue'

interface Props {
  hasImage?: boolean
  hasAvatar?: boolean
  lines?: number
  hasActions?: boolean
}

withDefaults(defineProps<Props>(), {
  hasImage: false,
  hasAvatar: true,
  lines: 3,
  hasActions: true,
})
</script>

<template>
  <div class="skeleton-card">
    <!-- Image -->
    <div v-if="hasImage" class="card-image">
      <SkeletonLoader type="image" size="xl" width="100%" height="160px" :delay="0" />
    </div>

    <div class="card-content">
      <!-- Header with avatar -->
      <div v-if="hasAvatar" class="card-header">
        <SkeletonLoader type="avatar" size="md" :delay="0" />
        <div class="header-text">
          <SkeletonLoader type="text" size="md" width="60%" :delay="0" />
          <SkeletonLoader type="text" size="sm" width="40%" :delay="0" />
        </div>
      </div>

      <!-- Content lines -->
      <div class="card-body">
        <SkeletonLoader
          v-for="line in lines"
          :key="line"
          type="text"
          size="sm"
          :width="line === lines ? '80%' : '100%'"
          :delay="0"
        />
      </div>

      <!-- Actions -->
      <div v-if="hasActions" class="card-actions">
        <SkeletonLoader type="button" size="sm" :delay="0" />
        <SkeletonLoader type="button" size="sm" :delay="0" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.skeleton-card {
  @apply bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden;
}

.card-image {
  @apply w-full;
}

.card-content {
  @apply p-4;
}

.card-header {
  @apply flex items-center gap-3 mb-4;
}

.header-text {
  @apply flex-1 flex flex-col gap-1;
}

.card-body {
  @apply flex flex-col gap-2 mb-4;
}

.card-actions {
  @apply flex gap-2 pt-4 border-t border-gray-100 dark:border-gray-700;
}
</style>
