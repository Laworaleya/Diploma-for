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
          <input v-model="form.name" type="text" class="form-control-dark w-100" required id="reg-name" />
        </div>

        <div class="form-group">
          <label class="form-label-dark">{{ $t('auth.email') }}</label>
          <input v-model="form.email" type="email" class="form-control-dark w-100" placeholder="email@example.com" required id="reg-email" />
        </div>

        <div class="form-group">
          <label class="form-label-dark">{{ $t('auth.password') }}</label>
          <input v-model="form.password" type="password" class="form-control-dark w-100" placeholder="Минимум 6 символов" required minlength="6" id="reg-password" />
        </div>

        <div class="form-row">
          <div class="form-group flex-1">
            <label class="form-label-dark">{{ $t('auth.language') }}</label>
            <select v-model="form.preferred_language" class="form-select-dark w-100" id="reg-language">
              <option value="kk">Қазақша</option>
              <option value="ru">Русский</option>
              <option value="en">English</option>
            </select>
          </div>
          <div class="form-group flex-1">
            <label class="form-label-dark">{{ $t('auth.currency') }}</label>
            <select v-model="form.currency" class="form-select-dark w-100" id="reg-currency">
              <option value="KZT">₸ KZT</option>
              <option value="USD">$ USD</option>
              <option value="EUR">€ EUR</option>
              <option value="RUB">₽ RUB</option>
            </select>
          </div>
        </div>

        <div v-if="authStore.error" class="error-msg">
          {{ authStore.error }}
        </div>

        <button type="submit" class="btn-primary-gradient w-100" :disabled="authStore.loading" id="reg-submit">
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
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import LanguageSwitcher from '../components/common/LanguageSwitcher.vue'

const router = useRouter()
const authStore = useAuthStore()
const { locale } = useI18n()

const form = reactive({
  name: '',
  email: '',
  password: '',
  preferred_language: locale.value,
  currency: 'KZT',
})

async function handleRegister() {
  try {
    await authStore.register(form)
    router.push('/dashboard')
  } catch (err) {
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
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  color: white;
}

.logo-text {
  font-size: 1.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, var(--primary-light), var(--secondary-light));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.auth-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.flex-1 {
  flex: 1;
}

.w-100 {
  width: 100%;
}

.error-msg {
  color: var(--danger);
  font-size: 0.85rem;
  text-align: center;
  padding: 0.5rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: var(--radius-sm);
}

.auth-footer {
  text-align: center;
  margin-top: 1.5rem;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.auth-footer a {
  color: var(--primary-light);
  text-decoration: none;
  font-weight: 600;
  margin-left: 0.25rem;
}

.auth-lang {
  display: flex;
  justify-content: center;
  margin-top: 1.5rem;
}
</style>
