<template>
  <nav class="bottom-nav" v-if="authStore.isAuthenticated">
    <router-link
      v-for="tab in tabs"
      :key="tab.to"
      :to="tab.to"
      class="bnav-item"
      :class="{ active: isActive(tab) }"
    >
      <i :class="['bnav-icon', tab.icon]"></i>
      <span class="bnav-label">{{ shortLabel(tab.labelKey) }}</span>
    </router-link>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useI18n } from 'vue-i18n'

const authStore = useAuthStore()
const route = useRoute()
const { t } = useI18n()

const tabs = [
  { to: '/dashboard', labelKey: 'nav.dashboard', icon: 'pi pi-home' },
  { to: '/reports', labelKey: 'nav.reports', icon: 'pi pi-chart-bar' },
  { to: '/goals', labelKey: 'nav.goals', icon: 'pi pi-flag' },
  { to: '/ai', labelKey: 'nav.ai', icon: 'pi pi-comments' },
  { to: '/recurring-payments', labelKey: 'nav.recurring_payments', icon: 'pi pi-refresh' },
]

function shortLabel(labelKey) {
  const full = t(labelKey)
  const parts = full.split(' ')
  return parts.length > 1 ? parts[parts.length - 1] : full
}

function isActive(tab) {
  if (tab.to === '/ai') return route.path.startsWith('/ai')
  return route.path === tab.to
}
</script>

<style scoped>
.bottom-nav {
  display: none;
}

@media (max-width: 768px) {
  .bottom-nav {
    display: flex;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: rgba(15, 23, 42, 0.96);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-top: 1px solid var(--border-color);
    z-index: 200;
    padding-bottom: env(safe-area-inset-bottom, 0);
  }

  .bnav-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    text-decoration: none;
    color: var(--text-muted);
    transition: color var(--transition-fast);
    padding: 0.2rem 0;
  }

  .bnav-item.active {
    color: var(--primary-light);
  }

  .bnav-icon {
    font-size: 1.2rem;
    line-height: 1;
  }

  .bnav-label {
    font-size: 0.58rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    line-height: 1;
    max-width: 60px;
    text-align: center;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
