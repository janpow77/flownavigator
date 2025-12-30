<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { usePreferences } from '@/composables/usePreferences'
import ViewSwitcher from '@/components/ViewSwitcher.vue'
import { TilesView, ListView, TreeView, RadialView, MinimalView } from '@/components/views'

const { t } = useI18n()
const { currentView, initialize } = usePreferences()

// Initialize preferences on mount
onMounted(() => {
  initialize()
})

// Map view type to component
const viewComponent = computed(() => {
  const views = {
    tiles: TilesView,
    list: ListView,
    tree: TreeView,
    radial: RadialView,
    minimal: MinimalView
  }
  return views[currentView.value] || TilesView
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header with ViewSwitcher -->
    <div v-if="currentView !== 'tree' && currentView !== 'minimal'" class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ t('dashboard.title') }}
        </h1>
      </div>
      <ViewSwitcher />
    </div>

    <!-- Floating ViewSwitcher for Tree/Minimal views -->
    <div
      v-if="currentView === 'tree' || currentView === 'minimal'"
      class="fixed top-4 right-4 z-50"
    >
      <ViewSwitcher />
    </div>

    <!-- Dynamic View Component -->
    <component :is="viewComponent" />
  </div>
</template>
