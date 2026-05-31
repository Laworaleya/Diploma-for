<template>
  <div class="home-page">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <h1 class="hero-title">
          {{ $t('home.hero_title') }}
        </h1>
        <p class="hero-subtitle">{{ $t('home.hero_subtitle') }}</p>
        <div class="hero-actions">
          <router-link
            :to="authStore.isAuthenticated ? '/dashboard' : '/register'"
            class="btn-primary-gradient btn-lg"
          >
            {{ $t('home.get_started') }}
            <span class="btn-arrow">→</span>
          </router-link>
        </div>

        <!-- Stats -->
        <div class="hero-stats">
          <div class="hero-stat">
            <span class="stat-number">3</span>
            <span class="stat-text">{{ langLabels.languages }}</span>
          </div>
          <div class="hero-stat-divider"></div>
          <div class="hero-stat">
            <span class="stat-number">24/7</span>
            <span class="stat-text">{{ langLabels.availability }}</span>
          </div>
        </div>
      </div>

      <!-- Floating decoration -->
      <div class="hero-visual">
        <div class="float-card card-1">
          <span class="float-icon">📊</span>
          <span class="float-label">Analytics</span>
        </div>
        <div class="float-card card-2">
          <span class="float-icon">🎯</span>
          <span class="float-label">Goals</span>
        </div>
        <div class="float-card card-4">
          <span class="float-icon">₸</span>
          <span class="float-label">Budget</span>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features">
      <div class="features-grid">
        <div class="feature-card" v-for="(feature, i) in features" :key="i">
          <div class="feature-icon" :style="{ background: feature.gradient }">
            {{ feature.icon }}
          </div>
          <h3>{{ $t(feature.titleKey) }}</h3>
          <p>{{ $t(feature.descKey) }}</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'

const { locale } = useI18n()
const authStore = useAuthStore()

const features = [
  {
    icon: '📊',
    titleKey: 'home.feature1_title',
    descKey: 'home.feature1_desc',
    gradient: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.2))',
  },
  {
    icon: '💡',
    titleKey: 'home.feature2_title',
    descKey: 'home.feature2_desc',
    gradient: 'linear-gradient(135deg, rgba(16,185,129,0.2), rgba(6,182,212,0.2))',
  },
  {
    icon: '🎯',
    titleKey: 'home.feature3_title',
    descKey: 'home.feature3_desc',
    gradient: 'linear-gradient(135deg, rgba(245,158,11,0.2), rgba(239,68,68,0.2))',
  },
]

const langLabels = computed(() => {
  const l = locale.value
  return {
    languages: l === 'kk' ? 'Тіл' : l === 'ru' ? 'Языка' : 'Languages',
    availability: l === 'kk' ? 'Қолжетімді' : l === 'ru' ? 'Доступно' : 'Available',
  }
})
</script>

<style scoped>
.home-page {
  overflow: hidden;
}

/* Hero */
.hero {
  max-width: 1200px;
  margin: 0 auto;
  padding: 5rem 1.5rem 4rem;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
  align-items: center;
  min-height: 80vh;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 20px;
  padding: 0.35rem 1rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--primary-light);
  margin-bottom: 1.5rem;
}

.badge-icon {
  font-size: 1rem;
}

.hero-title {
  font-size: 3.25rem;
  font-weight: 800;
  line-height: 1.15;
  margin-bottom: 1.25rem;
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--primary-light) 50%, var(--secondary-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.1rem;
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: 2rem;
  max-width: 520px;
}

.hero-actions {
  margin-bottom: 3rem;
}

.btn-lg {
  padding: 0.85rem 2rem;
  font-size: 1.05rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-arrow {
  transition: transform var(--transition-base);
}

.btn-lg:hover .btn-arrow {
  transform: translateX(4px);
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.hero-stat {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--primary-light);
}

.stat-text {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 500;
}

.hero-stat-divider {
  width: 1px;
  height: 40px;
  background: var(--border-color);
}

/* Floating visual */
.hero-visual {
  position: relative;
  height: 400px;
}

.float-card {
  position: absolute;
  background: var(--bg-glass);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 1.25rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  animation: float 6s ease-in-out infinite;
  box-shadow: var(--shadow-md);
}

.float-icon {
  font-size: 1.5rem;
}

.float-label {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.95rem;
}

.card-1 { top: 10%; left: 15%; animation-delay: 0s; }
.card-2 { top: 35%; right: 10%; animation-delay: 1.5s; }
.card-3 { bottom: 25%; left: 5%; animation-delay: 3s; }
.card-4 { bottom: 5%; right: 20%; animation-delay: 4.5s; }

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-15px); }
}

/* Features */
.features {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1.5rem 5rem;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.feature-card {
  background: var(--bg-glass);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 2rem;
  transition: all var(--transition-base);
}

.feature-card:hover {
  transform: translateY(-4px);
  border-color: var(--border-glow);
  box-shadow: var(--shadow-glow);
}

.feature-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-bottom: 1.25rem;
}

.feature-card h3 {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
}

.feature-card p {
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .hero {
    grid-template-columns: 1fr;
    padding: 3rem 1.5rem 2rem;
    min-height: auto;
  }
  .hero-title {
    font-size: 2.25rem;
  }
  .hero-visual {
    display: none;
  }
  .features-grid {
    grid-template-columns: 1fr;
  }
}
</style>
