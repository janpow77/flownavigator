<script setup lang="ts">
import { ref } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import TheSidebar from '@/components/TheSidebar.vue'
import TheHeader from '@/components/TheHeader.vue'

const router = useRouter()
const authStore = useAuthStore()

const sidebarOpen = ref(false)

async function handleLogout() {
  await authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Mobile sidebar overlay -->
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 z-40 bg-gray-900/50 lg:hidden"
      @click="sidebarOpen = false"
    />

    <!-- Sidebar -->
    <TheSidebar
      :open="sidebarOpen"
      @close="sidebarOpen = false"
    />

    <!-- Main content -->
    <div class="lg:pl-64">
      <TheHeader
        @toggle-sidebar="sidebarOpen = !sidebarOpen"
        @logout="handleLogout"
      />

      <main class="py-6">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>
