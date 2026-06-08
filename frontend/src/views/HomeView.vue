<template>
  <div class="home-page">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-content">
        <div class="hero-eyebrow">{{ $t('home.eyebrow') }}</div>
        <h1 class="hero-title">{{ $t('home.hero_title') }}</h1>
        <p class="hero-subtitle">{{ $t('home.hero_subtitle') }}</p>

        <div class="hero-actions">
          <router-link
            :to="authStore.isAuthenticated ? '/dashboard' : '/register'"
            class="btn-primary-gradient btn-lg"
          >
            {{ $t('home.get_started') }}
            <span class="btn-arrow">→</span>
          </router-link>
          <router-link v-if="!authStore.isAuthenticated" to="/login" class="btn-ghost">
            {{ $t('nav.login') }}
          </router-link>
        </div>

        <div class="hero-stats">
          <div class="hero-stat">
            <span class="stat-number">3</span>
            <span class="stat-text">{{ $t('home.stat_languages') }}</span>
          </div>
          <div class="hero-stat-divider"></div>
          <div class="hero-stat">
            <span class="stat-number">24/7</span>
            <span class="stat-text">{{ $t('home.stat_availability') }}</span>
          </div>
          <div class="hero-stat-divider"></div>
          <div class="hero-stat">
            <span class="stat-number">AI</span>
            <span class="stat-text">{{ $t('home.stat_analysis') }}</span>
          </div>
        </div>
      </div>

      <!-- Dashboard preview mock -->
      <div class="hero-visual">
        <div class="glow-blob blob-1"></div>
        <div class="glow-blob blob-2"></div>

        <div class="mock-card glass-card">
          <div class="mock-card-header">
            <div class="mock-card-title">{{ $t('home.mock_title') }}</div>
            <div class="mock-period">{{ mockPeriod }}</div>
          </div>

          <div class="mock-balance">
            <div class="mock-balance-label">{{ $t('home.mock_balance') }}</div>
            <div class="mock-balance-amount">534 950 <span class="mock-currency">₸</span></div>
          </div>

          <div class="mock-progress-wrap">
            <div class="mock-progress-meta">
              <span>{{ $t('home.mock_budget_used') }}</span>
              <span class="mock-pct">44%</span>
            </div>
            <div class="mock-progress-track">
              <div class="mock-progress-fill" style="width: 44%"></div>
            </div>
          </div>

          <div class="mock-chart">
            <div v-for="(h, i) in chartBars" :key="i"
              class="mock-bar"
              :class="{ active: i === chartBars.length - 1 }"
              :style="{ height: h + '%' }"
            ></div>
          </div>

          <div class="mock-cats">
            <div class="mock-cat-row" v-for="(cat, i) in mockCategories" :key="i">
              <span class="mock-cat-dot" :style="{ background: cat.color }"></span>
              <span class="mock-cat-name">{{ cat.name }}</span>
              <div class="mock-cat-bar-track">
                <div class="mock-cat-bar-fill" :style="{ width: cat.pct + '%', background: cat.color }"></div>
              </div>
              <span class="mock-cat-pct">{{ cat.pct }}%</span>
            </div>
          </div>
        </div>

        <!-- Floating chips -->
        <div class="chip chip-1">
          <span class="chip-dot chip-dot--green"></span>
          <span>{{ $t('home.chip_balance') }}</span>
        </div>
        <div class="chip chip-2">
          <span class="chip-dot chip-dot--purple"></span>
          <span>{{ $t('home.chip_ai') }}</span>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="features">
      <div class="features-grid">
        <div class="feature-card" v-for="(f, i) in features" :key="i">
          <div class="feature-icon-wrap" :style="{ '--fg': f.color }">
            <component :is="f.icon" class="feature-svg" />
          </div>
          <h3>{{ $t(f.titleKey) }}</h3>
          <p>{{ $t(f.descKey) }}</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, defineComponent, h } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'

const { t, locale } = useI18n()
const authStore = useAuthStore()

const mockPeriod = computed(() => {
  const tag = { ru: 'ru-RU', en: 'en-US', kk: 'kk-KZ' }[locale.value] || 'ru-RU'
  const label = new Date().toLocaleString(tag, { month: 'long', year: 'numeric' })
  return label.charAt(0).toUpperCase() + label.slice(1)
})

const chartBars = [28, 45, 35, 60, 50, 72, 88]
const mockCategories = computed(() => [
  { name: t('tracker.categories.food'), pct: 42, color: '#6366F1' },
  { name: t('tracker.categories.transport'), pct: 28, color: '#8B5CF6' },
  { name: t('tracker.categories.other'), pct: 30, color: '#06B6D4' },
])

// Inline SVG icon components
const IconChart = defineComponent({
  render: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('line', { x1: '18', y1: '20', x2: '18', y2: '10' }),
    h('line', { x1: '12', y1: '20', x2: '12', y2: '4' }),
    h('line', { x1: '6', y1: '20', x2: '6', y2: '14' }),
    h('line', { x1: '2', y1: '20', x2: '22', y2: '20' }),
  ])
})

const IconBrain = defineComponent({
  render: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('path', { d: 'M12 2a4 4 0 0 1 4 4v1a4 4 0 0 1 0 8v1a4 4 0 0 1-8 0v-1a4 4 0 0 1 0-8V6a4 4 0 0 1 4-4z' }),
    h('path', { d: 'M8 10h.01M16 10h.01M8 14h.01M16 14h.01M12 10v4' }),
  ])
})

const IconTarget = defineComponent({
  render: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('circle', { cx: '12', cy: '12', r: '10' }),
    h('circle', { cx: '12', cy: '12', r: '6' }),
    h('circle', { cx: '12', cy: '12', r: '2' }),
  ])
})

const features = [
  { icon: IconChart, color: '#6366F1', titleKey: 'home.feature1_title', descKey: 'home.feature1_desc' },
  { icon: IconBrain, color: '#10B981', titleKey: 'home.feature2_title', descKey: 'home.feature2_desc' },
  { icon: IconTarget, color: '#F59E0B', titleKey: 'home.feature3_title', descKey: 'home.feature3_desc' },
]

</script>

<style scoped>
.home-page { overflow: hidden; }

/* ── Hero ─────────────────────────────────────────────────────────────────── */
.hero {
  max-width: 1200px;
  margin: 0 auto;
  padding: 5rem 1.5rem 4rem;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
  min-height: 80vh;
}

.hero-eyebrow {
  display: inline-block;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: 20px;
  padding: 0.3rem 1rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--primary-light);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 1.25rem;
}

.hero-title {
  font-size: 3.25rem;
  font-weight: 800;
  line-height: 1.15;
  margin-bottom: 1.25rem;
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--primary-light) 55%, var(--secondary-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.05rem;
  color: var(--text-secondary);
  line-height: 1.75;
  margin-bottom: 2.25rem;
  max-width: 480px;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 3rem;
}

.btn-lg {
  padding: 0.85rem 2rem;
  font-size: 1rem;
  gap: 0.5rem;
}

.btn-arrow { transition: transform 0.2s; }
.btn-lg:hover .btn-arrow { transform: translateX(4px); }

.btn-ghost {
  padding: 0.85rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: var(--radius-sm);
  transition: color 0.2s;
}
.btn-ghost:hover { color: var(--text-primary); }

.hero-stats {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}
.hero-stat { display: flex; flex-direction: column; }
.stat-number { font-size: 1.4rem; font-weight: 800; color: var(--primary-light); }
.stat-text { font-size: 0.75rem; color: var(--text-muted); font-weight: 500; }
.hero-stat-divider { width: 1px; height: 36px; background: var(--border-color); }

/* ── Dashboard preview ────────────────────────────────────────────────────── */
.hero-visual {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 460px;
}

.glow-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  pointer-events: none;
  z-index: 0;
}
.blob-1 {
  width: 280px; height: 280px;
  background: rgba(99, 102, 241, 0.18);
  top: -20px; right: 0;
}
.blob-2 {
  width: 200px; height: 200px;
  background: rgba(139, 92, 246, 0.12);
  bottom: 20px; left: 20px;
}

.mock-card {
  position: relative;
  z-index: 1;
  width: 320px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
}

.mock-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.mock-card-title { font-size: 0.82rem; font-weight: 700; color: var(--text-secondary); }
.mock-period { font-size: 0.75rem; color: var(--text-muted); }

.mock-balance-label { font-size: 0.72rem; color: var(--text-muted); margin-bottom: 0.2rem; }
.mock-balance-amount {
  font-size: 1.75rem; font-weight: 800;
  background: linear-gradient(135deg, var(--primary-light), var(--secondary-light));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.mock-currency { font-size: 1.1rem; }

.mock-progress-meta {
  display: flex; justify-content: space-between;
  font-size: 0.72rem; color: var(--text-muted); margin-bottom: 0.4rem;
}
.mock-pct { color: var(--primary-light); font-weight: 700; }
.mock-progress-track {
  height: 6px; background: rgba(255,255,255,0.06); border-radius: 99px; overflow: hidden;
}
.mock-progress-fill {
  height: 100%; border-radius: 99px;
  background: linear-gradient(90deg, var(--primary), var(--secondary));
}

.mock-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 52px;
  padding: 0 2px;
}
.mock-bar {
  flex: 1;
  border-radius: 3px 3px 0 0;
  background: rgba(99, 102, 241, 0.25);
  transition: background 0.2s;
}
.mock-bar.active { background: linear-gradient(180deg, var(--primary-light), var(--primary)); }

.mock-cats { display: flex; flex-direction: column; gap: 0.55rem; }
.mock-cat-row { display: flex; align-items: center; gap: 0.5rem; font-size: 0.75rem; }
.mock-cat-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.mock-cat-name { color: var(--text-secondary); width: 70px; }
.mock-cat-bar-track { flex: 1; height: 4px; background: rgba(255,255,255,0.06); border-radius: 99px; overflow: hidden; }
.mock-cat-bar-fill { height: 100%; border-radius: 99px; }
.mock-cat-pct { color: var(--text-muted); width: 28px; text-align: right; }

/* Floating chips */
.chip {
  position: absolute;
  z-index: 2;
  background: var(--bg-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 0.4rem 0.85rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 0.4rem;
  white-space: nowrap;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}
.chip-1 { top: 30px; right: -10px; animation: chipFloat 5s ease-in-out infinite; }
.chip-2 { bottom: 55px; left: -10px; animation: chipFloat 5s ease-in-out infinite 2.5s; }

.chip-dot {
  width: 7px; height: 7px; border-radius: 50; flex-shrink: 0;
}
.chip-dot--green { background: #10B981; box-shadow: 0 0 6px #10B981; }
.chip-dot--purple { background: #8B5CF6; box-shadow: 0 0 6px #8B5CF6; }

@keyframes chipFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

/* ── Features ─────────────────────────────────────────────────────────────── */
.features {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 1.5rem 5rem;
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
  transition: all 0.25s;
}
.feature-card:hover {
  transform: translateY(-4px);
  border-color: var(--border-glow);
  box-shadow: var(--shadow-glow);
}

.feature-icon-wrap {
  width: 48px; height: 48px;
  border-radius: var(--radius-sm);
  background: color-mix(in srgb, var(--fg) 15%, transparent);
  border: 1px solid color-mix(in srgb, var(--fg) 25%, transparent);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 1.25rem;
  color: var(--fg);
}

.feature-svg { width: 22px; height: 22px; }

.feature-card h3 {
  font-size: 1.05rem; font-weight: 700;
  margin-bottom: 0.5rem; color: var(--text-primary);
}
.feature-card p {
  color: var(--text-secondary); font-size: 0.9rem; line-height: 1.65;
}

/* ── Responsive ─────────────────────────────────────────────────────────────*/
@media (max-width: 900px) {
  .hero {
    grid-template-columns: 1fr;
    padding: 3rem 1.5rem 2rem;
    min-height: auto;
    gap: 2rem;
  }
  .hero-title { font-size: 2.25rem; }
  .hero-visual { height: 340px; }
  .mock-card { width: 280px; }
  .features-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 600px) {
  .hero-visual { display: none; }
  .features-grid { grid-template-columns: 1fr; }
}
</style>
