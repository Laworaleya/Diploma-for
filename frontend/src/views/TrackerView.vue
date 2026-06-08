<template>
  <div class="tracker-page">

    <!-- Header row -->
    <div class="page-header">
      <div>
        <h1 class="page-title">{{ $t('tracker.title') }}</h1>
        <p class="page-subtitle">{{ periodLabel }}</p>
      </div>
      <div class="header-controls">
        <button class="btn-action btn-expense" @click="openModal('expense')">{{ $t('tracker.expense_btn') }}</button>
        <button class="btn-action btn-income" @click="openModal('income')">{{ $t('tracker.income_btn') }}</button>
        <button class="btn-action btn-budget" @click="openModal('budget')">{{ $t('tracker.budget_btn') }}</button>
        <select v-model="selectedPeriod" class="period-select" @change="loadAll">
          <option v-for="p in availablePeriods" :key="p.value" :value="p.value">{{ p.label }}</option>
        </select>
      </div>
    </div>

    <!-- ── Expense modal ──────────────────────────────────────────────────── -->
    <Teleport to="body">
      <div v-if="modal === 'expense'" class="modal-backdrop" @click.self="modal = null">
        <div class="modal-card glass-card">
          <div class="modal-header">
            <h3>{{ $t('tracker.add_expense_title') }}</h3>
            <button class="modal-close" @click="modal = null">✕</button>
          </div>

          <div v-if="!expenseStep" class="modal-body">
            <p class="modal-label">{{ $t('tracker.select_category') }}</p>
            <div class="category-grid">
              <button
                v-for="cat in CATEGORIES"
                :key="cat"
                class="cat-btn"
                :class="{ active: expenseForm.category === cat }"
                @click="expenseForm.category = cat"
              >{{ cat }}</button>
            </div>
            <div class="custom-cat-row">
              <input
                v-model="customCategory"
                class="form-control-dark"
                :placeholder="$t('tracker.custom_category')"
                @input="expenseForm.category = customCategory"
              />
            </div>
            <button
              class="btn-primary-gradient w-100 mt"
              :disabled="!expenseForm.category"
              @click="expenseStep = true"
            >{{ $t('tracker.next') }}</button>
          </div>

          <div v-else class="modal-body">
            <p class="modal-label">{{ $t('tracker.select_category') }}: <strong>{{ expenseForm.category }}</strong></p>
            <p class="modal-label" style="margin-top:1rem">{{ $t('tracker.expense_amount_label') }}</p>
            <input
              v-model.number="expenseForm.amount"
              type="number"
              min="1"
              class="form-control-dark amount-input"
              placeholder="0"
              autofocus
              @keyup.enter="submitExpense"
            />
            <div v-if="actionError" class="action-error">{{ actionError }}</div>
            <div class="modal-actions">
              <button class="btn-glass" @click="expenseStep = false">{{ $t('tracker.back') }}</button>
              <button
                class="btn-primary-gradient"
                :disabled="!expenseForm.amount || actionLoading"
                @click="submitExpense"
              >
                <span v-if="actionLoading" class="spinner"></span>
                {{ actionLoading ? '' : $t('tracker.save') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Income modal ─────────────────────────────────────────────────── -->
      <div v-if="modal === 'income'" class="modal-backdrop" @click.self="modal = null">
        <div class="modal-card glass-card">
          <div class="modal-header">
            <h3>{{ $t('tracker.add_income_title') }}</h3>
            <button class="modal-close" @click="modal = null">✕</button>
          </div>
          <div class="modal-body">
            <p class="modal-label">{{ $t('tracker.income_amount_label') }}</p>
            <input
              v-model.number="incomeForm.amount"
              type="number"
              min="1"
              class="form-control-dark amount-input"
              placeholder="0"
              autofocus
              @keyup.enter="submitIncome"
            />
            <p class="modal-note">{{ $t('tracker.income_note') }}</p>
            <div v-if="actionError" class="action-error">{{ actionError }}</div>
            <div class="modal-actions">
              <button class="btn-glass" @click="modal = null">{{ $t('tracker.cancel') }}</button>
              <button
                class="btn-success-gradient"
                :disabled="!incomeForm.amount || actionLoading"
                @click="submitIncome"
              >
                <span v-if="actionLoading" class="spinner"></span>
                {{ actionLoading ? '' : $t('tracker.save') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Budget modal ─────────────────────────────────────────────────── -->
      <div v-if="modal === 'budget'" class="modal-backdrop" @click.self="modal = null">
        <div class="modal-card glass-card">
          <div class="modal-header">
            <h3>{{ $t('tracker.monthly_budget_title') }}</h3>
            <button class="modal-close" @click="modal = null">✕</button>
          </div>
          <div class="modal-body">
            <p class="modal-label">
              {{ $t('tracker.budget_current') }}
              <strong>{{ summary ? fmt(summary.budget.monthly_limit) : '—' }}</strong>
            </p>
            <p class="modal-label" style="margin-top:1rem">{{ $t('tracker.budget_new_limit') }}</p>
            <input
              v-model.number="budgetForm.amount"
              type="number"
              min="1"
              class="form-control-dark amount-input"
              placeholder="0"
              autofocus
              @keyup.enter="submitBudget"
            />
            <p class="modal-note">{{ $t('tracker.budget_limit_note') }}</p>
            <div v-if="actionError" class="action-error">{{ actionError }}</div>
            <div class="modal-actions">
              <button class="btn-glass" @click="modal = null">{{ $t('tracker.cancel') }}</button>
              <button
                class="btn-primary-gradient"
                :disabled="!budgetForm.amount || actionLoading"
                @click="submitBudget"
              >
                <span v-if="actionLoading" class="spinner"></span>
                {{ actionLoading ? '' : $t('tracker.save') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Loading skeleton -->
    <template v-if="loading">
      <div class="kpi-grid">
        <div v-for="i in 4" :key="i" class="kpi-card skeleton-card"></div>
      </div>
      <div class="charts-grid">
        <div v-for="i in 3" :key="i" class="chart-card skeleton-card" style="height:280px"></div>
      </div>
    </template>

    <!-- Onboarding / link flow (no data yet) -->
    <div v-else-if="!hasData" class="onboarding-wrap">

      <!-- Welcome card -->
      <div class="glass-card onboarding-card">
        <div class="onboarding-header">
          <div>
            <h2 class="onboarding-title">{{ $t('tracker.onboarding_title') }}</h2>
            <p class="onboarding-sub">{{ $t('tracker.onboarding_subtitle') }}</p>
          </div>
        </div>

        <div class="onboarding-ways">
          <!-- Way 1: use directly -->
          <div class="onboarding-way">
            <div class="way-num">1</div>
            <div class="way-body">
              <div class="way-title">{{ $t('tracker.way1_title') }}</div>
              <div class="way-desc">{{ $t('tracker.way1_desc') }}</div>
              <div class="way-actions">
                <button class="btn-action btn-expense" @click="openModal('expense')">{{ $t('tracker.way1_add_expense') }}</button>
                <button class="btn-action btn-income"  @click="openModal('income')">{{ $t('tracker.way1_add_income') }}</button>
                <button class="btn-action btn-budget"  @click="openModal('budget')">{{ $t('tracker.way1_set_budget') }}</button>
              </div>
            </div>
          </div>

          <div class="onboarding-divider">{{ $t('tracker.or') }}</div>

          <!-- Way 2: link Telegram -->
          <div class="onboarding-way">
            <div class="way-num">2</div>
            <div class="way-body">
              <div class="way-title">{{ $t('tracker.way2_title') }}</div>
              <div class="way-desc">{{ $t('tracker.way2_desc') }}</div>

              <div class="ob-tg-steps">
                <!-- Step 1 -->
                <div class="ob-tg-step">
                  <span class="ob-tg-num">1</span>
                  <div class="ob-tg-body">
                    <span class="ob-tg-text">Открой бота в Telegram</span>
                    <a :href="telegramUrl" target="_blank" class="btn-glass ob-tg-btn">Открыть бота</a>
                  </div>
                </div>

                <!-- Step 2 -->
                <div class="ob-tg-step">
                  <span class="ob-tg-num">2</span>
                  <div class="ob-tg-body">
                    <span class="ob-tg-text">Нажми /start и введи месячный бюджет — выполни первую команду которую просит бот. Только после этого вставь код ниже.</span>
                  </div>
                </div>

                <!-- Step 3 -->
                <div class="ob-tg-step">
                  <span class="ob-tg-num">3</span>
                  <div class="ob-tg-body">
                    <span class="ob-tg-text">Вставь этот код в бот</span>
                    <button v-if="!linkCode" class="btn-primary-gradient ob-tg-gen-btn" :disabled="linkLoading" @click="getlinkCode">
                      <span v-if="linkLoading" class="spinner"></span>
                      {{ linkLoading ? '' : 'Получить код' }}
                    </button>
                    <div v-else class="ob-tg-code-row">
                      <code>/link {{ linkCode }}</code>
                      <button class="copy-btn" @click="copyCode">{{ copied ? 'Скопировано' : 'Копировать' }}</button>
                    </div>
                    <div v-if="linkCode" class="ob-tg-code-meta">
                      <span class="link-note">{{ $t('tracker.code_expires') }}</span>
                      <button class="link-reset" @click="linkCode = null">{{ $t('tracker.new_code') }}</button>
                    </div>
                  </div>
                </div>

                <!-- Step 4 -->
                <div class="ob-tg-step">
                  <span class="ob-tg-num">4</span>
                  <div class="ob-tg-body">
                    <span class="ob-tg-text">Обнови страницу — данные появятся</span>
                    <button class="btn-glass ob-tg-btn" @click="refreshWithProfile">Обновить</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template v-else-if="hasData">
      <!-- KPI strip -->
      <div class="kpi-grid">
        <div class="kpi-card glass-card">
          <div class="kpi-badge kpi-badge--blue">₸</div>
          <div class="kpi-body">
            <div class="kpi-value">{{ fmt(summary.budget.current_balance) }}</div>
            <div class="kpi-label">{{ $t('tracker.balance') }}</div>
          </div>
        </div>
        <div class="kpi-card glass-card">
          <div class="kpi-badge kpi-badge--red">−</div>
          <div class="kpi-body">
            <div class="kpi-value">{{ fmt(summary.budget.total_expense) }}</div>
            <div class="kpi-label">{{ $t('tracker.spent_month') }}</div>
          </div>
        </div>
        <div class="kpi-card glass-card" :class="usageClass">
          <div class="kpi-badge kpi-badge--yellow">%</div>
          <div class="kpi-body">
            <div class="kpi-value">{{ summary.budget.usage_pct }}%</div>
            <div class="kpi-label">{{ $t('tracker.usage_pct') }}</div>
          </div>
        </div>
        <div class="kpi-card glass-card">
          <div class="kpi-badge kpi-badge--purple">↗</div>
          <div class="kpi-body">
            <div class="kpi-value">{{ fmt(summary.daily_rate) }}</div>
            <div class="kpi-label">
              {{ $t('tracker.daily_rate') }}
              <span v-if="summary.days_left_forecast" class="forecast-tag">
                ≈ {{ summary.days_left_forecast }} {{ $t('tracker.days_left') }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Budget progress bar -->
      <div class="glass-card budget-bar-card">
        <div class="budget-bar-header">
          <span>{{ $t('tracker.budget_month') }}: {{ fmt(summary.budget.monthly_limit) }}</span>
          <span :class="usageClass">{{ summary.budget.usage_pct }}% {{ $t('tracker.used') }}</span>
        </div>
        <div class="budget-bar-track">
          <div class="budget-bar-fill" :style="budgetBarStyle"></div>
        </div>
        <div class="budget-bar-labels">
          <span>{{ fmt(summary.budget.total_expense) }} {{ $t('tracker.spent_label') }}</span>
          <span>{{ fmt(Math.max(0, summary.budget.monthly_limit - summary.budget.total_expense)) }} {{ $t('tracker.remaining_label') }}</span>
        </div>
      </div>

      <!-- Charts row -->
      <div class="charts-grid">
        <!-- Daily expenses line chart -->
        <div class="chart-card glass-card">
          <div class="chart-header">
            <h3 class="chart-title">{{ $t('tracker.chart_daily') }}</h3>
          </div>
          <div class="chart-wrap">
            <Line v-if="lineChartData" :data="lineChartData" :options="lineOptions" />
            <div v-else class="chart-empty">{{ $t('tracker.no_data') }}</div>
          </div>
        </div>

        <!-- Category doughnut -->
        <div class="chart-card glass-card">
          <div class="chart-header">
            <h3 class="chart-title">{{ $t('tracker.chart_categories') }}</h3>
          </div>
          <div class="chart-wrap chart-wrap--doughnut">
            <Doughnut v-if="doughnutData" :data="doughnutData" :options="doughnutOptions" />
            <div v-else class="chart-empty">{{ $t('tracker.no_data') }}</div>
          </div>
          <!-- Category legend -->
          <div class="cat-legend" v-if="summary.categories.length">
            <div v-for="(cat, i) in summary.categories.slice(0, 6)" :key="cat.name" class="cat-row">
              <span class="cat-dot" :style="{ background: COLORS[i % COLORS.length] }"></span>
              <span class="cat-name">{{ resolveCategory(cat.name, $t) }}</span>
              <span class="cat-pct">{{ cat.pct }}%</span>
              <span class="cat-amt">{{ fmt(cat.amount) }}</span>
            </div>
          </div>
        </div>

        <!-- Monthly history bar chart -->
        <div class="chart-card glass-card">
          <div class="chart-header">
            <h3 class="chart-title">{{ $t('tracker.chart_monthly') }}</h3>
          </div>
          <div class="chart-wrap">
            <Bar v-if="barChartData" :data="barChartData" :options="barOptions" />
            <div v-else class="chart-empty">{{ $t('tracker.no_data') }}</div>
          </div>
        </div>
      </div>

      <!-- AI Report section -->
      <div class="glass-card ai-section">
        <div class="ai-header">
          <div>
            <h3 class="ai-title">{{ $t('tracker.ai_title') }}</h3>
            <p class="ai-subtitle">{{ $t('tracker.ai_subtitle', { period: periodLabel }) }}</p>
          </div>
          <button class="btn-primary-gradient ai-btn" :disabled="aiStore.analyzing" @click="requestAiReport">
            <span v-if="aiStore.analyzing" class="spinner"></span>
            {{ aiStore.analyzing ? $t('tracker.ai_opening') : $t('tracker.ai_request_btn') }}
          </button>
        </div>

        <!-- Preview of what will be sent -->
        <div class="ai-preview">
          <div class="preview-label">{{ $t('tracker.ai_data_label') }}</div>
          <div class="preview-body">
            <div class="preview-row"><span>{{ $t('tracker.ai_income') }}</span><strong>{{ fmt(summary.budget.total_income) }}</strong></div>
            <div class="preview-row"><span>{{ $t('tracker.ai_expense') }}</span><strong>{{ fmt(summary.budget.total_expense) }}</strong></div>
            <div class="preview-row"><span>{{ $t('tracker.ai_balance') }}</span><strong>{{ fmt(summary.budget.current_balance) }}</strong></div>
            <div class="preview-row"><span>{{ $t('tracker.budget_month') }}</span><strong>{{ fmt(summary.budget.monthly_limit) }} ({{ summary.budget.usage_pct }}%)</strong></div>
            <div v-if="summary.categories.length" class="preview-row preview-row--cats">
              <span>{{ $t('tracker.ai_categories') }}</span>
              <div class="preview-cats">
                <span v-for="cat in summary.categories" :key="cat.name" class="preview-cat-chip">
                  {{ resolveCategory(cat.name, $t) }}: {{ fmt(cat.amount) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="aiError" class="ai-error">⚠️ {{ aiError }}</div>
      </div>

      <!-- Transaction list -->
      <div class="glass-card txn-card">
        <div class="txn-header">
          <h3 class="chart-title">{{ $t('tracker.transactions_title') }}</h3>
          <span class="txn-total">{{ txnData?.total ?? 0 }} {{ $t('tracker.transactions_count') }}</span>
        </div>
        <div class="txn-list" v-if="txnData?.items?.length">
          <div v-for="txn in txnData.items" :key="txn.id" class="txn-row">
            <div class="txn-left">
              <span class="txn-type-dot" :class="txn.type === 'expense' ? 'dot-expense' : 'dot-income'"></span>
              <div class="txn-info">
                <span class="txn-category">{{ resolveCategory(txn.category, $t) }}</span>
                <span class="txn-date">{{ fmtDate(txn.created_at) }}</span>
              </div>
            </div>
            <div class="txn-right">
              <span class="txn-amount" :class="txn.type === 'expense' ? 'amount-expense' : 'amount-income'">
                {{ txn.type === 'expense' ? '−' : '+' }}{{ fmt(txn.amount) }}
              </span>
              <button class="txn-delete" @click="deleteTransaction(txn)" title="Удалить">×</button>
            </div>
          </div>
        </div>
        <div v-else class="chart-empty">{{ $t('tracker.no_transactions') }}</div>

        <button v-if="txnData && txnData.total > txnData.items.length" class="load-more" @click="loadMoreTxn">
          {{ $t('tracker.load_more') }}
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAIChatsStore } from '../stores/aiChats'
import { useAuthStore } from '../stores/auth'

const { t, locale } = useI18n()
const authStore = useAuthStore()

async function refreshWithProfile() {
  try {
    const res = await api.get('/auth/me')
    authStore.user = res.data
    localStorage.setItem('user', JSON.stringify(res.data))
  } catch {}
  await loadAll()
}

function localeTag() {
  return { ru: 'ru-RU', en: 'en-US', kk: 'kk-KZ' }[locale.value] || 'ru-RU'
}
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  ArcElement, BarElement, Tooltip, Legend, Filler,
} from 'chart.js'
import { Line, Doughnut, Bar } from 'vue-chartjs'
import api from '../services/api'
import { resolveCategory } from '../utils/categoryUtils'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, ArcElement, BarElement, Tooltip, Legend, Filler)

const router = useRouter()
const aiStore = useAIChatsStore()

const COLORS = ['#6366F1','#8B5CF6','#06B6D4','#10B981','#F59E0B','#EF4444','#EC4899','#14B8A6','#F97316','#64748B']

const CATEGORIES = computed(() => [
  t('tracker.categories.required'),
  t('tracker.categories.food'),
  t('tracker.categories.transport'),
  t('tracker.categories.subscriptions'),
  t('tracker.categories.credits'),
  t('tracker.categories.clothing'),
  t('tracker.categories.entertainment'),
  t('tracker.categories.health'),
  t('tracker.categories.other'),
])

// ── Period selector ─────────────────────────────────────────────────────────
const availablePeriods = computed(() => {
  const now = new Date()
  const periods = []
  for (let i = 0; i < 6; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    const label = d.toLocaleString(localeTag(), { month: 'long', year: 'numeric' })
    periods.push({ value, label: label.charAt(0).toUpperCase() + label.slice(1) })
  }
  return periods
})

const selectedPeriod = ref(new Date().toISOString().slice(0, 7))
const periodLabel = computed(() => availablePeriods.value.find(p => p.value === selectedPeriod.value)?.label ?? '')

const telegramUrl = computed(() => `https://t.me/${import.meta.env.VITE_TELEGRAM_BOT_USERNAME || 'FinLit_bot'}`)

// ── State ───────────────────────────────────────────────────────────────────
const loading = ref(false)
const summary = ref(null)
const txnData = ref(null)
const history = ref([])
const aiError = ref(null)

// Link flow
const linkCode = ref(null)
const linkLoading = ref(false)
const copied = ref(false)

const hasData = computed(() =>
  summary.value && summary.value.budget.monthly_limit > 0
)

// ── Action modals ────────────────────────────────────────────────────────────
const modal = ref(null)        // 'expense' | 'income' | 'budget' | null
const actionLoading = ref(false)
const actionError = ref(null)

// Expense form
const expenseStep = ref(false)
const customCategory = ref('')
const expenseForm = ref({ category: '', amount: null, description: '' })

// Income / budget forms
const incomeForm = ref({ amount: null })
const budgetForm = ref({ amount: null })

function openModal(type) {
  modal.value = type
  actionError.value = null
  expenseStep.value = false
  expenseForm.value = { category: '', amount: null, description: '' }
  customCategory.value = ''
  incomeForm.value = { amount: null }
  budgetForm.value = { amount: null }
}

async function submitExpense() {
  if (!expenseForm.value.amount || expenseForm.value.amount <= 0) return
  actionLoading.value = true
  actionError.value = null
  try {
    await api.post('/tracker/expense', {
      amount: expenseForm.value.amount,
      category: expenseForm.value.category,
      description: expenseForm.value.description || null,
    })
    modal.value = null
    await loadAll()
  } catch (e) {
    actionError.value = e.response?.data?.detail || 'Ошибка сохранения'
  } finally {
    actionLoading.value = false
  }
}

async function submitIncome() {
  if (!incomeForm.value.amount || incomeForm.value.amount <= 0) return
  actionLoading.value = true
  actionError.value = null
  try {
    await api.post('/tracker/income', { amount: incomeForm.value.amount })
    modal.value = null
    await loadAll()
  } catch (e) {
    actionError.value = e.response?.data?.detail || 'Ошибка сохранения'
  } finally {
    actionLoading.value = false
  }
}

async function submitBudget() {
  if (!budgetForm.value.amount || budgetForm.value.amount <= 0) return
  actionLoading.value = true
  actionError.value = null
  try {
    await api.put('/tracker/budget', { amount: budgetForm.value.amount })
    modal.value = null
    await loadAll()
  } catch (e) {
    actionError.value = e.response?.data?.detail || 'Ошибка сохранения'
  } finally {
    actionLoading.value = false
  }
}

async function deleteTransaction(txn) {
  if (!confirm(`${t('common.delete')} "${resolveCategory(txn.category, t)}" — ${fmt(txn.amount)}?`)) return
  try {
    await api.delete(`/tracker/transaction/${txn.id}`)
    await loadAll()
  } catch (e) {
    alert('Не удалось удалить операцию')
  }
}

// ── Formatters ──────────────────────────────────────────────────────────────
function fmt(val) {
  return `${Number(val || 0).toLocaleString(localeTag())} ₸`
}
function fmtDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString(localeTag(), { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

// ── Load data ────────────────────────────────────────────────────────────────
async function loadAll() {
  loading.value = true
  summary.value = null
  txnData.value = null
  try {
    const [s, txn, h] = await Promise.all([
      api.get(`/tracker/summary?period=${selectedPeriod.value}`),
      api.get(`/tracker/transactions?period=${selectedPeriod.value}&limit=30`),
      api.get('/tracker/monthly-history?months=6'),
    ])
    summary.value = s.data
    txnData.value = txn.data
    history.value = h.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function getlinkCode() {
  linkLoading.value = true
  try {
    const res = await api.get('/auth/link-code')
    linkCode.value = res.data.code
  } catch (e) {
    console.error(e)
  } finally {
    linkLoading.value = false
  }
}

async function copyCode() {
  await navigator.clipboard.writeText(`/link ${linkCode.value}`)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

async function loadMoreTxn() {
  const skip = txnData.value.items.length
  const res = await api.get(`/tracker/transactions?period=${selectedPeriod.value}&limit=30&skip=${skip}`)
  txnData.value.items.push(...res.data.items)
}

// ── AI report ────────────────────────────────────────────────────────────────
async function requestAiReport() {
  aiError.value = null
  // Navigate to the AI page immediately — loading will display there
  await router.push('/ai')
  try {
    await aiStore.analyzeTrackerReport(selectedPeriod.value)
    // AIChatView watches pendingChatId and navigates to the chat automatically
  } catch {
    // Error is stored in aiStore.error; AIChatView will display it
  }
}

// ── Chart: budget usage style ────────────────────────────────────────────────
const usageClass = computed(() => {
  const pct = summary.value?.budget?.usage_pct ?? 0
  if (pct >= 100) return 'danger'
  if (pct >= 80) return 'warning'
  return 'success'
})

const budgetBarStyle = computed(() => {
  const pct = Math.min(summary.value?.budget?.usage_pct ?? 0, 100)
  const color = pct >= 100 ? '#EF4444' : pct >= 80 ? '#F59E0B' : '#10B981'
  return { width: pct + '%', background: color }
})

// ── Chart: Line (daily expenses) ─────────────────────────────────────────────
const lineChartData = computed(() => {
  const days = summary.value?.daily_expenses
  if (!days?.length) return null
  return {
    labels: days.map(d => d.date.slice(8)),
    datasets: [{
      label: t('dashboard.expenses'),
      data: days.map(d => d.amount),
      borderColor: '#6366F1',
      backgroundColor: 'rgba(99,102,241,0.12)',
      fill: true,
      tension: 0.3,
      pointRadius: 2,
      pointHoverRadius: 5,
    }],
  }
})

const lineOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748B', font: { size: 10 } } },
    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748B', font: { size: 10 } } },
  },
}

// ── Chart: Doughnut (categories) ─────────────────────────────────────────────
const doughnutData = computed(() => {
  const cats = summary.value?.categories
  if (!cats?.length) return null
  return {
    labels: cats.map(c => resolveCategory(c.name, t)),
    datasets: [{
      data: cats.map(c => c.amount),
      backgroundColor: COLORS,
      borderWidth: 2,
      borderColor: '#1E293B',
      hoverOffset: 8,
    }],
  }
})

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '68%',
  plugins: { legend: { display: false } },
}

// ── Chart: Bar (monthly history) ──────────────────────────────────────────────
const barChartData = computed(() => {
  if (!history.value?.length) return null
  const monthLabels = {
    '01':'Янв','02':'Фев','03':'Мар','04':'Апр','05':'Май','06':'Июн',
    '07':'Июл','08':'Авг','09':'Сен','10':'Окт','11':'Ноя','12':'Дек',
  }
  return {
    labels: history.value.map(h => monthLabels[h.period.slice(5)] ?? h.period.slice(5)),
    datasets: [
      {
        label: t('dashboard.expenses'),
        data: history.value.map(h => h.total_expense),
        backgroundColor: 'rgba(99,102,241,0.7)',
        borderRadius: 6,
      },
      {
        label: t('tracker.budget_month'),
        data: history.value.map(h => h.monthly_limit),
        backgroundColor: 'rgba(100,116,139,0.3)',
        borderRadius: 6,
      },
    ],
  }
})

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: '#94A3B8', font: { size: 11 } } },
  },
  scales: {
    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748B' } },
    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748B' } },
  },
}

onMounted(loadAll)
</script>

<style scoped>
.tracker-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem 1.5rem 5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Header */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.page-title { font-size: 1.6rem; font-weight: 800; color: var(--text-primary); margin: 0; }
.page-subtitle { color: var(--text-muted); font-size: 0.85rem; margin: 0.25rem 0 0; }

/* Action buttons */
.header-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.btn-action {
  padding: 0.45rem 0.9rem;
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
  white-space: nowrap;
}
.btn-expense { background: rgba(239,68,68,0.15); color: #F87171; border: 1px solid rgba(239,68,68,0.3); }
.btn-expense:hover { background: rgba(239,68,68,0.25); }
.btn-income  { background: rgba(16,185,129,0.15); color: #34D399; border: 1px solid rgba(16,185,129,0.3); }
.btn-income:hover  { background: rgba(16,185,129,0.25); }
.btn-budget  { background: rgba(99,102,241,0.15); color: #818CF8; border: 1px solid rgba(99,102,241,0.3); }
.btn-budget:hover  { background: rgba(99,102,241,0.25); }

/* Modal */
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
  padding: 1rem;
}
.modal-card {
  width: 100%; max-width: 460px;
  padding: 0;
  overflow: hidden;
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.modal-header h3 { margin: 0; font-size: 1rem; font-weight: 700; color: var(--text-primary); }
.modal-close {
  background: none; border: none; color: var(--text-muted);
  font-size: 1.1rem; cursor: pointer; line-height: 1;
  transition: color 0.15s;
}
.modal-close:hover { color: var(--text-primary); }
.modal-body { padding: 1.25rem 1.5rem; display: flex; flex-direction: column; gap: 0.75rem; }
.modal-label { font-size: 0.85rem; color: var(--text-secondary); margin: 0; }
.modal-note { font-size: 0.78rem; color: var(--text-muted); margin: 0; }
.modal-actions { display: flex; gap: 0.75rem; margin-top: 0.5rem; }
.modal-actions button { flex: 1; justify-content: center; }
.amount-input { font-size: 1.5rem; font-weight: 700; text-align: center; padding: 0.75rem; }
.action-error { color: var(--danger-light); font-size: 0.82rem; }
.mt { margin-top: 0.5rem; }
.w-100 { width: 100%; }

/* Category grid */
.category-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.4rem;
}
.cat-btn {
  padding: 0.5rem 0.25rem;
  border-radius: var(--radius-sm);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  color: var(--text-secondary);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s;
  text-align: center;
}
.cat-btn:hover { background: rgba(99,102,241,0.12); color: var(--text-primary); border-color: rgba(99,102,241,0.3); }
.cat-btn.active { background: rgba(99,102,241,0.2); color: var(--primary-light); border-color: var(--primary-light); font-weight: 600; }
.custom-cat-row { margin-top: 0.25rem; }

.period-select {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: var(--radius-sm);
  padding: 0.45rem 0.85rem;
  font-size: 0.85rem;
  cursor: pointer;
}

/* KPI grid */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}
.kpi-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
}
.kpi-badge {
  width: 38px; height: 38px;
  border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.95rem; font-weight: 800;
  flex-shrink: 0;
}
.kpi-badge--blue   { background: rgba(99,102,241,0.15);  color: #818CF8; border: 1px solid rgba(99,102,241,0.25); }
.kpi-badge--red    { background: rgba(239,68,68,0.12);   color: #F87171; border: 1px solid rgba(239,68,68,0.2); }
.kpi-badge--yellow { background: rgba(245,158,11,0.12);  color: #FCD34D; border: 1px solid rgba(245,158,11,0.2); }
.kpi-badge--purple { background: rgba(139,92,246,0.15);  color: #A78BFA; border: 1px solid rgba(139,92,246,0.25); }

.kpi-value { font-size: 1.3rem; font-weight: 700; color: var(--text-primary); }
.kpi-label { font-size: 0.78rem; color: var(--text-muted); margin-top: 2px; }
.forecast-tag {
  display: inline-block;
  background: rgba(99,102,241,0.15);
  color: var(--primary-light);
  font-size: 0.7rem;
  padding: 1px 6px;
  border-radius: 20px;
  margin-left: 4px;
}

/* Budget bar */
.budget-bar-card { padding: 1.25rem 1.5rem; }
.budget-bar-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 0.6rem;
}
.budget-bar-track {
  height: 10px;
  background: rgba(255,255,255,0.06);
  border-radius: 99px;
  overflow: hidden;
}
.budget-bar-fill { height: 100%; border-radius: 99px; transition: width 0.5s ease; }
.budget-bar-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-top: 0.4rem;
}

/* Charts */
.charts-grid {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1.4fr;
  gap: 1rem;
}
.chart-card { padding: 1.25rem; display: flex; flex-direction: column; gap: 1rem; }
.chart-header { display: flex; align-items: center; justify-content: space-between; }
.chart-title { font-size: 0.95rem; font-weight: 600; color: var(--text-primary); margin: 0; }
.chart-wrap { height: 200px; position: relative; }
.chart-wrap--doughnut { height: 160px; }
.chart-empty { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-muted); font-size: 0.85rem; }

/* Category legend */
.cat-legend { display: flex; flex-direction: column; gap: 0.4rem; }
.cat-row { display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; }
.cat-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.cat-name { flex: 1; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cat-pct { color: var(--text-muted); width: 36px; text-align: right; }
.cat-amt { color: var(--text-primary); font-weight: 600; width: 80px; text-align: right; }

/* AI section */
.ai-section { padding: 1.5rem; }
.ai-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.25rem; }
.ai-title { font-size: 1rem; font-weight: 700; color: var(--text-primary); margin: 0; }
.ai-subtitle { font-size: 0.82rem; color: var(--text-muted); margin: 0.25rem 0 0; }
.ai-btn { padding: 0.55rem 1.4rem; font-size: 0.85rem; white-space: nowrap; min-width: 160px; }
.ai-error { color: var(--danger-light); font-size: 0.85rem; margin-top: 0.75rem; }

.ai-preview {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius-md);
  padding: 1rem 1.25rem;
}
.preview-label { font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
.preview-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; font-size: 0.85rem; padding: 0.3rem 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.preview-row:last-child { border-bottom: none; }
.preview-row span { color: var(--text-muted); }
.preview-row strong { color: var(--text-primary); }
.preview-row--cats { flex-wrap: wrap; }
.preview-cats { display: flex; flex-wrap: wrap; gap: 0.35rem; justify-content: flex-end; }
.preview-cat-chip {
  background: rgba(99,102,241,0.12);
  color: var(--primary-light);
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 20px;
}

/* Transactions */
.txn-card { padding: 1.25rem; }
.txn-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.txn-total { font-size: 0.8rem; color: var(--text-muted); }
.txn-list { display: flex; flex-direction: column; gap: 0.5rem; }
.txn-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.65rem 0.75rem;
  border-radius: var(--radius-sm);
  background: rgba(255,255,255,0.02);
  transition: background 0.15s;
}
.txn-row:hover { background: rgba(255,255,255,0.05); }
.txn-left { display: flex; align-items: center; gap: 0.75rem; }
.txn-type-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot-expense { background: #EF4444; }
.dot-income  { background: #10B981; }
.txn-info { display: flex; flex-direction: column; gap: 2px; }
.txn-category { font-size: 0.88rem; font-weight: 500; color: var(--text-primary); }
.txn-date { font-size: 0.75rem; color: var(--text-muted); }
.txn-amount { font-size: 0.95rem; font-weight: 700; }
.amount-expense { color: #F87171; }
.amount-income  { color: #34D399; }

.txn-right { display: flex; align-items: center; gap: 0.75rem; }
.txn-delete {
  background: none; border: none; color: var(--text-muted);
  font-size: 1.1rem; cursor: pointer; line-height: 1; padding: 0 4px;
  opacity: 0; transition: opacity 0.15s, color 0.15s;
}
.txn-row:hover .txn-delete { opacity: 1; }
.txn-delete:hover { color: var(--danger-light); }

.load-more {
  display: block;
  margin: 1rem auto 0;
  background: none;
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  font-size: 0.82rem;
  padding: 0.45rem 1.2rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s;
}
.load-more:hover { color: var(--text-primary); border-color: var(--primary-light); }

/* Semantic colors */
.danger { color: var(--danger-light); }
.warning { color: var(--warning-light); }
.success { color: var(--success-light); }

/* ── Onboarding ───────────────────────────────────────────────────────────── */
.onboarding-wrap { display: flex; flex-direction: column; gap: 1rem; }
.onboarding-card { padding: 2rem; }
.onboarding-header { margin-bottom: 2rem; }
.onboarding-title { font-size: 1.4rem; font-weight: 800; color: var(--text-primary); margin: 0 0 0.3rem; }
.onboarding-sub { color: var(--text-muted); font-size: 0.88rem; margin: 0; }
.onboarding-ways { display: flex; flex-direction: column; gap: 0; }
.onboarding-divider {
  text-align: center; color: var(--text-muted); font-size: 0.82rem; padding: 1rem 0; position: relative;
}
.onboarding-divider::before, .onboarding-divider::after {
  content: ''; position: absolute; top: 50%; width: calc(50% - 30px);
  height: 1px; background: rgba(255,255,255,0.06);
}
.onboarding-divider::before { left: 0; }
.onboarding-divider::after  { right: 0; }
.onboarding-way {
  display: flex; gap: 1.25rem; padding: 1.5rem;
  border-radius: var(--radius-md);
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.05);
}
.way-num {
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff; font-size: 0.8rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 2px;
}
.way-body { flex: 1; display: flex; flex-direction: column; gap: 0.5rem; }
.way-title { font-size: 1rem; font-weight: 700; color: var(--text-primary); }
.way-desc  { font-size: 0.85rem; color: var(--text-muted); line-height: 1.5; }
.way-actions { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem; }
/* Link steps */
.link-steps { display: flex; flex-direction: column; gap: 0.75rem; margin-top: 0.5rem; }
.link-step { display: flex; align-items: center; gap: 0.75rem; font-size: 0.85rem; color: var(--text-secondary); }
.step-num {
  width: 22px; height: 22px; border-radius: 50%;
  background: rgba(99,102,241,0.2); color: var(--primary-light);
  font-size: 0.72rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.step-open { margin-left: auto; padding: 0.3rem 0.75rem; font-size: 0.78rem; white-space: nowrap; }
.link-code-box {
  display: flex; align-items: center; gap: 0.75rem;
  background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.3);
  border-radius: var(--radius-md); padding: 0.75rem 1.25rem;
}
.link-code-box code { font-size: 1.1rem; font-weight: 700; color: var(--primary-light); letter-spacing: 0.05em; flex: 1; }
.copy-btn {
  background: rgba(99,102,241,0.15);
  border: 1px solid rgba(99,102,241,0.3);
  color: var(--primary-light);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.65rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  flex-shrink: 0;
  white-space: nowrap;
  transition: background 0.15s;
}
.copy-btn:hover { background: rgba(99,102,241,0.28); }
.link-note { font-size: 0.75rem; color: var(--text-muted); margin: 0; }
.link-reset {
  background: none; border: none; color: var(--text-muted); font-size: 0.78rem;
  cursor: pointer; text-decoration: underline; text-underline-offset: 2px;
  padding: 0; align-self: flex-start;
}
.link-reset:hover { color: var(--text-secondary); }

/* ── Onboarding TG steps ────────────────────────────────────────────────────── */
.ob-tg-steps {
  display: flex;
  flex-direction: column;
  margin-top: 0.75rem;
  border: 1px solid rgba(42,171,238,0.15);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.ob-tg-step {
  display: flex;
  gap: 1rem;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  align-items: flex-start;
}
.ob-tg-step:last-child { border-bottom: none; }
.ob-tg-num {
  width: 24px; height: 24px; border-radius: 50%;
  background: rgba(42,171,238,0.15); color: #2AABEE;
  font-size: 0.75rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 1px;
}
.ob-tg-body {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}
.ob-tg-text {
  flex: 1;
  font-size: 0.88rem;
  color: var(--text-secondary);
  line-height: 1.5;
  min-width: 200px;
}
.ob-tg-btn {
  padding: 0.35rem 0.9rem;
  font-size: 0.82rem;
  white-space: nowrap;
  flex-shrink: 0;
}
.ob-tg-gen-btn {
  font-size: 0.82rem;
  padding: 0.4rem 1.1rem;
  flex-shrink: 0;
}
.ob-tg-code-row {
  display: flex; align-items: center; gap: 0.75rem;
  background: rgba(42,171,238,0.08);
  border: 1px solid rgba(42,171,238,0.25);
  border-radius: var(--radius-sm);
  padding: 0.6rem 1rem;
  flex: 1;
}
.ob-tg-code-row code {
  font-size: 1rem; font-weight: 700;
  color: #2AABEE; flex: 1;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.ob-tg-code-meta {
  display: flex; align-items: center; gap: 1rem;
  width: 100%;
}

/* Skeleton */
.skeleton-card {
  border-radius: var(--radius-md);
  background: linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.04) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  min-height: 90px;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* Responsive */
@media (max-width: 1100px) {
  .charts-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 768px) {
  .kpi-grid { grid-template-columns: 1fr 1fr; }
  .charts-grid { grid-template-columns: 1fr; }
  .tracker-page { padding: 1rem 1rem 5rem; }
  .category-grid { grid-template-columns: repeat(2, 1fr); }
  .modal-wrap { padding: 0.75rem; }
  .modal-box { padding: 1.25rem; max-height: 90vh; overflow-y: auto; }
  .txn-list { overflow-x: hidden; }
}
@media (max-width: 480px) {
  .kpi-grid { grid-template-columns: 1fr 1fr; }
  .category-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
