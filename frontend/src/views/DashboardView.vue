<template>
  <div class="page-container">

    <!-- Dashboard Header -->
    <div class="dash-header">
      <div>
        <h1 class="page-title">{{ greeting }}, {{ firstName }}</h1>
        <p class="page-subtitle" v-if="activeReport">{{ $t('dashboard.subtitle') }}</p>
        <p class="page-subtitle" v-else>{{ $t('dashboard.subtitle') }}</p>
      </div>
      <div class="dash-header-actions">
        <select
          v-if="reportsStore.reports.length > 1"
          v-model="selectedId"
          class="form-select-dark period-select"
        >
          <option v-for="r in reportsStore.reports" :key="r.id" :value="r.id">{{ r.period }}</option>
        </select>
        <router-link to="/reports" class="btn-primary-gradient btn-add">
          <i class="pi pi-plus"></i> {{ $t('reports.new_report') }}
        </router-link>
      </div>
    </div>

    <!-- KPI Strip -->
    <div class="kpi-strip" v-if="activeReport">
      <!-- Income -->
      <div class="kpi-card kpi-income">
        <div class="kpi-top">
          <div class="kpi-icon kpi-icon-income"><i class="pi pi-arrow-up"></i></div>
          <span v-if="prevReport && incomeTrend !== 0"
            class="kpi-trend-badge"
            :class="incomeTrend > 0 ? 'trend-pos' : 'trend-neg'">
            <i :class="incomeTrend > 0 ? 'pi pi-arrow-up' : 'pi pi-arrow-down'"></i>
            {{ Math.abs(incomeTrend) }}%
          </span>
        </div>
        <div class="kpi-value">{{ formatMoney(activeReport.total_income) }}</div>
        <div class="kpi-label">{{ $t('dashboard.income') }}</div>
        <div class="kpi-accent kpi-accent-income"></div>
      </div>

      <!-- Expense -->
      <div class="kpi-card kpi-expense">
        <div class="kpi-top">
          <div class="kpi-icon kpi-icon-expense"><i class="pi pi-arrow-down"></i></div>
          <span v-if="prevReport && expenseTrend !== 0"
            class="kpi-trend-badge"
            :class="expenseTrend > 0 ? 'trend-neg' : 'trend-pos'">
            <i :class="expenseTrend > 0 ? 'pi pi-arrow-up' : 'pi pi-arrow-down'"></i>
            {{ Math.abs(expenseTrend) }}%
          </span>
        </div>
        <div class="kpi-value">{{ formatMoney(activeReport.total_expense) }}</div>
        <div class="kpi-label">{{ $t('dashboard.expense') }}</div>
        <div class="kpi-accent kpi-accent-expense"></div>
      </div>

      <!-- Surplus / Deficit -->
      <div class="kpi-card" :class="activeReport.surplus >= 0 ? 'kpi-surplus' : 'kpi-deficit'">
        <div class="kpi-top">
          <div class="kpi-icon" :class="activeReport.surplus >= 0 ? 'kpi-icon-surplus' : 'kpi-icon-deficit'">
            <i class="pi pi-wallet"></i>
          </div>
          <span class="kpi-rate-tag" v-if="activeReport.total_income > 0">
            {{ savingsRate }}% rate
          </span>
        </div>
        <div class="kpi-value">{{ formatMoney(activeReport.surplus) }}</div>
        <div class="kpi-label">{{ $t('dashboard.surplus') }}</div>
        <div class="kpi-accent" :class="activeReport.surplus >= 0 ? 'kpi-accent-surplus' : 'kpi-accent-deficit'"></div>
      </div>

      <!-- Financial Health Score -->
      <div class="kpi-card kpi-health">
        <div class="kpi-top">
          <div class="kpi-icon kpi-icon-health"><i class="pi pi-heart"></i></div>
          <span class="kpi-health-badge" :class="healthClass">{{ healthLabel }}</span>
        </div>
        <div class="kpi-value">{{ healthScore }}<span class="kpi-unit"> / 100</span></div>
        <div class="kpi-label">Финансовое здоровье</div>
        <div class="health-mini-bar">
          <div class="health-mini-fill" :class="healthClass" :style="{ width: healthScore + '%' }"></div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!reportsStore.loading" class="empty-hero">
      <div class="empty-hero-icon"><i class="pi pi-chart-pie"></i></div>
      <h3>{{ $t('dashboard.no_reports') }}</h3>
      <p>{{ $t('dashboard.create_first_report') }}</p>
      <router-link to="/reports" class="btn-primary-gradient">{{ $t('reports.new_report') }}</router-link>
    </div>

    <!-- Analytics Grid (Category breakdown + Sidebar) -->
    <div class="analytics-grid" v-if="activeReport">

      <!-- Category Breakdown -->
      <div class="dash-card analytics-main">
        <div class="dash-card-header">
          <h3><i class="pi pi-chart-pie"></i> Распределение расходов</h3>
          <span class="card-total-tag">{{ formatMoney(activeReport.total_expense) }}</span>
        </div>

        <div class="chart-layout" v-if="chartCategories.length">
          <div class="chart-donut-wrap">
            <Doughnut :data="chartData" :options="chartOptions" />
            <div class="donut-center">
              <div class="donut-center-val">{{ formatMoney(activeReport.total_expense) }}</div>
              <div class="donut-center-lbl">расходы</div>
            </div>
          </div>

          <div class="category-bars">
            <div class="cat-row" v-for="(cat, i) in chartCategories" :key="i">
              <div class="cat-row-top">
                <div class="cat-name-group">
                  <span class="cat-dot" :style="{ background: COLORS[i % COLORS.length] }"></span>
                  <span class="cat-name">{{ cat.name }}</span>
                </div>
                <div class="cat-nums">
                  <span class="cat-pct">{{ cat.pct }}%</span>
                  <span class="cat-amount">{{ formatMoney(cat.amount) }}</span>
                </div>
              </div>
              <div class="cat-track">
                <div
                  class="cat-fill"
                  :style="{ width: cat.pct + '%', background: COLORS[i % COLORS.length] }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <div class="card-empty" v-else>
          <i class="pi pi-chart-bar" style="font-size:2.5rem; opacity:0.2"></i>
          <p>Добавьте категории расходов в отчёт</p>
        </div>
      </div>

      <!-- Right Sidebar -->
      <div class="analytics-side">

        <!-- Savings Rate Gauge -->
        <div class="dash-card savings-card">
          <div class="dash-card-header">
            <h3><i class="pi pi-percentage"></i> Норма сбережений</h3>
          </div>
          <div class="gauge-layout">
            <div class="gauge-wrap">
              <svg viewBox="0 0 120 120" class="gauge-svg">
                <circle
                  cx="60" cy="60" r="48"
                  fill="none"
                  stroke="rgba(148,163,184,0.1)"
                  stroke-width="10"
                />
                <circle
                  cx="60" cy="60" r="48"
                  fill="none"
                  :stroke="savingsRate >= 20 ? '#10B981' : savingsRate > 0 ? '#F59E0B' : '#EF4444'"
                  stroke-width="10"
                  :stroke-dasharray="`${Math.max(0, savingsRate) * 3.016} 301.6`"
                  stroke-linecap="round"
                  transform="rotate(-90 60 60)"
                />
              </svg>
              <div class="gauge-text">
                <span class="gauge-pct" :class="savingsRate >= 20 ? 'gauge-good' : savingsRate > 0 ? 'gauge-ok' : 'gauge-bad'">
                  {{ savingsRate }}%
                </span>
                <span class="gauge-lbl">сбережений</span>
              </div>
            </div>
            <div class="gauge-legend">
              <div class="gauge-leg-item">
                <span class="gauge-leg-dot leg-expense"></span>
                <span class="gauge-leg-label">Расходы</span>
                <span class="gauge-leg-val">{{ expenseRate }}%</span>
              </div>
              <div class="gauge-leg-item">
                <span class="gauge-leg-dot" :class="savingsRate >= 20 ? 'leg-savings-good' : 'leg-savings'"></span>
                <span class="gauge-leg-label">Сбережения</span>
                <span class="gauge-leg-val" :class="savingsRate >= 20 ? 'gauge-good' : savingsRate > 0 ? 'gauge-ok' : 'gauge-bad'">
                  {{ savingsRate }}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Smart Insights -->
        <div class="dash-card insights-card" v-if="insights.length">
          <div class="dash-card-header">
            <h3><i class="pi pi-lightbulb"></i> Аналитика</h3>
          </div>
          <div class="insights-list">
            <div
              class="insight-item"
              v-for="(ins, i) in insights"
              :key="i"
              :class="'ins-' + ins.type"
            >
              <i :class="ins.icon"></i>
              <p>{{ ins.text }}</p>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- Secondary Grid: Goals + Recent Reports -->
    <div class="secondary-grid" v-if="activeReport || goalsStore.goals.length">

      <!-- Goals Progress -->
      <div class="dash-card">
        <div class="dash-card-header">
          <h3><i class="pi pi-flag"></i> {{ $t('dashboard.active_goals') }}</h3>
          <router-link to="/goals" class="card-link-btn">
            Все <i class="pi pi-arrow-right"></i>
          </router-link>
        </div>
        <div v-if="goalsStore.activeGoals.length === 0" class="card-empty">
          <i class="pi pi-flag" style="font-size:2rem; opacity:0.2"></i>
          <p>{{ $t('dashboard.no_goals') }}</p>
          <router-link to="/goals" class="btn-glass btn-xs">+ {{ $t('goals.new_goal') }}</router-link>
        </div>
        <div v-else class="goals-stack">
          <div class="g-row" v-for="g in goalsStore.activeGoals.slice(0, 4)" :key="g.id">
            <div class="g-row-top">
              <span class="g-title">{{ g.title }}</span>
              <span class="g-pct" :class="pctClass(g.progress_percent)">{{ g.progress_percent }}%</span>
            </div>
            <div class="progress-bar-custom">
              <div
                class="progress-fill"
                :class="progressFill(g.progress_percent)"
                :style="{ width: Math.min(g.progress_percent, 100) + '%' }"
              ></div>
            </div>
            <div class="g-row-amounts">
              <span>{{ formatMoney(g.current_amount) }}</span>
              <span class="muted">/ {{ formatMoney(g.target_amount) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Reports -->
      <div class="dash-card">
        <div class="dash-card-header">
          <h3><i class="pi pi-history"></i> {{ $t('dashboard.recent_reports') }}</h3>
          <router-link to="/reports" class="card-link-btn">
            Все <i class="pi pi-arrow-right"></i>
          </router-link>
        </div>
        <div v-if="reportsStore.reports.length === 0" class="card-empty">
          <i class="pi pi-file" style="font-size:2rem; opacity:0.2"></i>
          <p>{{ $t('dashboard.no_reports') }}</p>
        </div>
        <div v-else class="reports-stack">
          <div
            v-for="r in reportsStore.reports.slice(0, 5)"
            :key="r.id"
            class="r-row"
            :class="{ 'r-row-active': activeReport?.id === r.id }"
            @click="selectedId = r.id"
          >
            <div class="r-left">
              <div class="r-indicator" :class="r.surplus >= 0 ? 'r-pos' : 'r-neg'"></div>
              <div>
                <div class="r-period">{{ r.period }}</div>
                <div class="r-sub">{{ formatMoney(r.total_income) }} доходов</div>
              </div>
            </div>
            <div class="r-right">
              <div class="r-exp-val">-{{ formatMoney(r.total_expense) }}</div>
              <div :class="r.surplus >= 0 ? 'r-surplus-pos' : 'r-surplus-neg'">
                {{ r.surplus >= 0 ? '+' : '' }}{{ formatMoney(r.surplus) }}
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { useReportsStore } from '../stores/reports'
import { useGoalsStore } from '../stores/goals'
import { useAuthStore } from '../stores/auth'

ChartJS.register(ArcElement, Tooltip, Legend)

const reportsStore = useReportsStore()
const goalsStore = useGoalsStore()
const authStore = useAuthStore()
const selectedId = ref(null)

onMounted(async () => {
  await Promise.all([reportsStore.fetchReports(), goalsStore.fetchGoals()])
})

watch(() => reportsStore.reports, (reports) => {
  if (reports.length > 0 && !selectedId.value) selectedId.value = reports[0].id
}, { immediate: true })

const activeReport = computed(() =>
  reportsStore.reports.find(r => r.id === selectedId.value) || reportsStore.reports[0] || null
)

const prevReport = computed(() => {
  if (!activeReport.value || reportsStore.reports.length < 2) return null
  const idx = reportsStore.reports.findIndex(r => r.id === activeReport.value.id)
  return reportsStore.reports[idx + 1] || null
})

const firstName = computed(() => {
  const name = authStore.user?.name || ''
  return name.split(' ')[0] || name
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return 'Доброе утро'
  if (h < 17) return 'Добрый день'
  return 'Добрый вечер'
})

const currencySymbol = computed(() => {
  const s = { KZT: '₸', USD: '$', EUR: '€', RUB: '₽' }
  return s[authStore.userCurrency] || '₸'
})

function formatMoney(val) {
  if (val == null) return '0 ' + currencySymbol.value
  return new Intl.NumberFormat('ru-RU').format(Math.round(val)) + ' ' + currencySymbol.value
}

function trendPct(curr, prev) {
  if (!prev || prev === 0) return 0
  return Math.round(((curr - prev) / Math.abs(prev)) * 100)
}

const incomeTrend = computed(() =>
  prevReport.value ? trendPct(activeReport.value.total_income, prevReport.value.total_income) : 0
)

const expenseTrend = computed(() =>
  prevReport.value ? trendPct(activeReport.value.total_expense, prevReport.value.total_expense) : 0
)

const savingsRate = computed(() => {
  if (!activeReport.value || !activeReport.value.total_income) return 0
  const rate = (activeReport.value.surplus / activeReport.value.total_income) * 100
  return Math.max(0, Math.min(100, Math.round(rate)))
})

const expenseRate = computed(() => Math.max(0, 100 - savingsRate.value))

const healthScore = computed(() => {
  if (!activeReport.value) return 0
  let score = 0
  if (savingsRate.value >= 20) score += 35
  else if (savingsRate.value > 10) score += 20
  else if (savingsRate.value > 0) score += 10

  const unaccPct = activeReport.value.total_expense > 0
    ? (activeReport.value.unaccounted_expense / activeReport.value.total_expense) * 100
    : 0
  if (unaccPct < 10) score += 25
  else if (unaccPct < 25) score += 12

  if (goalsStore.activeGoals.length > 0) score += 20

  if (activeReport.value.surplus >= 0) score += 20

  return Math.min(100, score)
})

const healthLabel = computed(() => {
  if (healthScore.value >= 70) return 'Отлично'
  if (healthScore.value >= 40) return 'Неплохо'
  return 'Риск'
})

const healthClass = computed(() => {
  if (healthScore.value >= 70) return 'health-good'
  if (healthScore.value >= 40) return 'health-ok'
  return 'health-bad'
})

const COLORS = [
  '#6366F1', '#8B5CF6', '#06B6D4', '#10B981',
  '#F59E0B', '#EF4444', '#EC4899', '#14B8A6',
  '#F97316', '#64748B',
]

const chartCategories = computed(() => {
  if (!activeReport.value) return []
  const cats = activeReport.value.categories || []
  const total = activeReport.value.total_expense || 1
  const unaccounted = activeReport.value.unaccounted_expense || 0
  const result = cats.map(c => ({
    name: c.name,
    amount: c.amount,
    pct: Math.round((c.amount / total) * 100),
  }))
  if (unaccounted > 0) {
    result.push({ name: 'Прочие', amount: unaccounted, pct: Math.round((unaccounted / total) * 100) })
  }
  return result.sort((a, b) => b.amount - a.amount).slice(0, 8)
})

const chartData = computed(() => {
  if (!chartCategories.value.length) return { labels: [], datasets: [] }
  return {
    labels: chartCategories.value.map(c => c.name),
    datasets: [{
      data: chartCategories.value.map(c => c.amount),
      backgroundColor: COLORS.slice(0, chartCategories.value.length),
      borderWidth: 0,
      hoverOffset: 10,
    }],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '72%',
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx) => ` ${ctx.label}: ${new Intl.NumberFormat('ru-RU').format(Math.round(ctx.raw))} ₸`,
      },
    },
  },
}

const insights = computed(() => {
  if (!activeReport.value) return []
  const result = []

  if (activeReport.value.surplus < 0) {
    result.push({ type: 'bad', icon: 'pi pi-exclamation-triangle', text: 'Расходы превышают доходы. Пересмотрите бюджет.' })
  } else if (savingsRate.value >= 20) {
    result.push({ type: 'good', icon: 'pi pi-check-circle', text: `Отличная норма сбережений — ${savingsRate.value}% дохода откладывается.` })
  } else {
    result.push({ type: 'warn', icon: 'pi pi-info-circle', text: `Норма сбережений ${savingsRate.value}%. Рекомендуется 20%+.` })
  }

  const topCat = chartCategories.value[0]
  if (topCat) {
    result.push({ type: 'info', icon: 'pi pi-tag', text: `Наибольшие расходы: «${topCat.name}» — ${topCat.pct}% от трат.` })
  }

  const unaccPct = activeReport.value.total_expense > 0
    ? Math.round((activeReport.value.unaccounted_expense / activeReport.value.total_expense) * 100)
    : 0
  if (unaccPct > 15) {
    result.push({ type: 'warn', icon: 'pi pi-question-circle', text: `${unaccPct}% расходов не распределены по категориям.` })
  }

  return result.slice(0, 3)
})

function pctClass(pct) {
  if (pct >= 75) return 'pct-success'
  if (pct >= 40) return 'pct-warning'
  return 'pct-default'
}

function progressFill(pct) {
  if (pct >= 75) return 'success'
  if (pct >= 40) return 'warning'
  return ''
}
</script>

<style scoped>
/* ── Header ── */
.dash-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1.75rem;
  flex-wrap: wrap;
}

.dash-header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.period-select {
  min-width: 140px;
  font-size: 0.875rem;
}

.btn-add {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 1.1rem;
  font-size: 0.875rem;
  white-space: nowrap;
}

/* ── KPI Strip ── */
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.kpi-card {
  position: relative;
  background: var(--bg-glass);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  overflow: hidden;
  transition: all var(--transition-base);
}

.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* Left accent bar */
.kpi-accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  border-radius: 3px 0 0 3px;
}
.kpi-accent-income  { background: var(--success); }
.kpi-accent-expense { background: var(--danger); }
.kpi-accent-surplus { background: var(--primary); }
.kpi-accent-deficit { background: var(--danger); }

.kpi-income  { border-color: rgba(16, 185, 129, 0.2); }
.kpi-expense { border-color: rgba(239, 68, 68, 0.2); }
.kpi-surplus { border-color: rgba(99, 102, 241, 0.2); }
.kpi-deficit { border-color: rgba(239, 68, 68, 0.2); }
.kpi-health  { border-color: rgba(139, 92, 246, 0.2); }

.kpi-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.85rem;
}

.kpi-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
}

.kpi-icon-income  { background: rgba(16, 185, 129, 0.15); color: var(--success); }
.kpi-icon-expense { background: rgba(239, 68, 68, 0.15);  color: var(--danger); }
.kpi-icon-surplus { background: rgba(99, 102, 241, 0.15); color: var(--primary-light); }
.kpi-icon-deficit { background: rgba(239, 68, 68, 0.15);  color: var(--danger); }
.kpi-icon-health  { background: rgba(139, 92, 246, 0.15); color: var(--secondary-light); }

.kpi-trend-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  padding: 0.2rem 0.5rem;
  border-radius: 20px;
  font-size: 0.72rem;
  font-weight: 600;
}
.trend-pos { background: rgba(16, 185, 129, 0.15); color: var(--success-light); }
.trend-neg { background: rgba(239, 68, 68, 0.15);  color: var(--danger-light); }

.kpi-rate-tag {
  font-size: 0.72rem;
  color: var(--primary-light);
  background: rgba(99, 102, 241, 0.1);
  border-radius: 20px;
  padding: 0.2rem 0.5rem;
  font-weight: 600;
}

.kpi-health-badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: 20px;
}
.health-good { background: rgba(16, 185, 129, 0.15); color: var(--success-light); }
.health-ok   { background: rgba(245, 158, 11, 0.15); color: var(--warning-light); }
.health-bad  { background: rgba(239, 68, 68, 0.15);  color: var(--danger-light); }

.kpi-value {
  font-size: 1.3rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.2;
  margin-bottom: 0.2rem;
}

.kpi-unit {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-muted);
}

.kpi-label {
  font-size: 0.72rem;
  color: var(--text-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.health-mini-bar {
  height: 4px;
  background: rgba(148, 163, 184, 0.1);
  border-radius: 2px;
  margin-top: 0.6rem;
  overflow: hidden;
}

.health-mini-fill {
  height: 100%;
  border-radius: 2px;
  transition: width var(--transition-slow);
}
.health-good .health-mini-fill,
.health-mini-fill.health-good { background: var(--success); }
.health-mini-fill.health-ok   { background: var(--warning); }
.health-mini-fill.health-bad  { background: var(--danger); }

/* ── Empty Hero ── */
.empty-hero {
  text-align: center;
  padding: 4rem 1.5rem;
  color: var(--text-muted);
}

.empty-hero-icon {
  font-size: 3.5rem;
  opacity: 0.2;
  margin-bottom: 1rem;
}

.empty-hero h3 {
  color: var(--text-secondary);
  font-size: 1.2rem;
  margin-bottom: 0.5rem;
}

.empty-hero p {
  margin-bottom: 1.5rem;
  font-size: 0.95rem;
}

/* ── Analytics Grid ── */
.analytics-grid {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 1.25rem;
  margin-bottom: 1.25rem;
}

.analytics-side {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* ── Dash Card (shared) ── */
.dash-card {
  background: var(--bg-glass);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 1.25rem;
}

.dash-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.1rem;
}

.dash-card-header h3 {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.dash-card-header h3 i {
  color: var(--primary-light);
}

.card-total-tag {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  padding: 0.25rem 0.6rem;
}

/* ── Chart Layout ── */
.chart-layout {
  display: flex;
  gap: 1.5rem;
  align-items: flex-start;
}

.chart-donut-wrap {
  position: relative;
  flex: 0 0 200px;
  height: 200px;
}

.donut-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.donut-center-val {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-primary);
  text-align: center;
  line-height: 1.2;
  max-width: 90px;
}

.donut-center-lbl {
  font-size: 0.65rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* ── Category Bars ── */
.category-bars {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
  overflow: hidden;
}

.cat-row {}

.cat-row-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.3rem;
}

.cat-name-group {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  min-width: 0;
}

.cat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.cat-name {
  font-size: 0.82rem;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.cat-nums {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-shrink: 0;
}

.cat-pct {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-secondary);
}

.cat-amount {
  font-size: 0.78rem;
  color: var(--text-muted);
  min-width: 80px;
  text-align: right;
}

.cat-track {
  height: 5px;
  background: rgba(148, 163, 184, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.cat-fill {
  height: 100%;
  border-radius: 3px;
  opacity: 0.85;
  transition: width var(--transition-slow);
}

/* ── Card Empty ── */
.card-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 2rem 1rem;
  color: var(--text-muted);
  text-align: center;
}

.card-empty p {
  margin: 0;
  font-size: 0.9rem;
}

/* ── Savings Gauge ── */
.savings-card { padding: 1.25rem; }

.gauge-layout {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.gauge-wrap {
  position: relative;
  flex: 0 0 110px;
  height: 110px;
}

.gauge-svg {
  width: 110px;
  height: 110px;
}

.gauge-text {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.gauge-pct {
  font-size: 1.3rem;
  font-weight: 800;
  line-height: 1;
}

.gauge-lbl {
  font-size: 0.62rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-top: 0.2rem;
}

.gauge-good { color: var(--success); }
.gauge-ok   { color: var(--warning); }
.gauge-bad  { color: var(--danger); }

.gauge-legend {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.gauge-leg-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.gauge-leg-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.leg-expense { background: var(--danger); }
.leg-savings { background: var(--warning); }
.leg-savings-good { background: var(--success); }

.gauge-leg-label {
  flex: 1;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.gauge-leg-val {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-primary);
}

/* ── Insights ── */
.insights-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.insight-item {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.65rem 0.75rem;
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  line-height: 1.5;
}

.insight-item i {
  margin-top: 0.1rem;
  flex-shrink: 0;
  font-size: 0.9rem;
}

.insight-item p { margin: 0; }

.ins-good { background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2); color: var(--success-light); }
.ins-warn { background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.2); color: var(--warning-light); }
.ins-bad  { background: rgba(239, 68, 68, 0.08);  border: 1px solid rgba(239, 68, 68, 0.2);  color: var(--danger-light); }
.ins-info { background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.2); color: var(--primary-light); }

/* ── Secondary Grid ── */
.secondary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
}

/* ── Card Link Button ── */
.card-link-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.8rem;
  color: var(--text-muted);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.card-link-btn:hover {
  color: var(--primary-light);
}

/* ── Goals Stack ── */
.goals-stack {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.g-row {
  padding: 0.75rem;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
}

.g-row-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.g-title {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 70%;
}

.g-pct {
  font-weight: 700;
  font-size: 0.82rem;
}

.pct-success { color: var(--success); }
.pct-warning { color: var(--warning); }
.pct-default { color: var(--primary-light); }

.g-row-amounts {
  display: flex;
  gap: 0.4rem;
  font-size: 0.77rem;
  color: var(--text-secondary);
  margin-top: 0.35rem;
}

.muted { color: var(--text-muted); }

/* ── Reports Stack ── */
.reports-stack {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.r-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.65rem 0.75rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid transparent;
  gap: 0.75rem;
}

.r-row:hover { background: var(--bg-tertiary); }

.r-row-active {
  background: rgba(99, 102, 241, 0.08);
  border-color: rgba(99, 102, 241, 0.2);
}

.r-left {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  min-width: 0;
}

.r-indicator {
  width: 3px;
  height: 36px;
  border-radius: 3px;
  flex-shrink: 0;
}

.r-pos { background: var(--success); }
.r-neg { background: var(--danger); }

.r-period {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--text-primary);
}

.r-sub {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.1rem;
}

.r-right {
  text-align: right;
  flex-shrink: 0;
}

.r-exp-val {
  font-size: 0.82rem;
  color: var(--danger-light);
  font-weight: 500;
}

.r-surplus-pos {
  font-size: 0.82rem;
  color: var(--success-light);
  font-weight: 600;
}

.r-surplus-neg {
  font-size: 0.82rem;
  color: var(--danger-light);
  font-weight: 600;
}

/* ── Responsive ── */
@media (max-width: 1280px) {
  .analytics-grid {
    grid-template-columns: 1fr 300px;
  }
}

@media (max-width: 1024px) {
  .kpi-strip {
    grid-template-columns: repeat(2, 1fr);
  }

  .analytics-grid {
    grid-template-columns: 1fr;
  }

  .analytics-side {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .dash-header {
    flex-direction: column;
    gap: 0.75rem;
  }

  .dash-header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .analytics-side {
    grid-template-columns: 1fr;
  }

  .secondary-grid {
    grid-template-columns: 1fr;
  }

  .chart-layout {
    flex-direction: column;
  }

  .chart-donut-wrap {
    flex: none;
    width: 180px;
    height: 180px;
    margin: 0 auto;
  }
}

@media (max-width: 480px) {
  .kpi-strip {
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }

  .kpi-value {
    font-size: 1.05rem;
  }

  .kpi-card {
    padding: 1rem;
  }
}
</style>
