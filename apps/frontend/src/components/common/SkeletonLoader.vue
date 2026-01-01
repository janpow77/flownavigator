<script setup lang="ts">
/**
 * Skeleton Loader Component
 * AC-5.1.1 - AC-5.1.4: Shimmer loading states
 */
import { ref, onMounted, onUnmounted } from 'vue'

interface Props {
  type?: 'text' | 'avatar' | 'card' | 'button' | 'image'
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  variant?: 'shimmer' | 'pulse' | 'wave'
  count?: number
  width?: string
  height?: string
  rounded?: boolean | 'sm' | 'md' | 'lg' | 'full'
  delay?: number
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  size: 'md',
  variant: 'shimmer',
  count: 1,
  rounded: false,
  delay: 200,
})

const show = ref(false)
let timeout: ReturnType<typeof setTimeout>

onMounted(() => {
  // Delayed skeleton to prevent flash for fast loads
  if (props.delay > 0) {
    timeout = setTimeout(() => {
      show.value = true
    }, props.delay)
  } else {
    show.value = true
  }
})

onUnmounted(() => {
  if (timeout) clearTimeout(timeout)
})

const sizeClasses: Record<string, Record<string, string>> = {
  text: {
    xs: 'h-2 w-16',
    sm: 'h-3 w-24',
    md: 'h-4 w-32',
    lg: 'h-5 w-48',
    xl: 'h-6 w-64',
  },
  avatar: {
    xs: 'h-6 w-6',
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
  },
  card: {
    xs: 'h-20 w-full',
    sm: 'h-32 w-full',
    md: 'h-48 w-full',
    lg: 'h-64 w-full',
    xl: 'h-80 w-full',
  },
  button: {
    xs: 'h-6 w-16',
    sm: 'h-8 w-20',
    md: 'h-10 w-24',
    lg: 'h-12 w-32',
    xl: 'h-14 w-40',
  },
  image: {
    xs: 'h-16 w-16',
    sm: 'h-24 w-24',
    md: 'h-32 w-32',
    lg: 'h-48 w-48',
    xl: 'h-64 w-64',
  },
}

const roundedClasses: Record<string, string> = {
  true: 'rounded',
  sm: 'rounded-sm',
  md: 'rounded-md',
  lg: 'rounded-lg',
  full: 'rounded-full',
}
</script>

<template>
  <div v-if="show" class="skeleton-container">
    <div
      v-for="i in count"
      :key="i"
      class="skeleton"
      :class="[
        sizeClasses[type]?.[size] || sizeClasses.text.md,
        variant,
        rounded ? roundedClasses[String(rounded)] : '',
        type === 'avatar' ? 'rounded-full' : '',
      ]"
      :style="{
        width: width || undefined,
        height: height || undefined,
      }"
    />
  </div>
</template>

<style scoped>
.skeleton-container {
  @apply flex flex-col gap-2;
}

.skeleton {
  @apply bg-gray-200 dark:bg-gray-700;
}

/* Shimmer animation */
.skeleton.shimmer {
  background: linear-gradient(
    90deg,
    rgb(229 231 235) 0%,
    rgb(243 244 246) 50%,
    rgb(229 231 235) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* Pulse animation */
.skeleton.pulse {
  animation: pulse-subtle 2s ease-in-out infinite;
}

@keyframes pulse-subtle {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* Wave animation */
.skeleton.wave {
  position: relative;
  overflow: hidden;
}

.skeleton.wave::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent
  );
  animation: skeleton-wave 1.5s infinite;
}

@keyframes skeleton-wave {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

/* Dark mode */
.dark .skeleton.shimmer {
  background: linear-gradient(
    90deg,
    rgb(55 65 81) 0%,
    rgb(75 85 99) 50%,
    rgb(55 65 81) 100%
  );
  background-size: 200% 100%;
}

/* Accessibility: Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .skeleton.shimmer,
  .skeleton.pulse,
  .skeleton.wave,
  .skeleton.wave::after {
    animation: none;
  }
}
</style>
