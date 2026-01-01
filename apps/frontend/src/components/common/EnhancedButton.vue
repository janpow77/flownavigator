<script setup lang="ts">
/**
 * Enhanced Button with Ripple Effect and States
 * AC-5.2.1: Ripple-Effekt bei Button-Klick
 * AC-5.2.2: Button zeigt Success-State
 * AC-5.2.3: Button zeigt Error-State mit Shake
 */
import { ref, computed } from 'vue'

interface Props {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  loading?: boolean
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
  state?: 'idle' | 'loading' | 'success' | 'error'
  fullWidth?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  loading: false,
  disabled: false,
  type: 'button',
  state: 'idle',
  fullWidth: false,
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const buttonRef = ref<HTMLButtonElement>()
const ripples = ref<Array<{ id: number; x: number; y: number; size: number }>>([])
let rippleId = 0

const isDisabled = computed(() => props.disabled || props.loading || props.state === 'loading')

const currentState = computed(() => {
  if (props.loading) return 'loading'
  return props.state
})

function handleClick(event: MouseEvent) {
  if (isDisabled.value) return

  // Create ripple
  createRipple(event)

  emit('click', event)
}

function createRipple(event: MouseEvent) {
  const button = buttonRef.value
  if (!button) return

  const rect = button.getBoundingClientRect()
  const size = Math.max(rect.width, rect.height) * 2

  const ripple = {
    id: rippleId++,
    x: event.clientX - rect.left - size / 2,
    y: event.clientY - rect.top - size / 2,
    size,
  }

  ripples.value.push(ripple)

  setTimeout(() => {
    ripples.value = ripples.value.filter((r) => r.id !== ripple.id)
  }, 600)
}

const sizeClasses: Record<string, string> = {
  xs: 'px-2 py-1 text-xs',
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-base',
  xl: 'px-6 py-3 text-lg',
}

const variantClasses: Record<string, string> = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
  secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-500 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600',
  outline: 'bg-transparent border-2 border-blue-600 text-blue-600 hover:bg-blue-50 focus:ring-blue-500 dark:hover:bg-blue-900/20',
  ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-500 dark:text-gray-300 dark:hover:bg-gray-800',
  danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
}

const stateClasses = computed(() => ({
  'animate-shake bg-red-600': currentState.value === 'error' && props.variant !== 'danger',
  'bg-green-600': currentState.value === 'success',
}))
</script>

<template>
  <button
    ref="buttonRef"
    :type="type"
    :disabled="isDisabled"
    class="enhanced-button"
    :class="[
      sizeClasses[size],
      variantClasses[variant],
      stateClasses,
      { 'w-full': fullWidth, 'opacity-50 cursor-not-allowed': isDisabled },
    ]"
    @click="handleClick"
  >
    <!-- Ripple container -->
    <span class="ripple-container">
      <span
        v-for="ripple in ripples"
        :key="ripple.id"
        class="ripple"
        :style="{
          left: `${ripple.x}px`,
          top: `${ripple.y}px`,
          width: `${ripple.size}px`,
          height: `${ripple.size}px`,
        }"
      />
    </span>

    <!-- Loading spinner -->
    <svg
      v-if="currentState === 'loading'"
      class="spinner"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        class="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="4"
      />
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>

    <!-- Success icon -->
    <svg
      v-else-if="currentState === 'success'"
      class="state-icon"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
    </svg>

    <!-- Error icon -->
    <svg
      v-else-if="currentState === 'error'"
      class="state-icon"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
    </svg>

    <!-- Content -->
    <span
      :class="{ 'opacity-0': currentState !== 'idle' }"
      class="button-content"
    >
      <slot />
    </span>
  </button>
</template>

<style scoped>
.enhanced-button {
  @apply relative overflow-hidden rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 inline-flex items-center justify-center;
}

.ripple-container {
  @apply absolute inset-0 overflow-hidden pointer-events-none;
}

.ripple {
  @apply absolute rounded-full bg-white/30 animate-ripple pointer-events-none;
}

@keyframes ripple {
  from {
    transform: scale(0);
    opacity: 1;
  }
  to {
    transform: scale(1);
    opacity: 0;
  }
}

.animate-ripple {
  animation: ripple 0.6s ease-out forwards;
}

.spinner {
  @apply absolute w-5 h-5 animate-spin;
}

.state-icon {
  @apply absolute w-5 h-5;
  animation: icon-pop 0.3s ease-out;
}

@keyframes icon-pop {
  0% {
    transform: scale(0);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}

.button-content {
  @apply transition-opacity duration-200;
}

@keyframes shake {
  0%, 100% {
    transform: translateX(0);
  }
  10%, 30%, 50%, 70%, 90% {
    transform: translateX(-4px);
  }
  20%, 40%, 60%, 80% {
    transform: translateX(4px);
  }
}

.animate-shake {
  animation: shake 0.5s ease-in-out;
}
</style>
