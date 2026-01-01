<script setup lang="ts">
/**
 * License Gauge Component
 * Radial gauge showing license utilization
 */
import { computed } from 'vue'

interface Props {
  value: number
  max: number
  label: string
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
})

const percent = computed(() => {
  if (props.max === 0) return 0
  return Math.round((props.value / props.max) * 100)
})

const color = computed(() => {
  if (percent.value >= 100) return '#ef4444' // red
  if (percent.value >= 90) return '#f97316' // orange
  if (percent.value >= 80) return '#eab308' // yellow
  return '#22c55e' // green
})

const radius = computed(() => {
  switch (props.size) {
    case 'sm': return 30
    case 'lg': return 60
    default: return 45
  }
})

const strokeWidth = computed(() => {
  switch (props.size) {
    case 'sm': return 6
    case 'lg': return 10
    default: return 8
  }
})

const circumference = computed(() => 2 * Math.PI * radius.value)

const dashOffset = computed(() => {
  const clampedPercent = Math.min(percent.value, 100)
  return circumference.value - (clampedPercent / 100) * circumference.value
})

const svgSize = computed(() => (radius.value + strokeWidth.value) * 2)
</script>

<template>
  <div class="license-gauge" data-testid="license-gauge">
    <svg
      :width="svgSize"
      :height="svgSize"
      :viewBox="`0 0 ${svgSize} ${svgSize}`"
    >
      <!-- Background circle -->
      <circle
        :cx="svgSize / 2"
        :cy="svgSize / 2"
        :r="radius"
        fill="none"
        :stroke="color + '20'"
        :stroke-width="strokeWidth"
      />
      <!-- Progress circle -->
      <circle
        :cx="svgSize / 2"
        :cy="svgSize / 2"
        :r="radius"
        fill="none"
        :stroke="color"
        :stroke-width="strokeWidth"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="dashOffset"
        stroke-linecap="round"
        transform="rotate(-90)"
        :transform-origin="`${svgSize / 2} ${svgSize / 2}`"
        class="transition-all duration-500"
      />
    </svg>
    <div class="gauge-content">
      <span class="gauge-value" data-testid="gauge-value" :style="{ color }">
        {{ percent }}%
      </span>
      <span class="gauge-label">{{ label }}</span>
      <span class="gauge-detail">{{ value }} / {{ max }}</span>
    </div>
  </div>
</template>

<style scoped>
.license-gauge {
  @apply relative inline-flex flex-col items-center;
}

.gauge-content {
  @apply absolute inset-0 flex flex-col items-center justify-center;
}

.gauge-value {
  @apply text-xl font-bold;
}

.gauge-label {
  @apply text-xs text-gray-500;
}

.gauge-detail {
  @apply text-xs text-gray-400;
}
</style>
