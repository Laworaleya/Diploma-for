<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">Регулярные платежи</h1>
        <p class="page-subtitle">Обязательные платежи и напоминания о ближайших списаниях</p>
      </div>
      <button class="btn-primary-gradient" type="button" @click="openForm()">
        + Добавить платеж
      </button>
    </div>

    <div class="stats-grid">
      <div class="stat-card sc-neutral">
        <div class="sc-icon"><i class="pi pi-list"></i></div>
        <div>
          <div class="stat-value">{{ paymentsStore.sortedPayments.length }}</div>
          <div class="stat-label">Всего платежей</div>
        </div>
      </div>
      <div class="stat-card sc-primary">
        <div class="sc-icon"><i class="pi pi-credit-card"></i></div>
        <div>
          <div class="stat-value">{{ formatMoney(monthlyTotal) }}</div>
          <div class="stat-label">Ежемесячная нагрузка</div>
        </div>
      </div>
      <div class="stat-card" :class="urgentCount > 0 ? 'sc-urgent' : 'sc-safe'">
        <div class="sc-icon"><i class="pi pi-clock"></i></div>
        <div>
          <div class="stat-value">{{ urgentCount }}</div>
          <div class="stat-label">Срочные и сегодня</div>
        </div>
      </div>
    </div>

    <div v-if="paymentsStore.error" class="alert-box danger">
      {{ paymentsStore.error }}
    </div>

    <div v-if="paymentsStore.loading && !paymentsStore.payments.length" class="loading-grid">
      <div class="skeleton" style="height:96px" v-for="i in 4" :key="i"></div>
    </div>

    <div v-else-if="!paymentsStore.sortedPayments.length" class="empty-state">
      <div class="empty-icon"><i class="pi pi-refresh"></i></div>
      <h3>Регулярных платежей пока нет</h3>
      <p>Добавьте платеж вручную или создайте отчет с обязательными категориями.</p>
      <button class="btn-primary-gradient" type="button" @click="openForm()">+ Добавить платеж</button>
    </div>

    <div v-else class="payments-list">
      <article
        v-for="payment in paymentsStore.sortedPayments"
        :key="payment.id"
        class="payment-row"
        :class="payment.status"
      >
        <div class="payment-icon" :class="payment.status">
          {{ payment.title.slice(0, 1).toUpperCase() }}
        </div>

        <div class="payment-main">
          <div class="payment-title-row">
            <h2>{{ payment.title }}</h2>
            <span class="source-badge" v-if="payment.source === 'requiredCategory'">
              из отчета
            </span>
          </div>
          <p>{{ formatStatus(payment.status) }}</p>
        </div>

        <div class="payment-cell">
          <span>Сумма</span>
          <strong>{{ formatMoney(payment.amount) }}</strong>
        </div>

        <div class="payment-cell">
          <span>Следующий платеж</span>
          <strong>{{ formatDate(payment.nextPaymentDate) }}</strong>
        </div>

        <div class="payment-cell days-cell">
          <span>Осталось</span>
          <strong :class="payment.status">{{ formatDays(getDaysUntilPayment(payment.nextPaymentDate)) }}</strong>
        </div>

        <div class="row-actions">
          <button class="btn-icon-text" type="button" @click="openForm(payment)">Edit</button>
          <button class="btn-remove" type="button" @click="deletePayment(payment.id)">x</button>
        </div>
      </article>
    </div>

    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal-box glass-card">
        <h2 class="modal-title">{{ editingId ? 'Редактировать платеж' : 'Новый регулярный платеж' }}</h2>

        <form @submit.prevent="savePayment">
          <div class="form-group">
            <label class="form-label-dark">Название платежа</label>
            <input v-model="form.title" class="form-control-dark" required placeholder="Например, Кредит" />
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label class="form-label-dark">Сумма платежа</label>
              <input v-model.number="form.amount" type="number" min="0" step="1" class="form-control-dark" required />
            </div>
            <div class="form-group flex-1">
              <label class="form-label-dark">Дата платежа</label>
              <input v-model="form.originalPaymentDate" type="date" class="form-control-dark" required />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label class="form-label-dark">Цвет иконки</label>
              <select v-model="form.iconColor" class="form-select-dark">
                <option value="purple">Фиолетовый</option>
                <option value="green">Зеленый</option>
                <option value="yellow">Желтый</option>
                <option value="orange">Оранжевый</option>
                <option value="red">Красный</option>
              </select>
            </div>
            <div class="form-group flex-1">
              <label class="form-label-dark">Периодичность</label>
              <select v-model="form.period" class="form-select-dark">
                <option value="monthly">Каждый месяц</option>
              </select>
            </div>
          </div>

          <div class="preview-box" v-if="form.originalPaymentDate">
            <span>Следующая дата будет рассчитана автоматически.</span>
          </div>

          <div class="form-actions">
            <button type="button" class="btn-glass" @click="closeForm">Отмена</button>
            <button type="submit" class="btn-primary-gradient" :disabled="paymentsStore.loading">
              <span v-if="paymentsStore.loading" class="spinner"></span>
              Сохранить
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRecurringPaymentsStore } from '../stores/recurringPayments'

const paymentsStore = useRecurringPaymentsStore()
const authStore = useAuthStore()

const showForm = ref(false)
const editingId = ref(null)

const form = reactive({
  title: '',
  amount: 0,
  originalPaymentDate: '',
  iconColor: 'purple',
  period: 'monthly',
})

onMounted(() => {
  paymentsStore.fetchPayments()
})

const currencySymbol = computed(() => {
  const symbols = { KZT: '₸', USD: '$', EUR: '€', RUB: '₽' }
  return symbols[authStore.userCurrency] || '₸'
})

const monthlyTotal = computed(() =>
  paymentsStore.sortedPayments.reduce((sum, payment) => sum + Number(payment.amount || 0), 0)
)

const urgentCount = computed(() =>
  paymentsStore.sortedPayments.filter(payment =>
    payment.status === 'urgent' || payment.status === 'overdue'
  ).length
)

function openForm(payment = null) {
  if (payment) {
    editingId.value = payment.id
    form.title = payment.title
    form.amount = payment.amount
    form.originalPaymentDate = payment.originalPaymentDate
    form.iconColor = payment.manualIconColor || payment.iconColor || 'purple'
    form.period = payment.period || 'monthly'
  } else {
    editingId.value = null
    form.title = ''
    form.amount = 0
    form.originalPaymentDate = new Date().toISOString().slice(0, 10)
    form.iconColor = 'purple'
    form.period = 'monthly'
  }
  showForm.value = true
}

function closeForm() {
  showForm.value = false
}

async function savePayment() {
  const payload = {
    title: form.title,
    amount: form.amount,
    originalPaymentDate: form.originalPaymentDate,
    iconColor: form.iconColor,
    period: form.period,
  }

  if (editingId.value) {
    await paymentsStore.updatePayment(editingId.value, payload)
  } else {
    await paymentsStore.createPayment(payload)
  }
  closeForm()
}

async function deletePayment(id) {
  if (confirm('Удалить регулярный платеж?')) {
    await paymentsStore.deletePayment(id)
  }
}

function formatMoney(value) {
  return new Intl.NumberFormat('ru-RU').format(Math.round(Number(value || 0))) + ' ' + currencySymbol.value
}

function formatDate(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('ru-RU').format(new Date(value))
}

function getDaysUntilPayment(value) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const target = new Date(value)
  target.setHours(0, 0, 0, 0)
  return Math.round((target - today) / 86400000)
}

function formatDays(days) {
  if (days < 0) return `просрочено на ${Math.abs(days)} дн.`
  if (days === 0) return 'сегодня'
  return `${days} дн.`
}

function formatStatus(status) {
  const labels = {
    safe: 'до платежа больше недели',
    soon: 'платеж приближается',
    urgent: 'осталось 1-3 дня',
    overdue: 'сегодня или просрочено',
  }
  return labels[status] || status
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.sc-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.sc-neutral .sc-icon { background: var(--bg-tertiary); color: var(--text-secondary); }
.sc-primary .sc-icon { background: rgba(99, 102, 241, 0.15); color: var(--primary-light); }
.sc-primary { border-color: rgba(99, 102, 241, 0.2); }
.sc-urgent .sc-icon { background: rgba(239, 68, 68, 0.15); color: var(--danger-light); }
.sc-urgent { border-color: rgba(239, 68, 68, 0.3); }
.sc-safe .sc-icon { background: rgba(16, 185, 129, 0.15); color: var(--success); }
.sc-safe { border-color: rgba(16, 185, 129, 0.2); }

.payments-list {
  display: grid;
  gap: 0.75rem;
}

.payment-row {
  display: grid;
  grid-template-columns: 48px minmax(160px, 1fr) 140px 170px 120px auto;
  align-items: center;
  gap: 1rem;
  background: var(--bg-glass);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 1rem;
}

.payment-row.overdue {
  border-color: rgba(239, 68, 68, 0.55);
  background: rgba(239, 68, 68, 0.08);
}

.payment-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 800;
}

.payment-icon.safe { background: var(--success); }
.payment-icon.soon { background: var(--warning); }
.payment-icon.urgent { background: #f97316; }
.payment-icon.overdue { background: var(--danger); }

.payment-title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.payment-main h2 {
  margin: 0;
  font-size: 1rem;
}

.payment-main p {
  margin: 0.15rem 0 0;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.payment-cell {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.payment-cell span {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.payment-cell strong {
  color: var(--text-primary);
  font-size: 0.95rem;
}

.payment-cell strong.safe { color: var(--success-light); }
.payment-cell strong.soon { color: var(--warning-light); }
.payment-cell strong.urgent { color: #fb923c; }
.payment-cell strong.overdue { color: var(--danger-light); }

.source-badge {
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  border-radius: 999px;
  padding: 0.1rem 0.55rem;
  font-size: 0.72rem;
}

.row-actions {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.btn-icon-text {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.82rem;
}

.alert-box {
  border-radius: var(--radius-sm);
  padding: 0.75rem 0.9rem;
  margin-bottom: 1rem;
}

.alert-box.danger {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.25);
  color: var(--danger-light);
}

.loading-grid {
  display: grid;
  gap: 0.75rem;
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
  max-width: 620px;
  padding: 2rem;
}

.modal-title {
  color: var(--text-primary);
  font-size: 1.25rem;
  margin-bottom: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 1rem;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.flex-1 {
  flex: 1;
}

.preview-box {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  padding: 0.8rem 1rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.btn-remove {
  background: rgba(239,68,68,0.1);
  border: 1px solid rgba(239,68,68,0.2);
  color: var(--danger-light);
  padding: 0.4rem 0.55rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
}

@media (max-width: 1100px) {
  .payment-row {
    grid-template-columns: 48px minmax(160px, 1fr) 1fr 1fr;
  }

  .days-cell,
  .row-actions {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .page-header,
  .form-row {
    flex-direction: column;
  }

  .stats-grid,
  .payment-row {
    grid-template-columns: 1fr;
  }

  .days-cell,
  .row-actions {
    grid-column: auto;
  }
}
</style>
