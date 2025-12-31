<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { usePreferences } from '@/composables/usePreferences'
import { useAuthStore } from '@/stores/auth'

const { animationsEnabled, hoverEffectsEnabled } = usePreferences()
const authStore = useAuthStore()

// LocalStorage keys
const STORAGE_KEY_ZOOM = 'radialView.zoom'
const STORAGE_KEY_COLOR = 'radialView.color'

// Color customization
interface ColorPreset {
  name: string
  primary: string
  glow: string
  light: string
  dark: string
}

const colorPresets: ColorPreset[] = [
  { name: 'Lila', primary: '#8b5cf6', glow: 'rgba(139, 92, 246, 0.4)', light: 'rgba(139, 92, 246, 0.1)', dark: 'rgba(139, 92, 246, 0.9)' },
  { name: 'Blau', primary: '#3b82f6', glow: 'rgba(59, 130, 246, 0.4)', light: 'rgba(59, 130, 246, 0.1)', dark: 'rgba(59, 130, 246, 0.9)' },
  { name: 'Cyan', primary: '#06b6d4', glow: 'rgba(6, 182, 212, 0.4)', light: 'rgba(6, 182, 212, 0.1)', dark: 'rgba(6, 182, 212, 0.9)' },
  { name: 'Grün', primary: '#10b981', glow: 'rgba(16, 185, 129, 0.4)', light: 'rgba(16, 185, 129, 0.1)', dark: 'rgba(16, 185, 129, 0.9)' },
  { name: 'Orange', primary: '#f97316', glow: 'rgba(249, 115, 22, 0.4)', light: 'rgba(249, 115, 22, 0.1)', dark: 'rgba(249, 115, 22, 0.9)' },
  { name: 'Pink', primary: '#ec4899', glow: 'rgba(236, 72, 153, 0.4)', light: 'rgba(236, 72, 153, 0.1)', dark: 'rgba(236, 72, 153, 0.9)' },
  { name: 'Rot', primary: '#ef4444', glow: 'rgba(239, 68, 68, 0.4)', light: 'rgba(239, 68, 68, 0.1)', dark: 'rgba(239, 68, 68, 0.9)' },
]

// Load saved settings from localStorage
function loadSavedZoom(): number {
  const saved = localStorage.getItem(STORAGE_KEY_ZOOM)
  if (saved) {
    const value = parseFloat(saved)
    if (!isNaN(value) && value >= 0.5 && value <= 1.5) {
      return value
    }
  }
  return 1
}

function loadSavedColor(): ColorPreset {
  const saved = localStorage.getItem(STORAGE_KEY_COLOR)
  if (saved) {
    const found = colorPresets.find(c => c.name === saved)
    if (found) return found
  }
  return colorPresets[0]
}

// Zoom controls
const zoom = ref(loadSavedZoom())
const minZoom = 0.5
const maxZoom = 1.5
const zoomStep = 0.1
const containerRef = ref<HTMLElement | null>(null)

function handleWheel(event: WheelEvent): void {
  event.preventDefault()
  const delta = event.deltaY > 0 ? -zoomStep : zoomStep
  const newZoom = Math.max(minZoom, Math.min(maxZoom, zoom.value + delta))
  zoom.value = newZoom
  localStorage.setItem(STORAGE_KEY_ZOOM, newZoom.toString())
}

function resetZoom(): void {
  zoom.value = 1
  localStorage.setItem(STORAGE_KEY_ZOOM, '1')
}

// Watch for slider changes
watch(zoom, (newValue) => {
  localStorage.setItem(STORAGE_KEY_ZOOM, newValue.toString())
})

const zoomPercent = computed(() => Math.round(zoom.value * 100))

// Color state
const selectedColor = ref<ColorPreset>(loadSavedColor())
const showColorPicker = ref(false)

function selectColor(color: ColorPreset): void {
  selectedColor.value = color
  showColorPicker.value = false
  localStorage.setItem(STORAGE_KEY_COLOR, color.name)
}

interface Module {
  id: string
  name: string
  icon: string
  route: string
  stats?: string
  color: string
  locked?: boolean
  version?: string
  status?: 'active' | 'beta' | 'new' | 'locked'
}

const modules: Module[] = [
  { id: 'audits', name: 'Prüfungen', icon: 'clipboard', route: '/audit-cases', stats: '12 aktiv, 2 fällig', color: 'blue', version: 'v2.1', status: 'active' },
  { id: 'reports', name: 'Auswertungen', icon: 'chart', route: '/reports', stats: '3 neue', color: 'purple', version: 'v1.8', status: 'active' },
  { id: 'group', name: 'Konzern', icon: 'building', route: '/group-queries', stats: '2 offen', color: 'cyan', version: 'v1.2', status: 'beta' },
  { id: 'documents', name: 'Dokumente', icon: 'folder', route: '/documents', stats: '1.2 GB', color: 'orange', version: 'v2.0', status: 'active' },
  { id: 'sampling', name: 'Stichproben', icon: 'random', route: '/sampling', stats: 'MUS, Random', color: 'green', version: 'v1.5', status: 'active' },
  { id: 'checklists', name: 'Checklisten', icon: 'checklist', route: '/checklists', stats: '8 Vorlagen', color: 'pink', version: 'v1.0', status: 'new' },
  { id: 'jkb', name: 'Berichte', icon: 'file', route: '/jkb', stats: 'JKB 2024', color: 'teal', version: 'v3.0', status: 'active' },
  { id: 'admin', name: 'Admin', icon: 'cog', route: '/admin', color: 'gray', version: 'v2.2', status: 'active' }
]

const hoveredModule = ref<string | null>(null)
const mousePosition = ref({ x: 0, y: 0 })
const centerElement = ref<HTMLElement | null>(null)

const colorClasses: Record<string, string> = {
  blue: 'bg-blue-500',
  purple: 'bg-purple-500',
  cyan: 'bg-cyan-500',
  orange: 'bg-orange-500',
  green: 'bg-green-500',
  pink: 'bg-pink-500',
  teal: 'bg-teal-500',
  gray: 'bg-gray-500'
}

const hoverColorClasses: Record<string, string> = {
  blue: 'shadow-blue-500/50',
  purple: 'shadow-purple-500/50',
  cyan: 'shadow-cyan-500/50',
  orange: 'shadow-orange-500/50',
  green: 'shadow-green-500/50',
  pink: 'shadow-pink-500/50',
  teal: 'shadow-teal-500/50',
  gray: 'shadow-gray-500/50'
}

const statusLabels: Record<string, { label: string; class: string }> = {
  active: { label: 'Aktiv', class: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
  beta: { label: 'Beta', class: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' },
  new: { label: 'Neu', class: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  locked: { label: 'Gesperrt', class: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400' }
}

// Orbit ring radii
const orbitRings = [120, 220, 320]

// Calculate position for each module in a circle
function getModulePosition(index: number, total: number): { x: number; y: number; angle: number } {
  const angle = (index / total) * 2 * Math.PI - Math.PI / 2 // Start from top
  const radius = 250 // Increased distance from center for larger view
  return {
    x: Math.cos(angle) * radius,
    y: Math.sin(angle) * radius,
    angle: angle * (180 / Math.PI)
  }
}

// Get hovered module data
const hoveredModuleData = computed(() => {
  return modules.find(m => m.id === hoveredModule.value)
})

// Parallax effect
function handleMouseMove(event: MouseEvent): void {
  if (!centerElement.value) return
  const rect = centerElement.value.getBoundingClientRect()
  const centerX = rect.left + rect.width / 2
  const centerY = rect.top + rect.height / 2
  mousePosition.value = {
    x: (event.clientX - centerX) * 0.02,
    y: (event.clientY - centerY) * 0.02
  }
}

onMounted(() => {
  if (animationsEnabled.value) {
    window.addEventListener('mousemove', handleMouseMove)
  }
})

onUnmounted(() => {
  window.removeEventListener('mousemove', handleMouseMove)
})
</script>

<template>
  <div
    ref="containerRef"
    class="flex items-center justify-center min-h-[800px] relative"
    @wheel.prevent="handleWheel"
  >
    <!-- Controls Bar -->
    <div class="absolute top-4 right-4 z-40 flex items-center gap-4 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-lg px-4 py-2 shadow-lg border border-gray-200 dark:border-gray-700">
      <!-- Color Picker -->
      <div class="relative">
        <button
          class="flex items-center gap-2 px-2 py-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          @click="showColorPicker = !showColorPicker"
        >
          <span
            class="w-5 h-5 rounded-full border-2 border-white shadow-sm"
            :style="{ backgroundColor: selectedColor.primary }"
          />
          <span class="text-xs font-medium text-gray-600 dark:text-gray-400">{{ selectedColor.name }}</span>
          <svg class="w-3 h-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <!-- Color Dropdown -->
        <Transition name="dropdown">
          <div
            v-if="showColorPicker"
            class="absolute top-full right-0 mt-2 p-3 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 min-w-[180px]"
          >
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Akzentfarbe</p>
            <div class="grid grid-cols-4 gap-2">
              <button
                v-for="color in colorPresets"
                :key="color.name"
                class="group relative w-8 h-8 rounded-full transition-transform hover:scale-110"
                :style="{ backgroundColor: color.primary }"
                :title="color.name"
                @click="selectColor(color)"
              >
                <span
                  v-if="selectedColor.name === color.name"
                  class="absolute inset-0 flex items-center justify-center"
                >
                  <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                  </svg>
                </span>
              </button>
            </div>
          </div>
        </Transition>
      </div>

      <div class="w-px h-6 bg-gray-200 dark:bg-gray-700" />

      <!-- Zoom Controls -->
      <button
        class="w-7 h-7 flex items-center justify-center rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors"
        :disabled="zoom <= minZoom"
        :class="{ 'opacity-40 cursor-not-allowed': zoom <= minZoom }"
        @click="zoom = Math.max(minZoom, zoom - zoomStep)"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" />
        </svg>
      </button>

      <input
        v-model.number="zoom"
        type="range"
        :min="minZoom"
        :max="maxZoom"
        :step="zoomStep"
        class="w-24 h-1.5 bg-gray-200 dark:bg-gray-600 rounded-lg appearance-none cursor-pointer accent-accent-600"
      />

      <button
        class="w-7 h-7 flex items-center justify-center rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors"
        :disabled="zoom >= maxZoom"
        :class="{ 'opacity-40 cursor-not-allowed': zoom >= maxZoom }"
        @click="zoom = Math.min(maxZoom, zoom + zoomStep)"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
      </button>

      <span class="text-xs font-medium text-gray-600 dark:text-gray-400 w-10 text-center">
        {{ zoomPercent }}%
      </span>

      <button
        v-if="zoom !== 1"
        class="ml-1 px-2 py-1 text-xs font-medium text-accent-600 hover:text-accent-700 dark:text-accent-400 dark:hover:text-accent-300 transition-colors"
        @click="resetZoom"
      >
        Reset
      </button>
    </div>

    <!-- Radial Container -->
    <div
      ref="centerElement"
      class="relative w-[700px] h-[700px] transition-transform duration-150"
      :style="{
        transform: `scale(${zoom}) translate(${animationsEnabled ? mousePosition.x : 0}px, ${animationsEnabled ? mousePosition.y : 0}px)`
      }"
    >
      <!-- Orbit Rings (Dashed Circles) -->
      <svg class="absolute inset-0 w-full h-full pointer-events-none">
        <circle
          v-for="radius in orbitRings"
          :key="`orbit-${radius}`"
          cx="50%"
          cy="50%"
          :r="radius"
          fill="none"
          class="stroke-gray-200 dark:stroke-gray-700/50"
          stroke-dasharray="8 8"
          stroke-width="1"
        />
      </svg>

      <!-- Connection Lines -->
      <svg class="absolute inset-0 w-full h-full pointer-events-none">
        <defs>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        <line
          v-for="(module, index) in modules"
          :key="`line-${module.id}`"
          x1="50%"
          y1="50%"
          :x2="`${50 + getModulePosition(index, modules.length).x / 7}%`"
          :y2="`${50 + getModulePosition(index, modules.length).y / 7}%`"
          class="transition-all duration-300"
          :style="{
            stroke: hoveredModule === module.id ? selectedColor.primary : '',
            strokeWidth: hoveredModule === module.id ? 3 : 1
          }"
          :class="hoveredModule !== module.id ? 'stroke-gray-200 dark:stroke-gray-700' : ''"
          :filter="hoveredModule === module.id ? 'url(#glow)' : ''"
        />
      </svg>

      <!-- Center User Circle with Glow Effect -->
      <div class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
        <!-- Pulse Animation Ring -->
        <div
          v-if="animationsEnabled"
          class="absolute inset-0 -m-4 rounded-full animate-pulse-ring"
          :style="{ backgroundColor: selectedColor.light }"
        />
        <div
          v-if="animationsEnabled"
          class="absolute inset-0 -m-2 rounded-full animate-pulse-ring-delayed"
          :style="{ backgroundColor: selectedColor.light }"
        />

        <!-- Glow Effect -->
        <div
          class="absolute inset-0 -m-3 rounded-full blur-xl"
          :style="{ backgroundColor: selectedColor.glow }"
        />

        <!-- Main Center Circle -->
        <div
          :class="[
            'relative w-28 h-28 rounded-full flex flex-col items-center justify-center shadow-2xl',
            animationsEnabled ? 'animate-fade-in-scale' : ''
          ]"
          :style="{
            backgroundColor: selectedColor.light,
            boxShadow: `0 25px 50px -12px ${selectedColor.glow}`
          }"
        >
          <div
            class="w-14 h-14 rounded-full flex items-center justify-center text-white text-xl font-semibold shadow-lg"
            :style="{ backgroundColor: selectedColor.primary }"
          >
            {{ authStore.user?.firstName?.charAt(0) }}{{ authStore.user?.lastName?.charAt(0) }}
          </div>
          <span
            class="mt-1.5 text-[13px] font-medium"
            :style="{ color: selectedColor.primary }"
          >
            {{ authStore.user?.firstName }}
          </span>
          <span class="text-[11px]" :style="{ color: selectedColor.glow }">Prüfer</span>
        </div>
      </div>

      <!-- Module Nodes (45px size) -->
      <router-link
        v-for="(module, index) in modules"
        :key="module.id"
        :to="module.locked ? '#' : module.route"
        :class="[
          'absolute w-[45px] h-[45px] rounded-full flex items-center justify-center shadow-lg transition-all duration-300 cursor-pointer',
          colorClasses[module.color],
          animationsEnabled ? 'stagger-item' : '',
          hoverEffectsEnabled && hoveredModule === module.id
            ? `scale-125 z-20 shadow-xl ${hoverColorClasses[module.color]}`
            : 'z-10',
          module.locked ? 'opacity-50' : ''
        ]"
        :style="{
          left: `calc(50% + ${getModulePosition(index, modules.length).x}px - 22.5px)`,
          top: `calc(50% + ${getModulePosition(index, modules.length).y}px - 22.5px)`,
          animationDelay: animationsEnabled ? `${index * 0.1}s` : '0s'
        }"
        @mouseenter="hoveredModule = module.id"
        @mouseleave="hoveredModule = null"
        @click.prevent="module.locked ? null : undefined"
      >
        <!-- Node Label (shown below node) -->
        <span
          :class="[
            'absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap text-[13px] font-medium transition-all duration-300',
            hoveredModule === module.id
              ? 'text-gray-900 dark:text-white'
              : 'text-gray-500 dark:text-gray-400'
          ]"
        >
          {{ module.name }}
        </span>

        <svg v-if="module.icon === 'clipboard'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <svg v-else-if="module.icon === 'chart'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <svg v-else-if="module.icon === 'building'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <svg v-else-if="module.icon === 'folder'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
        <svg v-else-if="module.icon === 'random'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <svg v-else-if="module.icon === 'checklist'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
        <svg v-else-if="module.icon === 'file'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <svg v-else-if="module.icon === 'cog'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </router-link>

      <!-- Enhanced Hover Info Panel -->
      <Transition name="fade">
        <div
          v-if="hoveredModuleData"
          class="absolute left-1/2 bottom-0 -translate-x-1/2 translate-y-full mt-6 card p-5 w-72 z-30 shadow-xl"
        >
          <!-- Header with Title and Status -->
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-[15px] font-semibold text-gray-900 dark:text-white">
              {{ hoveredModuleData.name }}
            </h3>
            <span
              v-if="hoveredModuleData.status"
              :class="[
                'px-2 py-0.5 rounded-full text-[11px] font-medium',
                statusLabels[hoveredModuleData.status].class
              ]"
            >
              {{ statusLabels[hoveredModuleData.status].label }}
            </span>
          </div>

          <!-- Info Grid -->
          <div class="grid grid-cols-2 gap-3 mb-4">
            <div class="text-[13px]">
              <span class="text-gray-500 dark:text-gray-400">Status:</span>
              <span class="ml-1 text-gray-900 dark:text-white font-medium">
                {{ hoveredModuleData.stats || 'Bereit' }}
              </span>
            </div>
            <div class="text-[13px]">
              <span class="text-gray-500 dark:text-gray-400">Version:</span>
              <span class="ml-1 text-gray-900 dark:text-white font-medium">
                {{ hoveredModuleData.version || 'v1.0' }}
              </span>
            </div>
          </div>

          <!-- Action Button -->
          <button
            :class="[
              'w-full py-2 rounded-lg text-[13px] font-medium transition-colors',
              colorClasses[hoveredModuleData.color],
              'text-white hover:opacity-90'
            ]"
          >
            Modul öffnen →
          </button>
        </div>
      </Transition>
    </div>

  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(calc(100% + 10px));
}

/* Dropdown Animation */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Pulse Ring Animation */
@keyframes pulse-ring {
  0% {
    transform: scale(1);
    opacity: 0.4;
  }
  50% {
    transform: scale(1.15);
    opacity: 0.2;
  }
  100% {
    transform: scale(1);
    opacity: 0.4;
  }
}

.animate-pulse-ring {
  animation: pulse-ring 3s ease-in-out infinite;
}

.animate-pulse-ring-delayed {
  animation: pulse-ring 3s ease-in-out infinite;
  animation-delay: 1.5s;
}
</style>
