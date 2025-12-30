// FlowAudit User Preferences Types

export type ThemeMode = 'light' | 'dark' | 'system'
export type AccentColor = 'blue' | 'purple' | 'green' | 'orange' | 'pink' | 'teal'
export type ViewType = 'tiles' | 'list' | 'tree' | 'radial' | 'minimal'
export type FontSize = 'small' | 'medium' | 'large'
export type TimeFormat = '12h' | '24h'
export type EmailDigest = 'none' | 'daily' | 'weekly'

export type WidgetId =
  | 'active_audits'
  | 'appointments'
  | 'tasks'
  | 'activities'
  | 'statistics'
  | 'quick_actions'

export interface AppearancePreferences {
  theme: ThemeMode
  accentColor: AccentColor
  fontSize: FontSize
  reducedMotion: boolean
  highContrast: boolean
}

export interface NavigationPreferences {
  defaultView: ViewType
  sidebarCollapsed: boolean
  enableAnimations: boolean
  enableHoverEffects: boolean
  showModuleBadges: boolean
}

export interface DashboardPreferences {
  startPage: string
  visibleWidgets: WidgetId[]
  widgetOrder: WidgetId[]
  compactMode: boolean
}

export interface ModulePreference {
  defaultTab?: string
  sortOrder?: string
  filters?: Record<string, unknown>
  columns?: string[]
}

export interface NotificationPreferences {
  enabled: boolean
  sound: boolean
  desktop: boolean
  emailDigest: EmailDigest
}

export interface LocalePreferences {
  language: 'de' | 'en'
  dateFormat: string
  timeFormat: TimeFormat
  timezone: string
  numberFormat: string
}

export interface ShortcutPreferences {
  enabled: boolean
  custom: Record<string, string>
}

export interface UserPreferences {
  id?: string
  userId?: string

  appearance: AppearancePreferences
  navigation: NavigationPreferences
  dashboard: DashboardPreferences
  modulePreferences: Record<string, ModulePreference>
  notifications: NotificationPreferences
  locale: LocalePreferences
  shortcuts: ShortcutPreferences

  updatedAt?: string
}

export const defaultPreferences: UserPreferences = {
  appearance: {
    theme: 'system',
    accentColor: 'blue',
    fontSize: 'medium',
    reducedMotion: false,
    highContrast: false
  },
  navigation: {
    defaultView: 'tiles',
    sidebarCollapsed: false,
    enableAnimations: true,
    enableHoverEffects: true,
    showModuleBadges: true
  },
  dashboard: {
    startPage: '/dashboard',
    visibleWidgets: ['active_audits', 'appointments', 'tasks', 'activities'],
    widgetOrder: ['active_audits', 'appointments', 'tasks', 'activities'],
    compactMode: false
  },
  modulePreferences: {},
  notifications: {
    enabled: true,
    sound: false,
    desktop: true,
    emailDigest: 'daily'
  },
  locale: {
    language: 'de',
    dateFormat: 'DD.MM.YYYY',
    timeFormat: '24h',
    timezone: 'Europe/Berlin',
    numberFormat: 'de-DE'
  },
  shortcuts: {
    enabled: true,
    custom: {}
  }
}

export const accentColors: Record<AccentColor, { name: string; hex: string }> = {
  blue: { name: 'Ocean', hex: '#3b82f6' },
  purple: { name: 'Lavender', hex: '#a855f7' },
  green: { name: 'Forest', hex: '#10b981' },
  orange: { name: 'Sunset', hex: '#f97316' },
  pink: { name: 'Rose', hex: '#ec4899' },
  teal: { name: 'Teal', hex: '#14b8a6' }
}

export const viewTypes: Record<ViewType, { name: string; icon: string; description: string }> = {
  tiles: {
    name: 'Kacheln',
    icon: 'grid',
    description: 'Übersichtliche Karten mit Icons und Statistiken'
  },
  list: {
    name: 'Liste',
    icon: 'list',
    description: 'Platzsparend, ideal für Power-User'
  },
  tree: {
    name: 'Sidebar',
    icon: 'sidebar',
    description: 'Klassische Navigation mit Hierarchie'
  },
  radial: {
    name: 'Radial',
    icon: 'circle',
    description: 'Visuell beeindruckend, zentrale Nutzerposition'
  },
  minimal: {
    name: 'Minimal',
    icon: 'minus',
    description: 'Maximale Aufgeräumtheit, nur das Wesentliche'
  }
}
