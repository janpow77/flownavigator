<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { usePreferences } from '@/composables/usePreferences'
import { useAuthStore } from '@/stores/auth'

const { animationsEnabled, hoverEffectsEnabled } = usePreferences()
const authStore = useAuthStore()

interface Module {
  id: string
  name: string
  icon: string
  route: string
  stats?: string
  color: string
  locked?: boolean
}

const modules: Module[] = [
  { id: 'audits', name: 'Prüfungen', icon: 'clipboard', route: '/audit-cases', stats: '12 aktiv, 2 fällig', color: 'blue' },
  { id: 'reports', name: 'Auswertungen', icon: 'chart', route: '/reports', stats: '3 neue', color: 'purple' },
  { id: 'group', name: 'Konzern', icon: 'building', route: '/group-queries', stats: '2 offen', color: 'cyan' },
  { id: 'documents', name: 'Dokumente', icon: 'folder', route: '/documents', stats: '1.2 GB', color: 'orange' },
  { id: 'sampling', name: 'Stichproben', icon: 'random', route: '/sampling', stats: 'MUS, Random', color: 'green' },
  { id: 'checklists', name: 'Checklisten', icon: 'checklist', route: '/checklists', stats: '8 Vorlagen', color: 'pink' },
  { id: 'jkb', name: 'Berichte', icon: 'file', route: '/jkb', stats: 'JKB 2024', color: 'teal' },
  { id: 'admin', name: 'Admin', icon: 'cog', route: '/admin', color: 'gray' }
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

// Calculate position for each module in a circle
function getModulePosition(index: number, total: number): { x: number; y: number; angle: number } {
  const angle = (index / total) * 2 * Math.PI - Math.PI / 2 // Start from top
  const radius = 180 // Distance from center
  return {
    x: Math.cos(angle) * radius,
    y: Math.sin(angle) * radius,
    angle: angle * (180 / Math.PI)
  }
}

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
  <div class="flex items-center justify-center min-h-[600px] relative">
    <!-- Radial Container -->
    <div
      ref="centerElement"
      class="relative w-[500px] h-[500px]"
      :style="animationsEnabled ? { transform: `translate(${mousePosition.x}px, ${mousePosition.y}px)` } : {}"
    >
      <!-- Connection Lines -->
      <svg class="absolute inset-0 w-full h-full pointer-events-none">
        <line
          v-for="(module, index) in modules"
          :key="`line-${module.id}`"
          x1="50%"
          y1="50%"
          :x2="`${50 + getModulePosition(index, modules.length).x / 5}%`"
          :y2="`${50 + getModulePosition(index, modules.length).y / 5}%`"
          :class="[
            'stroke-gray-200 dark:stroke-gray-700 transition-all duration-300',
            hoveredModule === module.id ? 'stroke-accent-500 stroke-2' : 'stroke-1'
          ]"
        />
      </svg>

      <!-- Center User Circle -->
      <div
        :class="[
          'absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 rounded-full bg-accent-100 dark:bg-accent-900 flex flex-col items-center justify-center z-10 shadow-lg',
          animationsEnabled ? 'animate-fade-in-scale' : ''
        ]"
      >
        <div class="w-12 h-12 rounded-full bg-accent-600 flex items-center justify-center text-white text-lg font-semibold">
          {{ authStore.user?.firstName?.charAt(0) }}{{ authStore.user?.lastName?.charAt(0) }}
        </div>
        <span class="mt-1 text-xs font-medium text-accent-700 dark:text-accent-300">
          {{ authStore.user?.firstName }}
        </span>
        <span class="text-[10px] text-accent-500">Prüfer</span>
      </div>

      <!-- Module Nodes -->
      <router-link
        v-for="(module, index) in modules"
        :key="module.id"
        :to="module.locked ? '#' : module.route"
        :class="[
          'absolute w-16 h-16 rounded-full flex items-center justify-center shadow-md transition-all duration-300 cursor-pointer',
          colorClasses[module.color],
          animationsEnabled ? 'stagger-item' : '',
          hoverEffectsEnabled && hoveredModule === module.id ? 'scale-125 z-20' : 'z-10',
          module.locked ? 'opacity-50' : ''
        ]"
        :style="{
          left: `calc(50% + ${getModulePosition(index, modules.length).x}px - 32px)`,
          top: `calc(50% + ${getModulePosition(index, modules.length).y}px - 32px)`,
          animationDelay: animationsEnabled ? `${index * 0.1}s` : '0s'
        }"
        @mouseenter="hoveredModule = module.id"
        @mouseleave="hoveredModule = null"
        @click.prevent="module.locked ? null : undefined"
      >
        <svg v-if="module.icon === 'clipboard'" class="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <svg v-else-if="module.icon === 'chart'" class="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <svg v-else-if="module.icon === 'building'" class="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <svg v-else-if="module.icon === 'folder'" class="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
        <svg v-else-if="module.icon === 'random'" class="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <svg v-else-if="module.icon === 'checklist'" class="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
        <svg v-else-if="module.icon === 'file'" class="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <svg v-else-if="module.icon === 'cog'" class="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </router-link>

      <!-- Hover Tooltip -->
      <Transition name="fade">
        <div
          v-if="hoveredModule"
          class="absolute left-1/2 bottom-0 -translate-x-1/2 translate-y-full mt-4 card p-4 w-64 z-30"
        >
          <h3 class="font-semibold text-gray-900 dark:text-white">
            {{ modules.find(m => m.id === hoveredModule)?.name }}
          </h3>
          <p class="mt-1 text-sm text-gray-500">
            {{ modules.find(m => m.id === hoveredModule)?.stats || 'Modul öffnen' }}
          </p>
          <button class="mt-3 btn-primary w-full text-sm">
            Öffnen →
          </button>
        </div>
      </Transition>
    </div>

    <!-- Locked Module Info -->
    <div class="absolute bottom-8 left-1/2 -translate-x-1/2 text-center">
      <div class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-500 text-sm border border-dashed border-gray-300 dark:border-gray-600">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
        FlowInvoice (gesperrt)
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
