<script setup lang="ts">
/**
 * Toast Notification Component
 * AC-5.2.4: Toast wird angezeigt und verschwindet
 */
import { computed } from 'vue'

interface Props {
  id: string
  type?: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
  dismissible?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'info',
  duration: 5000,
  dismissible: true,
})

const emit = defineEmits<{
  dismiss: [id: string]
}>()

const icons: Record<string, string> = {
  success: 'M5 13l4 4L19 7',
  error: 'M6 18L18 6M6 6l12 12',
  warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
  info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
}

const typeClasses = computed(() => ({
  'bg-green-50 border-green-200 dark:bg-green-900/30 dark:border-green-800': props.type === 'success',
  'bg-red-50 border-red-200 dark:bg-red-900/30 dark:border-red-800': props.type === 'error',
  'bg-yellow-50 border-yellow-200 dark:bg-yellow-900/30 dark:border-yellow-800': props.type === 'warning',
  'bg-blue-50 border-blue-200 dark:bg-blue-900/30 dark:border-blue-800': props.type === 'info',
}))

const iconClasses = computed(() => ({
  'text-green-500': props.type === 'success',
  'text-red-500': props.type === 'error',
  'text-yellow-500': props.type === 'warning',
  'text-blue-500': props.type === 'info',
}))
</script>

<template>
  <div
    class="toast"
    :class="typeClasses"
    role="alert"
    aria-live="assertive"
  >
    <div class="toast-icon" :class="iconClasses">
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="icons[type]" />
      </svg>
    </div>

    <div class="toast-content">
      <p class="toast-title">{{ title }}</p>
      <p v-if="message" class="toast-message">{{ message }}</p>
    </div>

    <button
      v-if="dismissible"
      class="toast-dismiss"
      @click="emit('dismiss', id)"
      aria-label="Schließen"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>

    <!-- Progress bar -->
    <div v-if="duration > 0" class="toast-progress">
      <div
        class="toast-progress-bar"
        :class="iconClasses"
        :style="{ animationDuration: `${duration}ms` }"
      />
    </div>
  </div>
</template>

<style scoped>
.toast {
  @apply relative flex items-start gap-3 p-4 rounded-lg border shadow-lg min-w-[320px] max-w-md;
  animation: toast-enter 0.3s ease-out;
}

@keyframes toast-enter {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.toast-icon {
  @apply flex-shrink-0;
}

.toast-content {
  @apply flex-1 min-w-0;
}

.toast-title {
  @apply font-medium text-gray-900 dark:text-white;
}

.toast-message {
  @apply mt-1 text-sm text-gray-600 dark:text-gray-300;
}

.toast-dismiss {
  @apply flex-shrink-0 p-1 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors;
}

.toast-progress {
  @apply absolute bottom-0 left-0 right-0 h-1 overflow-hidden rounded-b-lg;
}

.toast-progress-bar {
  @apply h-full opacity-50;
  animation: toast-progress linear forwards;
}

@keyframes toast-progress {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}
</style>
