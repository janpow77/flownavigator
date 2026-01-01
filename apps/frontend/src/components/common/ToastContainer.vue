<script setup lang="ts">
/**
 * Toast Container Component
 * Manages and displays toast notifications
 */
import { ref, onMounted, onUnmounted } from 'vue'
import Toast from './Toast.vue'

interface ToastItem {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
}

const toasts = ref<ToastItem[]>([])

function addToast(toast: Omit<ToastItem, 'id'>) {
  const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`
  const newToast = { id, ...toast }

  toasts.value.push(newToast)

  // Auto-remove after duration
  const duration = toast.duration ?? 5000
  if (duration > 0) {
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }
}

function removeToast(id: string) {
  const index = toasts.value.findIndex((t) => t.id === id)
  if (index !== -1) {
    toasts.value.splice(index, 1)
  }
}

// Expose methods globally via custom event
function handleToastEvent(event: CustomEvent<Omit<ToastItem, 'id'>>) {
  addToast(event.detail)
}

onMounted(() => {
  window.addEventListener('toast', handleToastEvent as EventListener)
})

onUnmounted(() => {
  window.removeEventListener('toast', handleToastEvent as EventListener)
})

// Expose for direct usage
defineExpose({ addToast, removeToast })
</script>

<template>
  <Teleport to="body">
    <div class="toast-container" aria-live="polite">
      <TransitionGroup name="toast">
        <Toast
          v-for="toast in toasts"
          :key="toast.id"
          :id="toast.id"
          :type="toast.type"
          :title="toast.title"
          :message="toast.message"
          :duration="toast.duration"
          @dismiss="removeToast"
        />
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-container {
  @apply fixed top-4 right-4 z-50 flex flex-col gap-3;
}

.toast-enter-active {
  transition: all 0.3s ease-out;
}

.toast-leave-active {
  transition: all 0.2s ease-in;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.toast-move {
  transition: transform 0.3s ease;
}
</style>
