import { createI18n } from 'vue-i18n'
import ru from './ru.json'
import en from './en.json'
import kk from './kk.json'

const savedLocale = localStorage.getItem('locale') || 'ru'

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'en',
  messages: { ru, en, kk },
})

export default i18n
