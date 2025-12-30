<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { setLocale } from '@/locales'

const emit = defineEmits<{
  'toggle-sidebar': []
  'logout': []
}>()

const { t, locale } = useI18n()
const userMenuOpen = ref(false)
const isDark = ref(document.documentElement.classList.contains('dark'))

function toggleDarkMode() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

function toggleLocale() {
  const newLocale = locale.value === 'de' ? 'en' : 'de'
  setLocale(newLocale)
}
</script>

<template>
  <header class="sticky top-0 z-30 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
    <div class="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
      <!-- Left: Menu button (mobile) -->
      <button
        type="button"
        class="lg:hidden p-2 -ml-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
        @click="emit('toggle-sidebar')"
      >
        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <!-- Right: Actions -->
      <div class="flex items-center gap-2 ml-auto">
        <!-- Language Toggle -->
        <button
          type="button"
          class="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
          :title="locale === 'de' ? 'Switch to English' : 'Auf Deutsch wechseln'"
          @click="toggleLocale"
        >
          <span class="text-sm font-medium">{{ locale.toUpperCase() }}</span>
        </button>

        <!-- Dark Mode Toggle -->
        <button
          type="button"
          class="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
          @click="toggleDarkMode"
        >
          <svg v-if="isDark" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <svg v-else class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
        </button>

        <!-- User Menu -->
        <div class="relative">
          <button
            type="button"
            class="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
            @click="userMenuOpen = !userMenuOpen"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </button>

          <!-- Dropdown -->
          <div
            v-if="userMenuOpen"
            class="absolute right-0 mt-2 w-48 rounded-lg bg-white dark:bg-gray-800 shadow-lg ring-1 ring-black ring-opacity-5 py-1"
            @click="userMenuOpen = false"
          >
            <button
              type="button"
              class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              @click="emit('logout')"
            >
              {{ t('auth.logout') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>
