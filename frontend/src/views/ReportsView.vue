<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">{{ $t('reports.title') }}</h1>
        <p class="page-subtitle">{{ $t('reports.subtitle') }}</p>
      </div>
      <div class="header-actions">
        <button class="btn-glass" type="button" @click="pdfInput?.click()">
          {{ $t('reports.kaspi_import') }}
        </button>
        <button class="btn-primary-gradient" @click="openForm()" id="new-report-btn">
          + {{ $t('reports.new_report') }}
        </button>
        <input
          ref="pdfInput"
          class="visually-hidden"
          type="file"
          accept="application/pdf,.pdf"
          @change="handlePdfUpload"
        />
      </div>
    </div>

    <div v-if="aiError" class="alert-box danger">{{ aiError }}</div>

    <section class="import-panel" v-if="importedAnalysis || importError || reportsStore.loading">
      <div class="import-status" v-if="reportsStore.loading && !importedAnalysis">
        <span class="spinner"></span>
        <span>{{ $t('reports.analyzing_pdf') }}</span>
      </div>

      <div v-if="importError" class="alert-box danger">{{ importError }}</div>

      <div v-if="importedAnalysis" class="analysis-layout">
        <div class="analysis-head">
          <div>
            <h2>{{ $t('reports.kaspi_analysis_title') }}</h2>
            <p>{{ $t('reports.operations_found') }}: {{ importedAnalysis.transactions.length }}</p>
          </div>
          <button class="btn-success-gradient" type="button" @click="saveImportedReport">
            {{ $t('reports.save_report') }}
          </button>
        </div>

        <div class="summary-grid">
          <div class="summary-item">
            <span>{{ $t('reports.available_total') }}</span>
            <strong class="income">{{ formatMoney(importedAnalysis.summary.totalIncome) }}</strong>
          </div>
          <div class="summary-item">
            <span>{{ $t('reports.spent_total') }}</span>
            <strong class="expense">{{ formatMoney(importedAnalysis.summary.totalExpense) }}</strong>
          </div>
          <div class="summary-item">
            <span>{{ $t('reports.remaining_surplus') }}</span>
            <strong :class="importedAnalysis.summary.balanceLeft >= 0 ? 'income' : 'expense'">
              {{ formatMoney(importedAnalysis.summary.balanceLeft) }}
            </strong>
          </div>
          <div class="summary-item">
            <span>{{ $t('reports.after_required') }}</span>
            <strong :class="moneyAfterRequired >= 0 ? 'income' : 'expense'">
              {{ formatMoney(moneyAfterRequired) }}
            </strong>
          </div>
        </div>

        <div class="summary-details">
          <div v-for="field in summaryFields" :key="field.key" class="detail-row">
            <span>{{ field.label }}</span>
            <strong>{{ formatMoney(importedAnalysis.summary[field.key]) }}</strong>
          </div>
        </div>

        <div class="warnings-list" v-if="importedAnalysis.warnings.length">
          <div v-for="warning in importedAnalysis.warnings" :key="warning" class="alert-box warning">
            {{ warning }}
          </div>
        </div>

        <div class="chart-section" v-if="importedAnalysis.chartData.length">
          <div class="section-title-row">
            <h3>{{ $t('reports.chart_daily') }}</h3>
            <span>{{ importedAnalysis.chartData.length }} {{ $t('reports.days_suffix') }}</span>
          </div>
          <div class="month-strip" v-if="chartMonths.length > 1">
            <span v-for="month in chartMonths" :key="month">{{ month }}</span>
          </div>
          <div class="chart-frame">
            <Line :data="chartConfig" :options="chartOptions" />
          </div>
        </div>

        <div class="manual-grid">
          <section class="manual-section">
            <div class="section-title-row">
              <h3>{{ $t('reports.categories') }}</h3>
              <span>{{ formatMoney(categorizedImportTotal) }}</span>
            </div>
            <datalist id="expense-category-options">
              <option v-for="category in standardCategories" :key="category" :value="category" />
            </datalist>
            <div class="editable-row" v-for="(category, index) in categoriesDraft" :key="`cat-${index}`">
              <input
                v-model="category.name"
                list="expense-category-options"
                class="form-control-dark"
                :placeholder="$t('reports.category_name')"
              />
              <input
                v-model.number="category.amount"
                type="number"
                min="0"
                step="1"
                class="form-control-dark amount-input"
                :placeholder="$t('reports.category_amount')"
              />
              <button type="button" class="btn-remove" @click="removeImportedCategory(index)">x</button>
            </div>
            <button type="button" class="btn-glass btn-sm" @click="addImportedCategory">
              + {{ $t('reports.add_category') }}
            </button>
          </section>

          <section class="manual-section">
            <div class="section-title-row">
              <h3>{{ $t('reports.required_categories') }}</h3>
              <span>{{ formatMoney(requiredTotal) }}</span>
            </div>
            <datalist id="required-category-options">
              <option v-for="category in requiredCategoryNames" :key="category" :value="category" />
            </datalist>
            <div
              class="required-row"
              v-for="(category, index) in requiredDraft"
              :key="`required-${index}`"
            >
              <input
                v-model="category.name"
                list="required-category-options"
                class="form-control-dark"
                :placeholder="$t('reports.payment_name')"
              />
              <input
                v-model.number="category.amount"
                type="number"
                min="0"
                step="1"
                class="form-control-dark"
                :placeholder="$t('reports.category_amount')"
              />
              <input
                v-model="category.duration"
                class="form-control-dark"
                :placeholder="$t('reports.payment_date_placeholder')"
              />
              <button type="button" class="btn-remove" @click="removeRequiredCategory(index)">x</button>
            </div>
            <button type="button" class="btn-glass btn-sm" @click="addRequiredCategory">
              + Добавить обязательный платеж
            </button>
            <div class="safety-line" :class="safetyClass">{{ safetyText }}</div>
          </section>
        </div>
      </div>
    </section>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal-box glass-card">
        <h2 class="modal-title">{{ editing ? $t('reports.edit_report') : $t('reports.new_report') }}</h2>

        <form @submit.prevent="handleSave">
          <div class="form-group">
            <label class="form-label-dark">{{ $t('reports.period') }}</label>
            <input
              v-model="form.period"
              type="month"
              class="form-control-dark w-100"
              required
              id="report-period"
            />
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label class="form-label-dark">{{ $t('reports.total_income') }}</label>
              <input v-model.number="form.total_income" type="number" min="0" step="1" class="form-control-dark w-100" required id="report-income" />
            </div>
            <div class="form-group flex-1">
              <label class="form-label-dark">{{ $t('reports.total_expense') }}</label>
              <input v-model.number="form.total_expense" type="number" min="0" step="1" class="form-control-dark w-100" required id="report-expense" />
            </div>
          </div>

          <div class="categories-section">
            <div class="section-header" @click="showCategories = !showCategories">
              <h3>{{ $t('reports.categories') }}</h3>
              <span class="toggle-icon">{{ showCategories ? 'v' : '>' }}</span>
            </div>

            <transition name="slide-up">
              <div v-if="showCategories" class="categories-list">
                <div class="category-row" v-for="(cat, i) in form.categories" :key="i">
                  <input
                    v-model="cat.name"
                    :placeholder="$t('reports.category_name')"
                    class="form-control-dark cat-name"
                  />
                  <input
                    v-model.number="cat.amount"
                    type="number"
                    min="0"
                    step="1"
                    :placeholder="$t('reports.category_amount')"
                    class="form-control-dark cat-amount"
                  />
                  <button type="button" class="btn-remove" @click="removeCategory(i)">x</button>
                </div>

                <button type="button" class="btn-glass btn-sm" @click="addCategory">
                  + {{ $t('reports.add_category') }}
                </button>
              </div>
            </transition>
          </div>

          <div class="categories-section">
            <div class="section-header" @click="showRequiredCategories = !showRequiredCategories">
              <h3>{{ $t('reports.required_categories') }}</h3>
              <span class="toggle-icon">{{ showRequiredCategories ? 'v' : '>' }}</span>
            </div>

            <transition name="slide-up">
              <div v-if="showRequiredCategories" class="categories-list">
                <div class="required-form-row" v-for="(cat, i) in form.required_categories" :key="`form-required-${i}`">
                  <input
                    v-model="cat.name"
                    list="required-category-options"
                    :placeholder="$t('reports.payment_name')"
                    class="form-control-dark"
                  />
                  <input
                    v-model.number="cat.amount"
                    type="number"
                    min="0"
                    step="1"
                    :placeholder="$t('reports.category_amount')"
                    class="form-control-dark"
                  />
                  <input
                    v-model="cat.duration"
                    :placeholder="$t('reports.payment_date_placeholder')"
                    class="form-control-dark"
                  />
                  <button type="button" class="btn-remove" @click="removeFormRequiredCategory(i)">x</button>
                </div>

                <button type="button" class="btn-glass btn-sm" @click="addFormRequiredCategory">
                  + {{ $t('reports.add_required') }}
                </button>
              </div>
            </transition>
          </div>

          <div class="balance-preview" v-if="form.total_expense > 0">
            <div class="balance-row">
              <span>{{ $t('reports.unaccounted') }}</span>
              <span class="balance-value" :class="{ warning: unaccounted > 0 }">
                {{ formatMoney(unaccounted) }}
              </span>
            </div>
            <div class="balance-row" v-if="formRequiredTotal > 0">
              <span>{{ $t('reports.required_payments') }}</span>
              <span class="balance-value warning">{{ formatMoney(formRequiredTotal) }}</span>
            </div>
            <div class="balance-row">
              <span>{{ $t('reports.surplus') }}</span>
              <span class="balance-value" :class="{ success: surplus >= 0, danger: surplus < 0 }">
                {{ formatMoney(surplus) }}
              </span>
            </div>
          </div>

          <div class="form-actions">
            <button type="button" class="btn-glass" @click="showForm = false">{{ $t('reports.cancel') }}</button>
            <button type="submit" class="btn-primary-gradient" :disabled="reportsStore.loading" id="report-save-btn">
              <span v-if="reportsStore.loading" class="spinner"></span>
              {{ $t('reports.save') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="reportsStore.loading && !reportsStore.reports.length && !importedAnalysis" class="loading-grid">
      <div class="skeleton" style="height:120px" v-for="i in 3" :key="i"></div>
    </div>

    <div v-else-if="reportsStore.reports.length === 0" class="empty-state">
      <h3>{{ $t('dashboard.no_reports') }}</h3>
      <p>{{ $t('dashboard.create_first_report') }}</p>
    </div>

    <div v-else class="reports-grid">
      <Menu ref="reportMenu" :model="reportMenuItems" popup />
      <div class="report-card premium-card" v-for="report in reportsStore.reports" :key="report.id">
        <!-- Card Header -->
        <div class="report-card-header">
          <div>
            <h3 class="report-period">{{ report.period }}</h3>
            <div class="report-cat-count" v-if="(report.categories || []).length">
              {{ report.categories.length }} {{ report.categories.length === 1 ? 'категория' : 'категорий' }}
            </div>
          </div>
          <div class="report-header-right">
            <span class="surplus-pill" :class="report.surplus >= 0 ? 'pill-pos' : 'pill-neg'">
              {{ report.surplus >= 0 ? '+' : '' }}{{ formatMoney(report.surplus) }}
            </span>
            <button
              class="btn-icon-round"
              @click="activeMenuReport = report; reportMenu.toggle($event)"
              title="Действия"
            >
              <i class="pi pi-ellipsis-v"></i>
            </button>
          </div>
        </div>

        <!-- Income vs Expense Stats -->
        <div class="report-stats-row">
          <div class="rs-block">
            <div class="rs-icon-wrap rs-inc"><i class="pi pi-arrow-up"></i></div>
            <div>
              <div class="rs-label">{{ $t('reports.total_income') }}</div>
              <div class="rs-value income">{{ formatMoney(report.total_income) }}</div>
            </div>
          </div>
          <div class="rs-block">
            <div class="rs-icon-wrap rs-exp"><i class="pi pi-arrow-down"></i></div>
            <div>
              <div class="rs-label">{{ $t('reports.total_expense') }}</div>
              <div class="rs-value expense">{{ formatMoney(report.total_expense) }}</div>
            </div>
          </div>
        </div>

        <!-- Expense ratio bar -->
        <div class="report-ratio-bar" v-if="report.total_income > 0">
          <div class="ratio-track">
            <div
              class="ratio-fill"
              :class="expenseRatioClass(report)"
              :style="{ width: Math.min(100, expenseRatio(report)) + '%' }"
            ></div>
          </div>
          <div class="ratio-labels">
            <span>{{ expenseRatio(report) }}% {{ $t('reports.spent_total').toLowerCase() }}</span>
            <span v-if="report.unaccounted_expense > 0" class="ratio-unaccounted">
              ~{{ formatMoney(report.unaccounted_expense) }} {{ $t('reports.no_categories') }}
            </span>
          </div>
        </div>

        <!-- Top Categories -->
        <div class="report-cats-row" v-if="(report.categories || []).length">
          <span
            class="cat-chip"
            v-for="cat in (report.categories || []).slice(0, 4)"
            :key="cat.name"
          >{{ cat.name }}</span>
          <span v-if="(report.categories || []).length > 4" class="cat-chip cat-chip-more">
            +{{ report.categories.length - 4 }}
          </span>
        </div>

        <div class="report-ai-actions" v-if="sendingReportToAi === report.id">
          <span class="spinner"></span>
          <span style="font-size:0.82rem;color:var(--text-muted)">{{ $t('reports.sending_ai') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Menu from 'primevue/menu'

const { t } = useI18n()
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
} from 'chart.js'
import { useReportsStore } from '../stores/reports'
import { useAuthStore } from '../stores/auth'
import { useAIChatsStore } from '../stores/aiChats'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler)

const reportsStore = useReportsStore()
const authStore = useAuthStore()
const aiChatsStore = useAIChatsStore()
const router = useRouter()

const showForm = ref(false)
const showCategories = ref(false)
const showRequiredCategories = ref(false)
const editing = ref(null)
const pdfInput = ref(null)
const importedAnalysis = ref(null)
const importError = ref('')
const aiError = ref('')
const sendingReportToAi = ref(null)
const categoriesDraft = ref([])
const reportMenu = ref(null)
const activeMenuReport = ref(null)

const reportMenuItems = computed(() => [
  {
    label: t('reports.edit_report'),
    icon: 'pi pi-pencil',
    command: () => openForm(activeMenuReport.value),
  },
  {
    label: t('reports.ai_analysis_btn'),
    icon: 'pi pi-sparkles',
    command: () => sendReportToAi(activeMenuReport.value),
  },
  {
    separator: true,
  },
  {
    label: t('common.delete'),
    icon: 'pi pi-trash',
    command: () => confirmDelete(activeMenuReport.value?.id),
  },
])
const requiredDraft = ref([])

const standardCategories = computed(() => [
  t('reports.categories_preset.food'),
  t('reports.categories_preset.restaurants'),
  t('reports.categories_preset.transport'),
  t('reports.categories_preset.taxi'),
  t('reports.categories_preset.utilities'),
  t('reports.categories_preset.communication'),
  t('reports.categories_preset.clothing_shoes'),
  t('reports.categories_preset.health_pharmacy'),
  t('reports.categories_preset.entertainment'),
  t('reports.categories_preset.education'),
  t('reports.categories_preset.loan'),
  t('reports.categories_preset.transfers_people'),
  t('reports.categories_preset.other_expenses'),
])

const requiredCategoryNames = computed(() => [
  t('reports.categories_preset.loan'),
  t('reports.categories_preset.rent'),
  t('reports.categories_preset.utilities'),
  t('tracker.categories.subscriptions'),
  t('reports.categories_preset.education'),
  t('reports.categories_preset.communication'),
])

const defaultCategoryCount = 3

const summaryFields = computed(() => [
  { key: 'startBalance', label: t('reports.summary.startBalance') },
  { key: 'topUps', label: t('reports.summary.topUps') },
  { key: 'ownAccountIncome', label: t('reports.summary.ownAccountIncome') },
  { key: 'transfers', label: t('reports.summary.transfers') },
  { key: 'ownAccountTransfers', label: t('reports.summary.ownAccountTransfers') },
  { key: 'purchases', label: t('reports.summary.purchases') },
  { key: 'cashWithdrawals', label: t('reports.summary.cashWithdrawals') },
  { key: 'other', label: t('reports.summary.other') },
])

const form = reactive({
  period: new Date().toISOString().slice(0, 7),
  total_income: 0,
  total_expense: 0,
  categories: [],
  required_categories: [],
})

onMounted(() => {
  reportsStore.fetchReports()
})

const currencySymbol = computed(() => {
  const symbols = { KZT: '₸', USD: '$', EUR: '€', RUB: '₽' }
  return symbols[authStore.userCurrency] || '₸'
})

const categorizedTotal = computed(() =>
  form.categories.reduce((sum, c) => sum + (c.amount || 0), 0)
)

const formRequiredTotal = computed(() =>
  form.required_categories.reduce((sum, c) => sum + (Number(c.amount) || 0), 0)
)

const unaccounted = computed(() =>
  Math.max(0, form.total_expense - categorizedTotal.value)
)

const surplus = computed(() =>
  form.total_income - form.total_expense
)

const categorizedImportTotal = computed(() =>
  categoriesDraft.value.reduce((sum, c) => sum + (Number(c.amount) || 0), 0)
)

const requiredTotal = computed(() =>
  requiredDraft.value.reduce((sum, c) => sum + (Number(c.amount) || 0), 0)
)

const moneyAfterRequired = computed(() => {
  if (!importedAnalysis.value) return 0
  return importedAnalysis.value.summary.balanceLeft - requiredTotal.value
})

const safetyClass = computed(() => {
  if (!importedAnalysis.value) return ''
  const expense = importedAnalysis.value.summary.totalExpense || 0
  const income = importedAnalysis.value.summary.totalIncome || 0
  const ratio = income > 0 ? (expense + requiredTotal.value) / income : 1
  if (moneyAfterRequired.value < 0 || ratio > 0.9) return 'danger'
  if (ratio > 0.7) return 'warning'
  return 'success'
})

const safetyText = computed(() => {
  if (!importedAnalysis.value) return ''
  if (safetyClass.value === 'danger') return 'Риск высокий: обязательные платежи почти съедают свободный остаток.'
  if (safetyClass.value === 'warning') return 'Нагрузка заметная: стоит держать расходы под контролем.'
  return 'Траты выглядят безопасно относительно доступных денег.'
})

const chartLabels = computed(() =>
  importedAnalysis.value?.chartData.map(item => item.date) || []
)

const chartConfig = computed(() => ({
  labels: chartLabels.value,
  datasets: [
    {
      label: 'Расходы',
      data: importedAnalysis.value?.chartData.map(item => item.expense) || [],
      borderColor: '#EF4444',
      backgroundColor: 'rgba(239, 68, 68, 0.14)',
      tension: 0.28,
      fill: true,
      pointRadius: chartLabels.value.length > 45 ? 1.5 : 3,
      pointHoverRadius: 5,
    },
  ],
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { intersect: false, mode: 'index' },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: context => formatMoney(context.parsed.y),
      },
    },
  },
  scales: {
    x: {
      grid: { color: 'rgba(148, 163, 184, 0.08)' },
      ticks: {
        color: '#94A3B8',
        maxRotation: 0,
        autoSkip: chartLabels.value.length > 35,
        callback(value, index) {
          const label = this.getLabelForValue(value)
          if (chartLabels.value.length > 45 && index % 5 !== 0) return ''
          return formatShortDate(label)
        },
      },
    },
    y: {
      beginAtZero: true,
      grid: { color: 'rgba(148, 163, 184, 0.08)' },
      ticks: {
        color: '#94A3B8',
        callback: value => new Intl.NumberFormat('ru-RU').format(value),
      },
    },
  },
}))

const chartMonths = computed(() => {
  const formatter = new Intl.DateTimeFormat('ru-RU', { month: 'long', year: 'numeric' })
  return [...new Set(chartLabels.value.map(date => formatter.format(new Date(date))))]
})

function formatMoney(val) {
  if (val == null || Number.isNaN(Number(val))) return `0 ${currencySymbol.value}`
  return new Intl.NumberFormat('ru-RU').format(Math.round(Number(val))) + ' ' + currencySymbol.value
}

function formatShortDate(value) {
  if (!value) return ''
  const [, month, day] = value.split('-')
  return `${day}.${month}`
}

function openForm(report = null) {
  if (report) {
    editing.value = report.id
    form.period = report.period
    form.total_income = report.total_income
    form.total_expense = report.total_expense
    form.categories = (report.categories || []).map(c => ({ ...c }))
    form.required_categories = (report.required_categories || []).map(c => ({ ...c }))
    showCategories.value = true
    showRequiredCategories.value = true
  } else {
    editing.value = null
    form.period = new Date().toISOString().slice(0, 7)
    form.total_income = 0
    form.total_expense = 0
    form.categories = getDefaultCategories()
    form.required_categories = []
    showCategories.value = true
    showRequiredCategories.value = false
  }
  showForm.value = true
}

function getDefaultCategories() {
  return standardCategories.value.slice(0, defaultCategoryCount).map(name => ({
    name,
    amount: 0,
    custom: false,
  }))
}

function addCategory() {
  form.categories.push({ name: '', amount: 0, custom: true })
}

function removeCategory(index) {
  form.categories.splice(index, 1)
}

function addFormRequiredCategory() {
  form.required_categories.push({
    name: '',
    amount: 0,
    period: 'monthly',
    duration: '',
  })
}

function removeFormRequiredCategory(index) {
  form.required_categories.splice(index, 1)
}

function addImportedCategory() {
  categoriesDraft.value.push({ name: '', amount: 0, custom: true })
}

function removeImportedCategory(index) {
  categoriesDraft.value.splice(index, 1)
}

function addRequiredCategory() {
  requiredDraft.value.push({
    name: '',
    amount: 0,
    period: 'monthly',
    duration: '',
  })
}

function removeRequiredCategory(index) {
  requiredDraft.value.splice(index, 1)
}

function inferImportedPeriod() {
  const firstDate = importedAnalysis.value?.chartData?.[0]?.date
  return firstDate ? firstDate.slice(0, 7) : new Date().toISOString().slice(0, 7)
}

function extractPaymentDay(duration) {
  const match = String(duration || '').trim().match(/^(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})$/)
  if (!match) return undefined
  const day = Number(match[1])
  return day >= 1 && day <= 31 ? String(day) : undefined
}

function normalizeRequiredPaymentDate(duration) {
  const raw = String(duration || '').trim()
  const match = raw.match(/^(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})$/)
  if (!match) return raw || undefined

  const day = match[1].padStart(2, '0')
  const month = match[2].padStart(2, '0')
  const year = match[3].length === 2 ? `20${match[3]}` : match[3]
  return `${year}-${month}-${day}`
}

function normalizeRequiredCategory(category) {
  const duration = String(category.duration || '').trim()
  return {
    name: category.name,
    amount: Number(category.amount),
    period: 'monthly',
    duration: duration || undefined,
    paymentDate: normalizeRequiredPaymentDate(duration) || extractPaymentDay(duration),
  }
}

async function handlePdfUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return

  importError.value = ''
  try {
    const analysis = await reportsStore.importKaspiPdf(file)
    importedAnalysis.value = analysis
    const hasAiCategories = analysis.categories.some(c => Number(c.amount) > 0)
    categoriesDraft.value = (
      hasAiCategories
        ? analysis.categories.filter(c => Number(c.amount) > 0)
        : analysis.categories.slice(0, defaultCategoryCount)
    ).map(category => ({ ...category }))
    requiredDraft.value = []
  } catch (err) {
    importError.value = reportsStore.error || 'Не удалось импортировать Kaspi PDF'
  } finally {
    event.target.value = ''
  }
}

async function saveImportedReport() {
  if (!importedAnalysis.value) return
  const payload = {
    period: inferImportedPeriod(),
    total_income: importedAnalysis.value.summary.totalIncome,
    total_expense: importedAnalysis.value.summary.totalExpense,
    categories: categoriesDraft.value
      .filter(category => category.name && Number(category.amount) > 0)
      .map(category => ({
        name: category.name,
        amount: Number(category.amount),
        custom: !standardCategories.value.includes(category.name),
      })),
    required_categories: requiredDraft.value
      .filter(category => category.name && Number(category.amount) > 0)
      .map(normalizeRequiredCategory),
  }
  await reportsStore.createReport(payload)
  importedAnalysis.value = null
  categoriesDraft.value = []
  requiredDraft.value = []
  importError.value = ''
}

async function sendReportToAi(report) {
  aiError.value = ''
  sendingReportToAi.value = report.id
  // Navigate immediately — AIChatView shows loading and then navigates to the chat
  await router.push({ name: 'ai-chat' })
  try {
    await aiChatsStore.analyzeReport(report.id)
    // AIChatView watches pendingChatId and navigates to the specific chat
  } catch {
    // aiChatsStore.error will be displayed inside AIChatView
  } finally {
    sendingReportToAi.value = null
  }
}

async function handleSave() {
  const data = {
    period: form.period,
    total_income: form.total_income,
    total_expense: form.total_expense,
    categories: form.categories.filter(c => c.name && c.amount > 0),
    required_categories: form.required_categories
      .filter(c => c.name && Number(c.amount) > 0)
      .map(normalizeRequiredCategory),
  }
  try {
    if (editing.value) {
      await reportsStore.updateReport(editing.value, data)
    } else {
      await reportsStore.createReport(data)
    }
    showForm.value = false
  } catch (err) {
    // handled in store
  }
}

async function confirmDelete(id) {
  if (confirm('Delete this report?')) {
    await reportsStore.deleteReport(id)
  }
}

function expenseRatio(report) {
  if (!report.total_income) return 0
  return Math.round((report.total_expense / report.total_income) * 100)
}

function expenseRatioClass(report) {
  const r = expenseRatio(report)
  if (r > 100) return 'ratio-danger'
  if (r > 80) return 'ratio-warning'
  return 'ratio-good'
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}

.import-panel {
  background: var(--bg-glass);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.import-status {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--text-secondary);
}

.analysis-layout {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.analysis-head,
.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.analysis-head h2,
.section-title-row h3 {
  color: var(--text-primary);
  font-size: 1.1rem;
  margin: 0;
}

.analysis-head p,
.section-title-row span {
  color: var(--text-muted);
  margin: 0;
  font-size: 0.85rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
}

.summary-item {
  background: rgba(15, 23, 42, 0.38);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 0.9rem;
}

.summary-item span {
  display: block;
  color: var(--text-muted);
  font-size: 0.78rem;
  margin-bottom: 0.3rem;
}

.summary-item strong {
  font-size: 1rem;
}

.income { color: var(--success-light); }
.expense { color: var(--danger-light); }

.summary-details {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem 1rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  border-bottom: 1px solid var(--border-color);
  padding: 0.45rem 0;
  color: var(--text-secondary);
}

.detail-row strong {
  color: var(--text-primary);
  white-space: nowrap;
}

.alert-box {
  border-radius: var(--radius-sm);
  padding: 0.75rem 0.9rem;
  font-size: 0.9rem;
}

.alert-box.warning {
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.25);
  color: var(--warning-light);
}

.alert-box.danger {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.25);
  color: var(--danger-light);
}

.warnings-list {
  display: grid;
  gap: 0.5rem;
}

.chart-section,
.manual-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.chart-frame {
  height: 330px;
  min-height: 260px;
}

.month-strip {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.month-strip span {
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: 999px;
  padding: 0.15rem 0.6rem;
  font-size: 0.78rem;
}

.manual-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr);
  gap: 1.25rem;
}

.editable-row,
.required-row,
.required-form-row {
  display: grid;
  gap: 0.5rem;
  align-items: center;
}

.editable-row {
  grid-template-columns: minmax(0, 1fr) 150px 36px;
}

.required-row {
  grid-template-columns: minmax(130px, 1fr) 120px minmax(180px, 1fr) 36px;
}

.required-form-row {
  grid-template-columns: minmax(120px, 1fr) 110px minmax(180px, 1fr) 36px;
}

.amount-input {
  min-width: 0;
}

.safety-line {
  border-radius: var(--radius-sm);
  padding: 0.75rem;
  font-size: 0.9rem;
}

.safety-line.success {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success-light);
}

.safety-line.warning {
  background: rgba(245, 158, 11, 0.1);
  color: var(--warning-light);
}

.safety-line.danger {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger-light);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-box {
  width: 100%;
  max-width: 760px;
  padding: 2rem;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  color: var(--text-primary);
}

.form-group { display: flex; flex-direction: column; margin-bottom: 1rem; }
.form-row { display: flex; gap: 1rem; }
.flex-1 { flex: 1; }
.w-100 { width: 100%; }

.categories-section {
  margin: 1rem 0;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.85rem 1rem;
  cursor: pointer;
  background: var(--bg-tertiary);
}

.section-header h3 {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0;
}

.toggle-icon {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.categories-list {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.category-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.cat-name { flex: 2; }
.cat-amount { flex: 1; }

.btn-remove {
  background: rgba(239,68,68,0.1);
  border: 1px solid rgba(239,68,68,0.2);
  color: var(--danger-light);
  padding: 0.4rem 0.55rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
}

.btn-sm { padding: 0.4rem 1rem; font-size: 0.8rem; }

.balance-preview {
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  padding: 1rem;
  margin: 1rem 0;
}

.balance-row {
  display: flex;
  justify-content: space-between;
  padding: 0.3rem 0;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.balance-value { font-weight: 600; }
.balance-value.success { color: var(--success); }
.balance-value.danger { color: var(--danger); }
.balance-value.warning { color: var(--warning); }

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.loading-grid {
  display: grid;
  gap: 1rem;
}

.reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(340px, 100%), 1fr));
  gap: 1rem;
}

.report-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  gap: 0.5rem;
}

.report-period {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--primary-light);
  margin-bottom: 0.1rem;
}

.report-cat-count {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.report-header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.surplus-pill {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 700;
  white-space: nowrap;
}

.pill-pos { background: rgba(16, 185, 129, 0.15); color: var(--success-light); }
.pill-neg { background: rgba(239, 68, 68, 0.15);  color: var(--danger-light); }

/* Stats row */
.report-stats-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.85rem;
}

.rs-block {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  background: rgba(15, 23, 42, 0.3);
  border-radius: var(--radius-sm);
  padding: 0.6rem 0.75rem;
  min-width: 0;
}

.rs-icon-wrap {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  flex-shrink: 0;
}

.rs-inc { background: rgba(16, 185, 129, 0.15); color: var(--success); }
.rs-exp { background: rgba(239, 68, 68, 0.15);  color: var(--danger); }

/* Ratio bar */
.report-ratio-bar {
  margin-bottom: 0.85rem;
}

.ratio-track {
  height: 6px;
  background: rgba(148, 163, 184, 0.1);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.35rem;
}

.ratio-fill {
  height: 100%;
  border-radius: 3px;
  transition: width var(--transition-slow);
}

.ratio-good    { background: linear-gradient(90deg, var(--success), #059669); }
.ratio-warning { background: linear-gradient(90deg, var(--warning), #D97706); }
.ratio-danger  { background: linear-gradient(90deg, var(--danger), #DC2626); }

.ratio-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.72rem;
  color: var(--text-muted);
}

.ratio-unaccounted { color: var(--warning-light); }

/* Category chips */
.report-cats-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-top: 0.25rem;
}

.cat-chip {
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.15);
  color: var(--text-secondary);
  border-radius: 20px;
  padding: 0.2rem 0.55rem;
  font-size: 0.72rem;
  font-weight: 500;
}

.cat-chip-more {
  background: var(--bg-tertiary);
  border-color: var(--border-color);
  color: var(--text-muted);
}

.report-actions { display: flex; gap: 0.25rem; }

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.8rem;
  color: var(--text-secondary);
  padding: 0.25rem;
  opacity: 0.8;
  transition: opacity var(--transition-fast);
}

.btn-icon:hover { opacity: 1; }

.btn-icon-round {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0.35rem 0.45rem;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  font-size: 1rem;
}

.btn-icon-round:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.rs-label { font-size: 0.72rem; color: var(--text-muted); margin-bottom: 0.15rem; }
.rs-value { font-size: 0.9rem; font-weight: 700; }
.rs-value.income { color: var(--success); }
.rs-value.expense { color: var(--danger); }
.warning-text { color: var(--warning); }

/* .report-categories removed — replaced by .report-cats-row */

.report-ai-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1rem;
}

.report-ai-actions .btn-sm {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

@media (max-width: 1100px) {
  .summary-grid,
  .manual-grid {
    grid-template-columns: 1fr 1fr;
  }

  .required-row,
  .required-form-row {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 1rem;
  }

  .header-actions,
  .analysis-head,
  .section-title-row {
    align-items: stretch;
    flex-direction: column;
  }

  .form-row,
  .category-row {
    flex-direction: column;
  }

  .summary-grid,
  .summary-details,
  .manual-grid,
  .editable-row,
  .required-row,
  .required-form-row {
    grid-template-columns: 1fr;
  }

  .chart-frame {
    height: 240px;
  }

  .import-modal {
    padding: 0.75rem;
    overflow-x: hidden;
  }

  .modal-inner {
    max-height: 85vh;
    overflow-y: auto;
    padding: 1.25rem;
  }
}
</style>
