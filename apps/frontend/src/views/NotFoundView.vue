<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

const { t } = useI18n()
const router = useRouter()
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
    <div class="max-w-md w-full text-center">
      <div class="mb-8">
        <span class="text-9xl font-bold text-gray-200 dark:text-gray-700">404</span>
      </div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
        {{ t('errors.pageNotFound') }}
      </h1>
      <p class="text-gray-500 dark:text-gray-400 mb-8">
        {{ t('errors.pageNotFoundDescription') }}
      </p>
      <div class="flex flex-col sm:flex-row gap-3 justify-center">
        <button
          class="btn-primary"
          @click="router.push({ name: 'dashboard' })"
        >
          {{ t('errors.backToDashboard') }}
        </button>
        <button
          class="btn-secondary"
          @click="router.back()"
        >
          {{ t('errors.goBack') }}
        </button>
      </div>
    </div>
  </div>
</template>
