<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// Check for existing session on app load
authStore.checkAuth()
</script>

<template>
  <RouterView />
</template>
