<template>
  <div class="auth-page">
    <div class="auth-card glass-card">
      <div class="auth-header">
        <router-link to="/" class="auth-logo">
          <span class="logo-icon">₸</span>
          <span class="logo-text">FinLit</span>
        </router-link>
        <h1>{{ $t('auth.register_title') }}</h1>
      </div>

      <form @submit.prevent="handleRegister" class="auth-form">
        <div class="form-group">
          <label class="form-label-dark">{{ $t('auth.name') }}</label>
          <input
            v-model="form.name"
            type="text"
            class="form-control-dark w-100"
            required
            autocomplete="name"
            id="reg-name"
          />
        </div>

        <div class="form-group">
          <label class="form-label-dark">{{ $t('auth.email') }}</label>
          <input
            v-model="form.email"
            type="email"
            class="form-control-dark w-100"
            placeholder="email@example.com"
            required
            autocomplete="email"
            id="reg-email"
          />
        </div>

        <div class="form-group">
          <label class="form-label-dark">{{ $t('auth.password') }}</label>
          <div class="input-eye-wrap">
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              class="form-control-dark w-100"
              :placeholder="$t('auth.password_placeholder')"
              required
              minlength="6"
              autocomplete="new-password"
              id="reg-password"
            />
            <button type="button" class="eye-btn" @click="showPassword = !showPassword" tabindex="-1">
              <svg v-if="showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
                <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </button>
          </div>
          <!-- Password strength -->
          <div v-if="form.password" class="strength-wrap">
            <div class="strength-bar">
              <div
                class="strength-fill"
                :class="passwordStrength.cls"
                :style="{ width: passwordStrength.pct + '%' }"
              ></div>
            </div>
            <span class="strength-label" :class="passwordStrength.cls">{{ passwordStrength.label }}</span>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label-dark">{{ $t('auth.password_confirm') }}</label>
          <div class="input-eye-wrap">
            <input
              v-model="confirmPassword"
              :type="showConfirm ? 'text' : 'password'"
              class="form-control-dark w-100"
              :class="{ 'input-error': confirmPassword && !passwordsMatch }"
              :placeholder="$t('auth.password_confirm_placeholder')"
              required
              autocomplete="new-password"
              id="reg-confirm"
            />
            <button type="button" class="eye-btn" @click="showConfirm = !showConfirm" tabindex="-1">
              <svg v-if="showConfirm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
                <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </button>
          </div>
          <span v-if="confirmPassword && !passwordsMatch" class="field-error">
            {{ $t('auth.passwords_no_match') }}
          </span>
          <span v-else-if="confirmPassword && passwordsMatch" class="field-ok">
            {{ $t('auth.passwords_match') }}
          </span>
        </div>

        <div v-if="authStore.error" class="error-msg">{{ authStore.error }}</div>
        <div v-if="localError" class="error-msg">{{ localError }}</div>

        <button
          type="submit"
          class="btn-primary-gradient w-100"
          :disabled="authStore.loading || !canSubmit"
          id="reg-submit"
        >
          <span v-if="authStore.loading" class="spinner"></span>
          {{ authStore.loading ? '' : $t('auth.register_btn') }}
        </button>
      </form>

      <div class="auth-footer">
        <span>{{ $t('auth.has_account') }}</span>
        <router-link to="/login">{{ $t('auth.login_link') }}</router-link>
      </div>

      <div class="auth-lang">
        <LanguageSwitcher />
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import LanguageSwitcher from '../components/common/LanguageSwitcher.vue'

const router = useRouter()
const authStore = useAuthStore()
const { locale, t } = useI18n()

const form = reactive({
  name: '',
  email: '',
  password: '',
  currency: 'KZT',
})

const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirm = ref(false)
const localError = ref('')

const passwordsMatch = computed(() => form.password === confirmPassword.value)

const passwordStrength = computed(() => {
  const p = form.password
  if (!p) return { pct: 0, cls: '', label: '' }
  let score = 0
  if (p.length >= 6) score++
  if (p.length >= 10) score++
  if (/[A-Z]/.test(p)) score++
  if (/[0-9]/.test(p)) score++
  if (/[^A-Za-z0-9]/.test(p)) score++
  if (score <= 1) return { pct: 25, cls: 'weak',   label: t('auth.strength_weak') }
  if (score === 2) return { pct: 50, cls: 'fair',   label: t('auth.strength_fair') }
  if (score === 3) return { pct: 75, cls: 'good',   label: t('auth.strength_good') }
  return              { pct: 100, cls: 'strong', label: t('auth.strength_strong') }
})

const canSubmit = computed(() =>
  form.name && form.email && form.password.length >= 6 && passwordsMatch.value
)

async function handleRegister() {
  localError.value = ''
  if (!passwordsMatch.value) {
    localError.value = t('auth.passwords_no_match')
    return
  }
  try {
    await authStore.register({ ...form, preferred_language: locale.value })
    router.push('/dashboard')
  } catch {
    // error handled in store
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.auth-card {
  width: 100%;
  max-width: 460px;
  padding: 2.5rem;
}

.auth-header {
  text-align: center;
  margin-bottom: 2rem;
}

.auth-logo {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  margin-bottom: 1.25rem;
}

.logo-icon {
  width: 44px; height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  display: flex; align-items: center; justify-content: center;
  font-size: 1.25rem; color: white;
}

.logo-text {
  font-size: 1.5rem; font-weight: 800;
  background: linear-gradient(135deg, var(--primary-light), var(--secondary-light));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}

.auth-header h1 {
  font-size: 1.5rem; font-weight: 700; color: var(--text-primary);
}

.auth-form { display: flex; flex-direction: column; gap: 1.1rem; }
.form-group { display: flex; flex-direction: column; gap: 0.35rem; }
.w-100 { width: 100%; }

/* Password eye toggle */
.input-eye-wrap { position: relative; }
.input-eye-wrap .form-control-dark { padding-right: 2.75rem; width: 100%; box-sizing: border-box; }
.eye-btn {
  position: absolute; right: 0.75rem; top: 50%; transform: translateY(-50%);
  background: none; border: none; color: var(--text-muted); cursor: pointer;
  padding: 0; display: flex; align-items: center;
}
.eye-btn svg { width: 18px; height: 18px; }
.eye-btn:hover { color: var(--text-secondary); }

/* Password strength */
.strength-wrap {
  display: flex; align-items: center; gap: 0.6rem; margin-top: 0.35rem;
}
.strength-bar {
  flex: 1; height: 4px; background: rgba(255,255,255,0.08);
  border-radius: 99px; overflow: hidden;
}
.strength-fill {
  height: 100%; border-radius: 99px;
  transition: width 0.3s, background 0.3s;
}
.strength-label { font-size: 0.72rem; font-weight: 600; white-space: nowrap; background: none !important; }

.strength-fill.weak   { background: #EF4444; }
.strength-fill.fair   { background: #F59E0B; }
.strength-fill.good   { background: #3B82F6; }
.strength-fill.strong { background: #10B981; }

.strength-label.weak   { color: #F87171; }
.strength-label.fair   { color: #FCD34D; }
.strength-label.good   { color: #93C5FD; }
.strength-label.strong { color: #34D399; }

/* Field feedback */
.field-error { font-size: 0.78rem; color: var(--danger-light); margin-top: 0.2rem; }
.field-ok    { font-size: 0.78rem; color: #34D399; margin-top: 0.2rem; }

.input-error { border-color: rgba(239, 68, 68, 0.5) !important; }

.error-msg {
  color: var(--danger); font-size: 0.85rem; text-align: center;
  padding: 0.5rem; background: rgba(239, 68, 68, 0.1); border-radius: var(--radius-sm);
}

.auth-footer {
  text-align: center; margin-top: 1.5rem;
  color: var(--text-muted); font-size: 0.9rem;
}
.auth-footer a {
  color: var(--primary-light); text-decoration: none;
  font-weight: 600; margin-left: 0.25rem;
}
.auth-footer a:hover { text-decoration: underline; }

.auth-lang { display: flex; justify-content: center; margin-top: 1.5rem; }

@media (max-width: 480px) {
  .auth-page { padding: 1rem; align-items: flex-start; padding-top: 2rem; }
  .auth-card { padding: 1.5rem; }
}
</style>
