<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { usePreferences } from '@/composables/usePreferences'
import { accentColors, viewTypes } from '@/types/preferences'
import type { AccentColor, ViewType, ThemeMode } from '@/types/preferences'

const { t } = useI18n()
const authStore = useAuthStore()
const {
  preferences,
  isSaving,
  setTheme,
  setAccentColor,
  setView,
  setLanguage,
  setFontSize,
  toggleAnimations,
  toggleHoverEffects,
  toggleReducedMotion,
  resetToDefaults
} = usePreferences()

const themeOptions: { value: ThemeMode; label: string; icon: string }[] = [
  { value: 'light', label: 'Hell', icon: 'sun' },
  { value: 'dark', label: 'Dunkel', icon: 'moon' },
  { value: 'system', label: 'System', icon: 'desktop' }
]

const accentColorList = computed(() =>
  Object.entries(accentColors).map(([key, value]) => ({
    key: key as AccentColor,
    ...value
  }))
)

const viewTypeList = computed(() =>
  Object.entries(viewTypes).map(([key, value]) => ({
    key: key as ViewType,
    ...value
  }))
)
</script>

<template>
  <div class="space-y-6 max-w-4xl">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ t('nav.settings') }}
        </h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {{ t('settings.description') }}
        </p>
      </div>
      <div v-if="isSaving" class="flex items-center gap-2 text-sm text-gray-500">
        <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        Speichern...
      </div>
    </div>

    <!-- Profile Section -->
    <div class="card">
      <div class="card-header">
        <h2 class="text-lg font-medium text-gray-900 dark:text-white">
          {{ t('settings.profile') }}
        </h2>
      </div>
      <div class="card-body">
        <div class="flex items-center gap-4">
          <div class="h-16 w-16 rounded-full bg-accent-100 dark:bg-accent-900 flex items-center justify-center">
            <span class="text-xl font-medium text-accent-700 dark:text-accent-300">
              {{ authStore.user?.firstName?.charAt(0) }}{{ authStore.user?.lastName?.charAt(0) }}
            </span>
          </div>
          <div>
            <p class="text-lg font-medium text-gray-900 dark:text-white">
              {{ authStore.userName }}
            </p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ authStore.user?.email }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Appearance Section -->
    <div class="card">
      <div class="card-header">
        <h2 class="text-lg font-medium text-gray-900 dark:text-white">
          {{ t('settings.appearance') }}
        </h2>
      </div>
      <div class="card-body space-y-6">
        <!-- Theme Selection -->
        <div>
          <label class="label mb-3">Theme</label>
          <div class="flex gap-3">
            <button
              v-for="option in themeOptions"
              :key="option.value"
              :class="[
                'flex-1 flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all',
                preferences.appearance.theme === option.value
                  ? 'border-accent-500 bg-accent-50 dark:bg-accent-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              ]"
              @click="setTheme(option.value)"
            >
              <div :class="[
                'w-10 h-10 rounded-lg flex items-center justify-center',
                preferences.appearance.theme === option.value
                  ? 'bg-accent-100 dark:bg-accent-800'
                  : 'bg-gray-100 dark:bg-gray-700'
              ]">
                <svg v-if="option.icon === 'sun'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
                <svg v-else-if="option.icon === 'moon'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
                <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ option.label }}</span>
              <div v-if="preferences.appearance.theme === option.value" class="w-2 h-2 rounded-full bg-accent-500" />
              <div v-else class="w-2 h-2" />
            </button>
          </div>
        </div>

        <!-- Accent Color Selection -->
        <div>
          <label class="label mb-3">Akzentfarbe</label>
          <div class="flex gap-3 flex-wrap">
            <button
              v-for="color in accentColorList"
              :key="color.key"
              :title="color.name"
              :class="[
                'w-12 h-12 rounded-xl flex items-center justify-center transition-all ring-2 ring-offset-2 ring-offset-white dark:ring-offset-gray-900',
                preferences.appearance.accentColor === color.key
                  ? 'ring-gray-900 dark:ring-white scale-110'
                  : 'ring-transparent hover:scale-105'
              ]"
              :style="{ backgroundColor: color.hex }"
              @click="setAccentColor(color.key)"
            >
              <svg
                v-if="preferences.appearance.accentColor === color.key"
                class="w-5 h-5 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </button>
          </div>
          <p class="mt-2 text-sm text-gray-500">
            {{ accentColors[preferences.appearance.accentColor].name }}
          </p>
        </div>

        <!-- Font Size -->
        <div>
          <label class="label mb-3">Schriftgröße</label>
          <div class="flex gap-3">
            <button
              v-for="size in ['small', 'medium', 'large'] as const"
              :key="size"
              :class="[
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                preferences.appearance.fontSize === size
                  ? 'bg-accent-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
              ]"
              @click="setFontSize(size)"
            >
              {{ size === 'small' ? 'Klein' : size === 'medium' ? 'Normal' : 'Groß' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Navigation Section -->
    <div class="card">
      <div class="card-header">
        <h2 class="text-lg font-medium text-gray-900 dark:text-white">
          Navigation
        </h2>
      </div>
      <div class="card-body space-y-6">
        <!-- Default View Selection -->
        <div>
          <label class="label mb-3">Standard-Ansicht</label>
          <div class="grid grid-cols-5 gap-3">
            <button
              v-for="view in viewTypeList"
              :key="view.key"
              :title="view.description"
              :class="[
                'flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-all',
                preferences.navigation.defaultView === view.key
                  ? 'border-accent-500 bg-accent-50 dark:bg-accent-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              ]"
              @click="setView(view.key)"
            >
              <!-- View Icons -->
              <div class="w-8 h-8 flex items-center justify-center text-gray-600 dark:text-gray-300">
                <template v-if="view.key === 'tiles'">
                  <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                  </svg>
                </template>
                <template v-else-if="view.key === 'list'">
                  <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </template>
                <template v-else-if="view.key === 'tree'">
                  <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h6M4 12h6m-6 6h6m4-12h6m-6 6h6m-6 6h6" />
                  </svg>
                </template>
                <template v-else-if="view.key === 'radial'">
                  <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <circle cx="12" cy="12" r="3" stroke-width="2" />
                    <circle cx="12" cy="12" r="8" stroke-width="2" stroke-dasharray="4 2" />
                  </svg>
                </template>
                <template v-else-if="view.key === 'minimal'">
                  <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14" />
                  </svg>
                </template>
              </div>
              <span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ view.name }}</span>
              <div v-if="preferences.navigation.defaultView === view.key" class="w-1.5 h-1.5 rounded-full bg-accent-500" />
              <div v-else class="w-1.5 h-1.5" />
            </button>
          </div>
        </div>

        <!-- Animation Toggles -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-white">Animationen aktivieren</p>
              <p class="text-sm text-gray-500 dark:text-gray-400">Smooth Transitions und Effekte</p>
            </div>
            <button
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200',
                preferences.navigation.enableAnimations ? 'bg-accent-600' : 'bg-gray-200 dark:bg-gray-700'
              ]"
              @click="toggleAnimations"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200',
                  preferences.navigation.enableAnimations ? 'translate-x-5' : 'translate-x-0'
                ]"
              />
            </button>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-white">Hover-Effekte</p>
              <p class="text-sm text-gray-500 dark:text-gray-400">Interaktive Elemente hervorheben</p>
            </div>
            <button
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200',
                preferences.navigation.enableHoverEffects ? 'bg-accent-600' : 'bg-gray-200 dark:bg-gray-700'
              ]"
              @click="toggleHoverEffects"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200',
                  preferences.navigation.enableHoverEffects ? 'translate-x-5' : 'translate-x-0'
                ]"
              />
            </button>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-white">Reduzierte Bewegung</p>
              <p class="text-sm text-gray-500 dark:text-gray-400">Für bessere Barrierefreiheit</p>
            </div>
            <button
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200',
                preferences.appearance.reducedMotion ? 'bg-accent-600' : 'bg-gray-200 dark:bg-gray-700'
              ]"
              @click="toggleReducedMotion"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200',
                  preferences.appearance.reducedMotion ? 'translate-x-5' : 'translate-x-0'
                ]"
              />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Language Section -->
    <div class="card">
      <div class="card-header">
        <h2 class="text-lg font-medium text-gray-900 dark:text-white">
          {{ t('settings.language') }}
        </h2>
      </div>
      <div class="card-body">
        <div class="flex gap-3">
          <button
            :class="[
              'flex-1 p-4 rounded-xl border-2 text-center transition-all',
              preferences.locale.language === 'de'
                ? 'border-accent-500 bg-accent-50 dark:bg-accent-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
            ]"
            @click="setLanguage('de')"
          >
            <span class="text-2xl">🇩🇪</span>
            <p class="mt-2 text-sm font-medium text-gray-900 dark:text-white">Deutsch</p>
          </button>
          <button
            :class="[
              'flex-1 p-4 rounded-xl border-2 text-center transition-all',
              preferences.locale.language === 'en'
                ? 'border-accent-500 bg-accent-50 dark:bg-accent-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
            ]"
            @click="setLanguage('en')"
          >
            <span class="text-2xl">🇬🇧</span>
            <p class="mt-2 text-sm font-medium text-gray-900 dark:text-white">English</p>
          </button>
        </div>
      </div>
    </div>

    <!-- Reset Section -->
    <div class="card border-red-200 dark:border-red-900">
      <div class="card-body">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-900 dark:text-white">Auf Standardwerte zurücksetzen</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">Alle Einstellungen werden zurückgesetzt</p>
          </div>
          <button
            class="px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
            @click="resetToDefaults"
          >
            Zurücksetzen
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
