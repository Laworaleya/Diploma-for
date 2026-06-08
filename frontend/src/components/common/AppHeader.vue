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

        <!-- Telegram Bot button -->
        <div class="tg-wrap" v-if="authStore.isAuthenticated" ref="tgWrapRef">
          <button
            class="tg-icon-btn"
            :class="{ active: tgOpen, linked: authStore.user?.telegram_id }"
            @click.stop="toggleTgPanel"
            :title="authStore.user?.telegram_id ? 'Telegram подключён' : 'Привязать Telegram'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
            </svg>
            <span v-if="authStore.user?.telegram_id" class="tg-linked-dot"></span>
          </button>

          <!-- Telegram panel -->
          <div v-if="tgOpen" class="tg-panel glass-card" @click.stop>
            <div class="tg-panel-head">
              <div class="tg-panel-icon">TG</div>
              <span class="tg-panel-title">Telegram</span>
              <button class="tg-panel-close" @click="tgOpen = false">✕</button>
            </div>

            <!-- Already linked -->
            <template v-if="authStore.user?.telegram_id">
              <div class="tg-linked-state">
                <div class="tg-linked-check">✓</div>
                <div>
                  <div class="tg-linked-title">Telegram подключён</div>
                  <div v-if="authStore.user?.telegram_username" class="tg-linked-user">@{{ authStore.user.telegram_username }}</div>
                </div>
              </div>
              <a :href="telegramUrl" target="_blank" class="btn-glass tg-open-bot-btn">Открыть бота</a>
            </template>

            <!-- Not linked -->
            <template v-else>
              <p class="tg-panel-desc">Добавляй расходы и следи за балансом прямо из Telegram</p>
              <div class="tg-steps">
                <div class="tg-step">
                  <span class="tg-snum">1</span>
                  <div class="tg-sbody">
                    <span class="tg-stext">Открой бота в Telegram</span>
                    <a :href="telegramUrl" target="_blank" class="btn-glass tg-sbtn">Открыть</a>
                  </div>
                </div>
                <div class="tg-step">
                  <span class="tg-snum">2</span>
                  <div class="tg-sbody">
                    <span class="tg-stext">Нажми /start и введи месячный бюджет — выполни первую команду которую просит бот. Только после этого вставь код ниже.</span>
                  </div>
                </div>
                <div class="tg-step">
                  <span class="tg-snum">3</span>
                  <div class="tg-sbody">
                    <span class="tg-stext">Вставь этот код в бот</span>
                    <button v-if="!linkCode" class="btn-primary-gradient tg-gen-btn" :disabled="linkLoading" @click="getLinkCode">
                      <span v-if="linkLoading" class="spinner-sm"></span>
                      {{ linkLoading ? '' : 'Получить код' }}
                    </button>
                    <div v-else class="tg-code-row">
                      <code>/link {{ linkCode }}</code>
                      <button class="tg-copy-btn" @click="copyCode">{{ copied ? 'Скопировано' : 'Копировать' }}</button>
                    </div>
                    <p v-if="linkCode" class="tg-code-note">Действителен 10 минут</p>
                  </div>
                </div>
                <div class="tg-step">
                  <span class="tg-snum">4</span>
                  <div class="tg-sbody">
                    <span class="tg-stext">Обнови страницу</span>
                    <button class="btn-glass tg-sbtn" @click="refreshProfile">Обновить</button>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>

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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import LanguageSwitcher from './LanguageSwitcher.vue'
import api from '../../services/api'

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

// ── Telegram panel ──────────────────────────────────────────────────────────
const tgOpen = ref(false)
const tgWrapRef = ref(null)
const linkCode = ref(null)
const linkLoading = ref(false)
const copied = ref(false)

const telegramUrl = computed(() =>
  `https://t.me/${import.meta.env.VITE_TELEGRAM_BOT_USERNAME || 'FinLit_bot'}`
)

function toggleTgPanel() {
  tgOpen.value = !tgOpen.value
  if (!tgOpen.value) {
    linkCode.value = null
    copied.value = false
  }
}

async function getLinkCode() {
  linkLoading.value = true
  try {
    const res = await api.get('/auth/link-code')
    linkCode.value = res.data.code
  } catch {}
  finally { linkLoading.value = false }
}

async function copyCode() {
  await navigator.clipboard.writeText(`/link ${linkCode.value}`)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

async function refreshProfile() {
  try {
    const res = await api.get('/auth/me')
    authStore.user = res.data
    localStorage.setItem('user', JSON.stringify(res.data))
  } catch {}
  tgOpen.value = false
  window.location.reload()
}

function handleClickOutside(e) {
  if (tgWrapRef.value && !tgWrapRef.value.contains(e.target)) {
    tgOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
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
  width: 34px; height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem; color: white; font-weight: 700;
  box-shadow: 0 0 14px rgba(99,102,241,0.3);
}
.logo-text {
  font-size: 1.2rem; font-weight: 800;
  background: linear-gradient(135deg, var(--primary-light) 0%, var(--secondary-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Nav */
.nav-links { display: flex; gap: 0.1rem; flex: 1; }
.nav-link {
  padding: 0.4rem 0.75rem;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.85rem; font-weight: 500;
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.nav-link:hover { color: var(--text-primary); background: rgba(148,163,184,0.08); }
.nav-link.active { color: var(--primary-light); background: rgba(99,102,241,0.12); }
.nav-link-admin { color: var(--warning, #f59e0b); }
.nav-link-admin:hover { color: #fbbf24; background: rgba(245,158,11,0.1); }
.nav-link-admin.active { color: #fbbf24; background: rgba(245,158,11,0.15); }

/* Header right */
.header-actions { display: flex; align-items: center; gap: 0.75rem; flex-shrink: 0; }

/* User badge */
.user-badge { display: flex; align-items: center; gap: 0.55rem; }
.user-avatar {
  width: 30px; height: 30px; border-radius: 50%;
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.65rem; font-weight: 700; color: white; flex-shrink: 0;
}
.user-name {
  color: var(--text-secondary); font-size: 0.85rem; font-weight: 500;
  max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

/* Logout */
.btn-logout {
  display: inline-flex; align-items: center; gap: 0.4rem;
  background: none; border: 1px solid var(--border-color);
  border-radius: var(--radius-sm); color: var(--text-muted);
  font-size: 0.8rem; font-weight: 500; padding: 0.38rem 0.75rem;
  cursor: pointer; transition: all var(--transition-fast); white-space: nowrap;
}
.btn-logout:hover { color: var(--danger-light); border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.06); }
.btn-sm { padding: 0.4rem 0.9rem; font-size: 0.8rem; }

/* ── Telegram button ────────────────────────────────────────────────────────── */
.tg-wrap { position: relative; }

.tg-icon-btn {
  position: relative;
  width: 32px; height: 32px;
  border-radius: var(--radius-sm);
  background: rgba(42,171,238,0.1);
  border: 1px solid rgba(42,171,238,0.2);
  color: #5BB8E8;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}
.tg-icon-btn:hover { background: rgba(42,171,238,0.2); border-color: rgba(42,171,238,0.4); color: #2AABEE; }
.tg-icon-btn.active { background: rgba(42,171,238,0.2); border-color: rgba(42,171,238,0.5); color: #2AABEE; }
.tg-icon-btn.linked { background: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.3); color: #34D399; }
.tg-icon-btn.linked:hover { background: rgba(16,185,129,0.2); }

.tg-linked-dot {
  position: absolute;
  top: -3px; right: -3px;
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #10B981;
  border: 1.5px solid rgba(15,23,42,0.9);
}

/* ── Telegram panel ─────────────────────────────────────────────────────────── */
.tg-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  width: 300px;
  padding: 1.25rem;
  z-index: 200;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}

.tg-panel-head {
  display: flex; align-items: center; gap: 0.65rem;
}
.tg-panel-icon {
  width: 28px; height: 28px;
  background: linear-gradient(135deg, #2AABEE, #229ED9);
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.65rem; font-weight: 800; color: #fff;
  flex-shrink: 0;
}
.tg-panel-title { font-size: 0.9rem; font-weight: 700; color: var(--text-primary); flex: 1; }
.tg-panel-close {
  background: none; border: none; color: var(--text-muted);
  font-size: 0.85rem; cursor: pointer; line-height: 1; padding: 2px;
  transition: color 0.15s;
}
.tg-panel-close:hover { color: var(--text-primary); }

.tg-panel-desc { font-size: 0.8rem; color: var(--text-muted); margin: 0; line-height: 1.5; }

/* Linked state */
.tg-linked-state {
  display: flex; align-items: center; gap: 0.75rem;
  background: rgba(16,185,129,0.08);
  border: 1px solid rgba(16,185,129,0.2);
  border-radius: var(--radius-sm);
  padding: 0.75rem 1rem;
}
.tg-linked-check {
  width: 28px; height: 28px; border-radius: 50%;
  background: rgba(16,185,129,0.2); color: #34D399;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.85rem; font-weight: 700; flex-shrink: 0;
}
.tg-linked-title { font-size: 0.85rem; font-weight: 600; color: #34D399; }
.tg-linked-user { font-size: 0.75rem; color: var(--text-muted); margin-top: 1px; }
.tg-open-bot-btn { width: 100%; justify-content: center; font-size: 0.82rem; }

/* Steps */
.tg-steps { display: flex; flex-direction: column; }
.tg-step {
  display: flex; gap: 0.65rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.tg-step:last-child { border-bottom: none; padding-bottom: 0; }
.tg-snum {
  width: 20px; height: 20px; border-radius: 50%;
  background: rgba(42,171,238,0.15); color: #2AABEE;
  font-size: 0.68rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 1px;
}
.tg-sbody { flex: 1; display: flex; flex-direction: column; gap: 0.5rem; }
.tg-stext { font-size: 0.8rem; color: var(--text-secondary); line-height: 1.45; }
.tg-sbtn {
  align-self: flex-start;
  padding: 0.28rem 0.65rem;
  font-size: 0.75rem;
  white-space: nowrap;
}
.tg-gen-btn {
  align-self: flex-start;
  font-size: 0.78rem;
  padding: 0.35rem 0.85rem;
}
.tg-code-row {
  display: flex; align-items: center; gap: 0.5rem;
  background: rgba(42,171,238,0.08);
  border: 1px solid rgba(42,171,238,0.25);
  border-radius: var(--radius-sm);
  padding: 0.45rem 0.65rem;
}
.tg-code-row code {
  font-size: 0.82rem; font-weight: 700;
  color: #2AABEE; flex: 1;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.tg-copy-btn {
  background: rgba(42,171,238,0.15);
  border: 1px solid rgba(42,171,238,0.3);
  color: #2AABEE;
  font-size: 0.68rem; font-weight: 600;
  padding: 0.18rem 0.5rem;
  border-radius: var(--radius-sm);
  cursor: pointer; flex-shrink: 0; white-space: nowrap;
  transition: background 0.15s;
}
.tg-copy-btn:hover { background: rgba(42,171,238,0.28); }
.tg-code-note { font-size: 0.68rem; color: var(--text-muted); margin: 0; }

.spinner-sm {
  display: inline-block;
  width: 12px; height: 12px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .nav-links   { display: none; }
  .user-name   { display: none; }
  .btn-logout span { display: none; }
  .btn-logout  { padding: 0.4rem 0.6rem; }
  .header-inner { height: 52px; gap: 0.5rem; padding: 0 1rem; }
  .logo-text { font-size: 1.05rem; }
  .tg-panel { width: calc(100vw - 2rem); right: -0.5rem; }
}
</style>
