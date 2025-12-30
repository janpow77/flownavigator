import { ref, computed, watch, onMounted } from 'vue'
import type {
  UserPreferences,
  ThemeMode,
  AccentColor,
  ViewType,
  WidgetId
} from '@/types/preferences'
import { defaultPreferences } from '@/types/preferences'
import { setLocale } from '@/locales'

const STORAGE_KEY = 'flowaudit-preferences'

// Global state (singleton pattern)
const preferences = ref<UserPreferences>(loadFromStorage())
const isLoading = ref(false)
const isSaving = ref(false)
const lastSyncError = ref<string | null>(null)

// Load from localStorage
function loadFromStorage(): UserPreferences {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return { ...defaultPreferences, ...JSON.parse(stored) }
    }
  } catch (e) {
    console.error('Failed to load preferences from storage:', e)
  }
  return { ...defaultPreferences }
}

// Save to localStorage
function saveToStorage(prefs: UserPreferences): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs))
  } catch (e) {
    console.error('Failed to save preferences to storage:', e)
  }
}

// Apply theme to document
function applyTheme(theme: ThemeMode): void {
  const isDark =
    theme === 'dark' ||
    (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)

  document.documentElement.classList.toggle('dark', isDark)
  localStorage.setItem('theme', isDark ? 'dark' : 'light')
}

// Apply accent color to document
function applyAccentColor(color: AccentColor): void {
  document.documentElement.setAttribute('data-accent', color)
}

// Apply reduced motion
function applyReducedMotion(reduced: boolean): void {
  document.documentElement.classList.toggle('reduced-motion', reduced)
}

// Apply font size
function applyFontSize(size: 'small' | 'medium' | 'large'): void {
  const fontSizes = {
    small: '14px',
    medium: '16px',
    large: '18px'
  }
  document.documentElement.style.fontSize = fontSizes[size]
}

export function usePreferences() {
  // Computed values
  const isDark = computed(() => {
    const theme = preferences.value.appearance.theme
    if (theme === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    return theme === 'dark'
  })

  const currentView = computed(() => preferences.value.navigation.defaultView)
  const accentColor = computed(() => preferences.value.appearance.accentColor)
  const language = computed(() => preferences.value.locale.language)
  const animationsEnabled = computed(() => preferences.value.navigation.enableAnimations)
  const hoverEffectsEnabled = computed(() => preferences.value.navigation.enableHoverEffects)
  const sidebarCollapsed = computed(() => preferences.value.navigation.sidebarCollapsed)

  // Watch for theme changes
  watch(
    () => preferences.value.appearance.theme,
    (theme) => applyTheme(theme),
    { immediate: true }
  )

  // Watch for accent color changes
  watch(
    () => preferences.value.appearance.accentColor,
    (color) => applyAccentColor(color),
    { immediate: true }
  )

  // Watch for reduced motion changes
  watch(
    () => preferences.value.appearance.reducedMotion,
    (reduced) => applyReducedMotion(reduced),
    { immediate: true }
  )

  // Watch for font size changes
  watch(
    () => preferences.value.appearance.fontSize,
    (size) => applyFontSize(size),
    { immediate: true }
  )

  // Watch for language changes
  watch(
    () => preferences.value.locale.language,
    (lang) => setLocale(lang),
    { immediate: true }
  )

  // Save to storage on any change
  watch(
    preferences,
    (prefs) => saveToStorage(prefs),
    { deep: true }
  )

  // Listen for system theme changes
  onMounted(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => {
      if (preferences.value.appearance.theme === 'system') {
        applyTheme('system')
      }
    }
    mediaQuery.addEventListener('change', handler)
  })

  // Actions
  async function loadFromServer(): Promise<void> {
    isLoading.value = true
    lastSyncError.value = null
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const response = await fetch('/api/preferences', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const serverPrefs = await response.json()
        if (serverPrefs) {
          preferences.value = { ...defaultPreferences, ...serverPrefs }
        }
      }
    } catch (e) {
      lastSyncError.value = 'Einstellungen konnten nicht geladen werden'
      console.error('Failed to load preferences from server:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function saveToServer(): Promise<void> {
    isSaving.value = true
    lastSyncError.value = null
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const response = await fetch('/api/preferences', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(preferences.value)
      })

      if (!response.ok) {
        throw new Error('Failed to save preferences')
      }
    } catch (e) {
      lastSyncError.value = 'Einstellungen konnten nicht gespeichert werden'
      console.error('Failed to save preferences to server:', e)
    } finally {
      isSaving.value = false
    }
  }

  // Debounced save to server
  let saveTimeout: ReturnType<typeof setTimeout> | null = null
  function debouncedSaveToServer(): void {
    if (saveTimeout) clearTimeout(saveTimeout)
    saveTimeout = setTimeout(() => saveToServer(), 1000)
  }

  // Setters with auto-save
  function setTheme(theme: ThemeMode): void {
    preferences.value.appearance.theme = theme
    debouncedSaveToServer()
  }

  function setAccentColor(color: AccentColor): void {
    preferences.value.appearance.accentColor = color
    debouncedSaveToServer()
  }

  function setView(view: ViewType): void {
    preferences.value.navigation.defaultView = view
    debouncedSaveToServer()
  }

  function setLanguage(lang: 'de' | 'en'): void {
    preferences.value.locale.language = lang
    debouncedSaveToServer()
  }

  function setFontSize(size: 'small' | 'medium' | 'large'): void {
    preferences.value.appearance.fontSize = size
    debouncedSaveToServer()
  }

  function toggleSidebar(): void {
    preferences.value.navigation.sidebarCollapsed = !preferences.value.navigation.sidebarCollapsed
    debouncedSaveToServer()
  }

  function toggleAnimations(): void {
    preferences.value.navigation.enableAnimations = !preferences.value.navigation.enableAnimations
    debouncedSaveToServer()
  }

  function toggleHoverEffects(): void {
    preferences.value.navigation.enableHoverEffects = !preferences.value.navigation.enableHoverEffects
    debouncedSaveToServer()
  }

  function toggleReducedMotion(): void {
    preferences.value.appearance.reducedMotion = !preferences.value.appearance.reducedMotion
    debouncedSaveToServer()
  }

  function setVisibleWidgets(widgets: WidgetId[]): void {
    preferences.value.dashboard.visibleWidgets = widgets
    debouncedSaveToServer()
  }

  function setWidgetOrder(order: WidgetId[]): void {
    preferences.value.dashboard.widgetOrder = order
    debouncedSaveToServer()
  }

  function resetToDefaults(): void {
    preferences.value = { ...defaultPreferences }
    saveToServer()
  }

  // Initialize
  function initialize(): void {
    // Apply all settings on init
    applyTheme(preferences.value.appearance.theme)
    applyAccentColor(preferences.value.appearance.accentColor)
    applyReducedMotion(preferences.value.appearance.reducedMotion)
    applyFontSize(preferences.value.appearance.fontSize)

    // Try to sync with server
    loadFromServer()
  }

  return {
    // State
    preferences,
    isLoading,
    isSaving,
    lastSyncError,

    // Computed
    isDark,
    currentView,
    accentColor,
    language,
    animationsEnabled,
    hoverEffectsEnabled,
    sidebarCollapsed,

    // Actions
    initialize,
    loadFromServer,
    saveToServer,
    setTheme,
    setAccentColor,
    setView,
    setLanguage,
    setFontSize,
    toggleSidebar,
    toggleAnimations,
    toggleHoverEffects,
    toggleReducedMotion,
    setVisibleWidgets,
    setWidgetOrder,
    resetToDefaults
  }
}
