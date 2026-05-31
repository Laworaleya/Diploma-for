<template>
  <div class="lang-switcher">
    <button
      v-for="lang in languages"
      :key="lang.code"
      :class="['lang-btn', { active: locale === lang.code }]"
      @click="switchLanguage(lang.code)"
      :title="lang.name"
    >
      {{ lang.label }}
    </button>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../../stores/auth'

const { locale } = useI18n()
const authStore = useAuthStore()

const languages = [
  { code: 'kk', label: 'ҚАЗ', name: 'Қазақша' },
  { code: 'ru', label: 'РУС', name: 'Русский' },
  { code: 'en', label: 'ENG', name: 'English' },
]

function switchLanguage(code) {
  locale.value = code
  localStorage.setItem('locale', code)
  if (authStore.isAuthenticated) {
    authStore.updateProfile({ preferred_language: code }).catch(() => {})
  }
}
</script>

<style scoped>
.lang-switcher {
  display: flex;
  gap: 2px;
  background: var(--bg-tertiary);
  border-radius: 6px;
  padding: 2px;
}

.lang-btn {
  padding: 0.25rem 0.5rem;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 0.7rem;
  font-weight: 600;
  border-radius: 4px;
  cursor: pointer;
  transition: all var(--transition-fast);
  letter-spacing: 0.03em;
  font-family: var(--font-family);
}

.lang-btn:hover {
  color: var(--text-primary);
}

.lang-btn.active {
  background: var(--primary);
  color: white;
}
</style>
