import { createI18n } from 'vue-i18n'
import de from './de.json'
import en from './en.json'

export type MessageSchema = typeof de

const i18n = createI18n<[MessageSchema], 'de' | 'en'>({
  legacy: false,
  locale: localStorage.getItem('locale') || 'de',
  fallbackLocale: 'de',
  messages: {
    de,
    en,
  },
})

export default i18n

export function setLocale(locale: 'de' | 'en') {
  // @ts-expect-error - locale is a ref in composition API mode
  i18n.global.locale.value = locale
  localStorage.setItem('locale', locale)
  document.documentElement.lang = locale
}
