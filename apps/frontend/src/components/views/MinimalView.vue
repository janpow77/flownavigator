<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePreferences } from '@/composables/usePreferences'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const { animationsEnabled, hoverEffectsEnabled } = usePreferences()
const authStore = useAuthStore()

interface Module {
  id: string
  name: string
  route: string
  shortcut: string
}

const modules: Module[] = [
  { id: 'audits', name: 'Prüfungen', route: '/audit-cases', shortcut: '1' },
  { id: 'reports', name: 'Auswertungen', route: '/reports', shortcut: '2' },
  { id: 'checklists', name: 'Checklisten', route: '/checklists', shortcut: '3' },
  { id: 'documents', name: 'Dokumente', route: '/documents', shortcut: '4' },
  { id: 'jkb', name: 'Berichte', route: '/jkb', shortcut: '5' },
  { id: 'group', name: 'Konzern', route: '/group-queries', shortcut: '6' }
]

const hoveredModule = ref<string | null>(null)

// Keyboard navigation
function handleKeydown(event: KeyboardEvent): void {
  const key = event.key
  if (key >= '1' && key <= '6') {
    const index = parseInt(key) - 1
    if (modules[index]) {
      router.push(modules[index].route)
    }
  }
  if (key === 'Escape') {
    router.back()
  }
  if (key === '?') {
    // Show help
  }
}

// Setup keyboard listener
onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})
onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

function handleLogout(): void {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="min-h-[600px] flex flex-col items-center justify-center relative">
    <!-- Logo & Title -->
    <div
      :class="[
        'text-center mb-16',
        animationsEnabled ? 'animate-fade-in' : ''
      ]"
    >
      <h1 class="text-4xl font-light text-gray-900 dark:text-white tracking-wide">
        FlowAudit
      </h1>
      <div class="mt-4 w-24 h-px bg-gray-300 dark:bg-gray-600 mx-auto" />
    </div>

    <!-- Module Links - 2 Columns -->
    <nav
      :class="[
        'grid grid-cols-2 gap-x-16 gap-y-6',
        animationsEnabled ? 'animate-fade-in-up' : ''
      ]"
      :style="animationsEnabled ? { animationDelay: '0.1s' } : {}"
    >
      <router-link
        v-for="module in modules"
        :key="module.id"
        :to="module.route"
        :class="[
          'group relative text-lg font-light transition-all duration-200',
          hoveredModule === module.id
            ? 'text-accent-600 dark:text-accent-400'
            : 'text-gray-600 dark:text-gray-400',
          hoverEffectsEnabled ? 'hover:text-accent-600 dark:hover:text-accent-400' : ''
        ]"
        @mouseenter="hoveredModule = module.id"
        @mouseleave="hoveredModule = null"
      >
        <span class="relative">
          {{ module.name }}
          <!-- Underline on hover -->
          <span
            :class="[
              'absolute left-0 bottom-0 h-px bg-accent-600 dark:bg-accent-400 transition-all duration-300',
              hoveredModule === module.id ? 'w-full' : 'w-0'
            ]"
          />
        </span>
        <!-- Keyboard shortcut hint -->
        <kbd
          :class="[
            'absolute -right-8 top-1/2 -translate-y-1/2 text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-400 transition-opacity',
            hoveredModule === module.id ? 'opacity-100' : 'opacity-0'
          ]"
        >
          {{ module.shortcut }}
        </kbd>
      </router-link>
    </nav>

    <!-- Divider -->
    <div class="mt-16 w-24 h-px bg-gray-300 dark:bg-gray-600" />

    <!-- Settings Link -->
    <router-link
      :to="{ name: 'settings' }"
      :class="[
        'mt-8 text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors flex items-center gap-2',
        animationsEnabled ? 'animate-fade-in' : ''
      ]"
      :style="animationsEnabled ? { animationDelay: '0.2s' } : {}"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      Einstellungen
    </router-link>

    <!-- User Info (Bottom Right) -->
    <div class="absolute bottom-8 right-8 flex items-center gap-4 text-sm text-gray-400">
      <span>{{ authStore.user?.firstName }} {{ authStore.user?.lastName?.charAt(0) }}.</span>
      <span class="text-gray-300 dark:text-gray-600">│</span>
      <button
        class="hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        @click="handleLogout"
      >
        Abmelden
      </button>
    </div>

    <!-- Keyboard Hints (Bottom Left) -->
    <div class="absolute bottom-8 left-8 text-xs text-gray-300 dark:text-gray-600 space-y-1">
      <div><kbd class="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800">1-6</kbd> Direktzugriff</div>
      <div><kbd class="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800">Esc</kbd> Zurück</div>
      <div><kbd class="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800">?</kbd> Hilfe</div>
    </div>
  </div>
</template>
