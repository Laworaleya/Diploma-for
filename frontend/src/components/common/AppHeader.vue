<template>
  <header class="app-header">
    <div class="header-inner">
      <router-link to="/" class="logo">
        <span class="logo-icon">₸</span>
        <span class="logo-text">FinLit</span>
      </router-link>

      <nav class="nav-links" v-if="authStore.isAuthenticated">
        <router-link to="/dashboard"          class="nav-link" active-class="active">{{ $t('nav.dashboard') }}</router-link>
        <router-link to="/reports"            class="nav-link" active-class="active">{{ $t('nav.reports') }}</router-link>
        <router-link to="/goals"              class="nav-link" active-class="active">{{ $t('nav.goals') }}</router-link>
        <router-link to="/ai"                 class="nav-link" active-class="active">{{ $t('nav.ai') }}</router-link>
        <router-link to="/tracker"             class="nav-link" active-class="active">{{ $t('nav.tracker') }}</router-link>
        <router-link to="/recurring-payments" class="nav-link" active-class="active">{{ $t('nav.recurring_payments') }}</router-link>
        <router-link v-if="authStore.isAdmin" to="/admin" class="nav-link nav-link-admin" active-class="active">{{ $t('nav.admin') }}</router-link>
      </nav>

      <div class="header-actions">
        <LanguageSwitcher />
        <template v-if="authStore.isAuthenticated">
          <div class="user-badge">
            <div class="user-avatar">{{ userInitials }}</div>
            <span class="user-name">{{ authStore.user?.name }}</span>
          </div>
          <button class="btn-logout" @click="handleLogout">
            <i class="pi pi-sign-out"></i>
            <span>{{ $t('nav.logout') }}</span>
          </button>
        </template>
        <template v-else>
          <router-link to="/login" class="btn-glass btn-sm">{{ $t('nav.login') }}</router-link>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import LanguageSwitcher from './LanguageSwitcher.vue'

const authStore = useAuthStore()
const router = useRouter()

const userInitials = computed(() => {
  const name = authStore.user?.name || ''
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name.slice(0, 2).toUpperCase() || '?'
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-header {
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-inner {
  max-width: 1600px;
  width: 96%;
  margin: 0 auto;
  padding: 0 1.5rem;
  height: 60px;
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

/* Logo */
.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  flex-shrink: 0;
}

.logo-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  color: white;
  font-weight: 700;
  box-shadow: 0 0 14px rgba(99, 102, 241, 0.3);
}

.logo-text {
  font-size: 1.2rem;
  font-weight: 800;
  background: linear-gradient(135deg, var(--primary-light) 0%, var(--secondary-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Nav */
.nav-links {
  display: flex;
  gap: 0.1rem;
  flex: 1;
}

.nav-link {
  padding: 0.4rem 0.75rem;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.nav-link:hover {
  color: var(--text-primary);
  background: rgba(148, 163, 184, 0.08);
}

.nav-link.active {
  color: var(--primary-light);
  background: rgba(99, 102, 241, 0.12);
}

.nav-link-admin {
  color: var(--warning, #f59e0b);
}

.nav-link-admin:hover {
  color: #fbbf24;
  background: rgba(245, 158, 11, 0.1);
}

.nav-link-admin.active {
  color: #fbbf24;
  background: rgba(245, 158, 11, 0.15);
}

/* Header right */
.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

/* User badge */
.user-badge {
  display: flex;
  align-items: center;
  gap: 0.55rem;
}

.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.65rem;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.user-name {
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: 500;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Logout button */
.btn-logout {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: none;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.38rem 0.75rem;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn-logout:hover {
  color: var(--danger-light);
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.06);
}

.btn-sm {
  padding: 0.4rem 0.9rem;
  font-size: 0.8rem;
}

@media (max-width: 768px) {
  .nav-links   { display: none; }
  .user-name   { display: none; }
  .btn-logout span { display: none; }
  .btn-logout  { padding: 0.4rem 0.6rem; }

  .header-inner {
    height: 52px;
    gap: 0.5rem;
    padding: 0 1rem;
  }

  .logo-text { font-size: 1.05rem; }
}
</style>
