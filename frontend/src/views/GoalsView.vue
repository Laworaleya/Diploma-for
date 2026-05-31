<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">{{ $t('goals.title') }}</h1>
        <p class="page-subtitle">{{ $t('goals.subtitle') }}</p>
      </div>
      <button class="btn-primary-gradient" @click="openForm()" id="new-goal-btn">
        + {{ $t('goals.new_goal') }}
      </button>
    </div>

    <div v-if="aiError" class="alert-box danger">{{ aiError }}</div>

    <!-- Goal Form Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal-box glass-card">
        <h2 class="modal-title">{{ editing ? $t('goals.edit_goal') : $t('goals.new_goal') }}</h2>

        <form @submit.prevent="handleSave">
          <div class="form-group">
            <label class="form-label-dark">{{ $t('goals.goal_title') }}</label>
            <input v-model="form.title" type="text" class="form-control-dark w-100" required id="goal-title" />
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label class="form-label-dark">{{ $t('goals.goal_type') }}</label>
              <select v-model="form.goal_type" class="form-select-dark w-100" id="goal-type">
                <option value="savings">{{ $t('goals.types.savings') }}</option>
                <option value="investment">{{ $t('goals.types.investment') }}</option>
                <option value="custom">{{ $t('goals.types.custom') }}</option>
              </select>
            </div>
            <div class="form-group flex-1">
              <label class="form-label-dark">{{ $t('goals.deadline') }}</label>
              <input v-model="form.deadline" type="date" class="form-control-dark w-100" id="goal-deadline" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label class="form-label-dark">{{ $t('goals.target_amount') }}</label>
              <input v-model.number="form.target_amount" type="number" min="1" step="1" class="form-control-dark w-100" required id="goal-target" />
            </div>
            <div class="form-group flex-1">
              <label class="form-label-dark">{{ $t('goals.current_amount') }}</label>
              <input v-model.number="form.current_amount" type="number" min="0" step="1" class="form-control-dark w-100" id="goal-current" />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label-dark">{{ $t('goals.description') }}</label>
            <textarea v-model="form.description" class="form-control-dark w-100" rows="2" id="goal-desc"></textarea>
          </div>

          <div class="form-actions">
            <button type="button" class="btn-glass" @click="showForm = false">{{ $t('goals.cancel') }}</button>
            <button type="submit" class="btn-primary-gradient" :disabled="goalsStore.loading" id="goal-save-btn">
              {{ $t('goals.save') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Goals List -->
    <div v-if="goalsStore.loading && !goalsStore.goals.length" class="loading-grid">
      <div class="skeleton" style="height:140px" v-for="i in 3" :key="i"></div>
    </div>

    <div v-else-if="goalsStore.goals.length === 0" class="empty-state">
      <h3>{{ $t('dashboard.no_goals') }}</h3>
    </div>

    <div v-else class="goals-grid">
      <Menu ref="goalMenu" :model="goalMenuItems" popup />
      <div
        class="goal-card premium-card"
        v-for="goal in goalsStore.goals"
        :key="goal.id"
        :class="{ completed: goal.status === 'completed' }"
      >
        <div class="goal-card-header">
          <div class="goal-badges">
            <span :class="['badge-glass', typeBadge(goal.goal_type)]">{{ $t('goals.types.' + goal.goal_type) }}</span>
            <span :class="['badge-glass', statusBadge(goal.status)]">{{ $t('goals.statuses.' + goal.status) }}</span>
          </div>
          <button
            class="btn-icon-round"
            @click="activeMenuGoal = goal; goalMenu.toggle($event)"
          >
            <i class="pi pi-ellipsis-v"></i>
          </button>
        </div>

        <h3 class="goal-name">{{ goal.title }}</h3>
        <p class="goal-desc" v-if="goal.description">{{ goal.description }}</p>

        <div class="goal-progress-section">
          <div class="progress-header">
            <span>{{ $t('goals.progress') }}</span>
            <span class="progress-pct">{{ goal.progress_percent }}%</span>
          </div>
          <div class="progress-bar-custom">
            <div
              class="progress-fill"
              :class="progressClass(goal.progress_percent)"
              :style="{ width: goal.progress_percent + '%' }"
            ></div>
          </div>
          <div class="progress-amounts">
            <span>{{ formatMoney(goal.current_amount) }}</span>
            <span class="text-muted">{{ formatMoney(goal.target_amount) }}</span>
          </div>
        </div>

        <div class="goal-footer" v-if="goal.deadline">
          <span class="text-muted">{{ $t('goals.deadline') }}: {{ goal.deadline }}</span>
        </div>

        <div class="goal-ai-actions">
          <button
            class="btn-glass btn-sm"
            type="button"
            :disabled="planningGoalId === goal.id"
            @click="planGoalWithAi(goal)"
          >
            <span v-if="planningGoalId === goal.id" class="spinner"></span>
            Составить план с AI
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Menu from 'primevue/menu'
import { useGoalsStore } from '../stores/goals'
import { useAuthStore } from '../stores/auth'
import { useAIChatsStore } from '../stores/aiChats'

const goalsStore = useGoalsStore()
const authStore = useAuthStore()
const aiChatsStore = useAIChatsStore()
const router = useRouter()

const showForm = ref(false)
const editing = ref(null)
const aiError = ref('')
const planningGoalId = ref(null)
const goalMenu = ref(null)
const activeMenuGoal = ref(null)

const goalMenuItems = computed(() => [
  {
    label: 'Редактировать',
    icon: 'pi pi-pencil',
    command: () => openForm(activeMenuGoal.value),
  },
  {
    label: 'Удалить',
    icon: 'pi pi-trash',
    command: () => confirmDelete(activeMenuGoal.value?.id),
  },
])

const form = reactive({
  title: '',
  goal_type: 'savings',
  target_amount: 0,
  current_amount: 0,
  deadline: '',
  description: '',
})

onMounted(() => {
  goalsStore.fetchGoals()
})

const currencySymbol = computed(() => {
  const symbols = { KZT: '₸', USD: '$', EUR: '€', RUB: '₽' }
  return symbols[authStore.userCurrency] || '₸'
})

function formatMoney(val) {
  return new Intl.NumberFormat('ru-RU').format(Math.round(val || 0)) + ' ' + currencySymbol.value
}

function typeBadge(type) {
  return { savings: 'badge-success', investment: 'badge-primary', custom: 'badge-warning' }[type] || 'badge-glass'
}

function statusBadge(status) {
  return { active: 'badge-primary', completed: 'badge-success', cancelled: 'badge-danger' }[status] || 'badge-glass'
}

function progressClass(pct) {
  if (pct >= 75) return 'success'
  if (pct >= 40) return 'warning'
  return ''
}

function openForm(goal = null) {
  if (goal) {
    editing.value = goal.id
    Object.assign(form, {
      title: goal.title,
      goal_type: goal.goal_type,
      target_amount: goal.target_amount,
      current_amount: goal.current_amount,
      deadline: goal.deadline || '',
      description: goal.description || '',
    })
  } else {
    editing.value = null
    Object.assign(form, {
      title: '',
      goal_type: 'savings',
      target_amount: 0,
      current_amount: 0,
      deadline: '',
      description: '',
    })
  }
  showForm.value = true
}

async function handleSave() {
  const data = { ...form }
  if (!data.deadline) data.deadline = null
  if (!data.description) data.description = null

  try {
    if (editing.value) {
      await goalsStore.updateGoal(editing.value, data)
    } else {
      await goalsStore.createGoal(data)
    }
    showForm.value = false
  } catch (err) {
    // handled in store
  }
}

async function planGoalWithAi(goal) {
  aiError.value = ''
  planningGoalId.value = goal.id
  try {
    const chat = await aiChatsStore.planGoal(goal.id)
    await router.push({ name: 'ai-chat-detail', params: { chatId: chat.id } })
  } catch (err) {
    aiError.value = aiChatsStore.error || 'Не удалось составить план с AI'
  } finally {
    planningGoalId.value = null
  }
}

async function confirmDelete(id) {
  if (confirm('Delete this goal?')) {
    await goalsStore.deleteGoal(id)
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
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
  max-width: 520px;
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

.alert-box {
  border-radius: var(--radius-sm);
  padding: 0.75rem 0.9rem;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.alert-box.danger {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.25);
  color: var(--danger-light);
}

.form-group { display: flex; flex-direction: column; margin-bottom: 1rem; }
.form-row { display: flex; gap: 1rem; }
.flex-1 { flex: 1; }
.w-100 { width: 100%; }

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

textarea.form-control-dark {
  resize: vertical;
  min-height: 60px;
}

.loading-grid { display: grid; gap: 1rem; }

.goals-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
}

.goal-card.completed {
  opacity: 0.7;
}

.goal-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
  gap: 0.5rem;
}

.goal-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.btn-icon-round {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0.3rem 0.4rem;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.btn-icon-round:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.goal-name {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 0.3rem;
  color: var(--text-primary);
}

.goal-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.goal-progress-section {
  margin: 1rem 0;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 0.4rem;
}

.progress-pct {
  font-weight: 700;
  color: var(--primary-light);
}

.progress-amounts {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  margin-top: 0.4rem;
  color: var(--text-secondary);
}

.text-muted { color: var(--text-muted); }

.goal-footer {
  font-size: 0.8rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
}

.goal-ai-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1rem;
}

.goal-ai-actions .btn-sm {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 1rem;
  font-size: 0.82rem;
}

@media (max-width: 768px) {
  .page-header { flex-direction: column; gap: 1rem; }
  .form-row { flex-direction: column; }
}
</style>
