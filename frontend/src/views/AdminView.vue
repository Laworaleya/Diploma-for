<template>
  <div class="page-container">
    <div class="admin-header">
      <div>
        <h1 class="page-title">Панель администратора</h1>
        <p class="page-subtitle">Управление пользователями и мониторинг системы</p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key)"
      >
        <i :class="tab.icon"></i>
        {{ tab.label }}
      </button>
    </div>

    <!-- Error banner -->
    <div v-if="adminStore.error" class="alert-error">
      <i class="pi pi-exclamation-triangle"></i>
      {{ adminStore.error }}
    </div>

    <!-- ── TAB: USERS ─────────────────────────────────────────────────────── -->
    <div v-if="activeTab === 'users'" class="tab-content">
      <div class="section-header">
        <span class="section-title">Пользователи ({{ adminStore.users.length }})</span>
        <button class="btn-outline btn-sm" @click="adminStore.fetchUsers()">
          <i class="pi pi-refresh"></i> Обновить
        </button>
      </div>

      <div v-if="adminStore.loading" class="loading-state">
        <i class="pi pi-spin pi-spinner"></i> Загрузка...
      </div>

      <div v-else-if="adminStore.users.length === 0" class="empty-state">
        Пользователи не найдены
      </div>

      <div v-else class="table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Имя</th>
              <th>Роль</th>
              <th>Отчётов</th>
              <th>Дата регистрации</th>
              <th>Статус</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="user in adminStore.users"
              :key="user.id"
              :class="{ 'row-blocked': user.is_blocked }"
            >
              <td class="cell-email">{{ user.email }}</td>
              <td>{{ user.name || '—' }}</td>
              <td>
                <span class="badge" :class="user.role === 'admin' ? 'badge-admin' : 'badge-user'">
                  {{ user.role }}
                </span>
              </td>
              <td class="cell-center">{{ user.report_count ?? 0 }}</td>
              <td class="cell-date">{{ formatDate(user.created_at) }}</td>
              <td>
                <span v-if="user.is_blocked" class="badge badge-blocked">Заблокирован</span>
                <span v-else class="badge badge-active">Активен</span>
              </td>
              <td class="cell-actions">
                <button
                  v-if="!user.is_blocked && user.role !== 'admin'"
                  class="btn-action btn-warn"
                  title="Заблокировать"
                  @click="handleBlock(user)"
                >
                  <i class="pi pi-ban"></i>
                </button>
                <button
                  v-if="user.role !== 'admin'"
                  class="btn-action btn-danger"
                  title="Удалить"
                  @click="handleDelete(user)"
                >
                  <i class="pi pi-trash"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── TAB: STATS ─────────────────────────────────────────────────────── -->
    <div v-if="activeTab === 'stats'" class="tab-content">
      <div class="section-header">
        <span class="section-title">Статистика системы</span>
        <button class="btn-outline btn-sm" @click="adminStore.fetchStats()">
          <i class="pi pi-refresh"></i> Обновить
        </button>
      </div>

      <div v-if="adminStore.loading" class="loading-state">
        <i class="pi pi-spin pi-spinner"></i> Загрузка...
      </div>

      <div v-else-if="adminStore.stats" class="stats-grid">
        <div class="stat-card stat-card-users">
          <div class="stat-icon"><i class="pi pi-users"></i></div>
          <div class="stat-value">{{ adminStore.stats.total_users }}</div>
          <div class="stat-label">Всего пользователей</div>
          <div class="stat-accent"></div>
        </div>
        <div class="stat-card stat-card-reports">
          <div class="stat-icon"><i class="pi pi-file"></i></div>
          <div class="stat-value">{{ adminStore.stats.total_reports }}</div>
          <div class="stat-label">Всего отчётов</div>
          <div class="stat-accent"></div>
        </div>
        <div class="stat-card stat-card-imports">
          <div class="stat-icon"><i class="pi pi-upload"></i></div>
          <div class="stat-value">{{ adminStore.stats.total_kaspi_imports }}</div>
          <div class="stat-label">PDF-импортов Kaspi</div>
          <div class="stat-accent"></div>
        </div>
        <div class="stat-card stat-card-chats">
          <div class="stat-icon"><i class="pi pi-comments"></i></div>
          <div class="stat-value">{{ adminStore.stats.total_ai_chats }}</div>
          <div class="stat-label">AI-чатов</div>
          <div class="stat-accent"></div>
        </div>
      </div>

      <div v-else class="empty-state">Нет данных</div>
    </div>

    <!-- ── TAB: AI MONITOR ────────────────────────────────────────────────── -->
    <div v-if="activeTab === 'ai'" class="tab-content">
      <div class="section-header">
        <span class="section-title">AI мониторинг</span>
        <button class="btn-outline btn-sm" @click="adminStore.fetchAiStats()">
          <i class="pi pi-refresh"></i> Обновить
        </button>
      </div>

      <div v-if="adminStore.loading" class="loading-state">
        <i class="pi pi-spin pi-spinner"></i> Загрузка...
      </div>

      <div v-else-if="adminStore.aiStats">
        <div class="ai-error-banner">
          <i class="pi pi-exclamation-circle"></i>
          <span>Всего ошибок AI: <strong>{{ adminStore.aiStats.total_ai_errors }}</strong></span>
        </div>

        <div class="section-title mt-section">Топ-10 вопросов пользователей</div>
        <div v-if="adminStore.aiStats.top_questions.length === 0" class="empty-state">
          Вопросов пока нет
        </div>
        <div v-else class="questions-list">
          <div
            v-for="(item, idx) in adminStore.aiStats.top_questions"
            :key="idx"
            class="question-row"
          >
            <span class="question-rank">#{{ idx + 1 }}</span>
            <span class="question-text">{{ item.question }}</span>
            <span class="question-count">{{ item.count }}×</span>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">Нет данных</div>
    </div>

    <!-- ── TAB: IMPORT ERRORS ─────────────────────────────────────────────── -->
    <div v-if="activeTab === 'errors'" class="tab-content">
      <div class="section-header">
        <span class="section-title">Ошибки импорта PDF (последние 50)</span>
        <button class="btn-outline btn-sm" @click="adminStore.fetchImportErrors()">
          <i class="pi pi-refresh"></i> Обновить
        </button>
      </div>

      <div v-if="adminStore.loading" class="loading-state">
        <i class="pi pi-spin pi-spinner"></i> Загрузка...
      </div>

      <div v-else-if="adminStore.importErrors.length === 0" class="empty-state">
        Ошибок импорта нет
      </div>

      <div v-else class="table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Дата</th>
              <th>User ID</th>
              <th>Файл</th>
              <th>Ошибка</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="err in adminStore.importErrors" :key="err.id">
              <td class="cell-date">{{ formatDate(err.created_at) }}</td>
              <td class="cell-id">{{ err.user_id }}</td>
              <td>{{ err.filename }}</td>
              <td class="cell-error">{{ err.error_message }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Confirm delete modal -->
    <div v-if="confirmTarget" class="modal-backdrop" @click.self="confirmTarget = null">
      <div class="modal-box">
        <h3 class="modal-title">Удалить пользователя?</h3>
        <p class="modal-body">
          Будут удалены <strong>{{ confirmTarget.email }}</strong> и все его данные:
          отчёты, цели, чаты, платежи. Это действие необратимо.
        </p>
        <div class="modal-actions">
          <button class="btn-outline" @click="confirmTarget = null">Отмена</button>
          <button class="btn-danger-solid" @click="confirmDelete">Удалить</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAdminStore } from '../stores/admin'

const adminStore = useAdminStore()

const activeTab = ref('users')
const confirmTarget = ref(null)

const tabs = [
  { key: 'users',  label: 'Пользователи',    icon: 'pi pi-users' },
  { key: 'stats',  label: 'Статистика',       icon: 'pi pi-chart-bar' },
  { key: 'ai',     label: 'AI мониторинг',    icon: 'pi pi-microchip-ai' },
  { key: 'errors', label: 'Ошибки импорта',   icon: 'pi pi-file-excel' },
]

const tabLoaders = {
  users:  () => adminStore.fetchUsers(),
  stats:  () => adminStore.fetchStats(),
  ai:     () => adminStore.fetchAiStats(),
  errors: () => adminStore.fetchImportErrors(),
}

function switchTab(key) {
  activeTab.value = key
  adminStore.error = null
  tabLoaders[key]()
}

async function handleBlock(user) {
  try {
    await adminStore.blockUser(user.id)
  } catch {
    // error shown via adminStore.error
  }
}

function handleDelete(user) {
  confirmTarget.value = user
}

async function confirmDelete() {
  if (!confirmTarget.value) return
  try {
    await adminStore.deleteUser(confirmTarget.value.id)
  } catch {
    // error shown via adminStore.error
  } finally {
    confirmTarget.value = null
  }
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

onMounted(() => {
  adminStore.fetchUsers()
})
</script>

<style scoped>
/* ── Layout ──────────────────────────────────────────────────────────────── */
.page-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1.5rem 1.5rem 4rem;
}

.admin-header {
  margin-bottom: 1.5rem;
}

.page-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.25rem;
}

.page-subtitle {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin: 0;
}

/* ── Tab bar ─────────────────────────────────────────────────────────────── */
.tab-bar {
  display: flex;
  gap: 0.25rem;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.6rem 1.1rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-muted);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  color: var(--primary-light);
  border-bottom-color: var(--primary-light);
}

/* ── Section header ──────────────────────────────────────────────────────── */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.mt-section {
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  display: block;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.9rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-outline:hover {
  border-color: var(--primary-light);
  color: var(--primary-light);
}

.btn-sm { padding: 0.35rem 0.7rem; font-size: 0.78rem; }

.btn-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.8rem;
  transition: all var(--transition-fast);
}

.btn-warn {
  background: rgba(245, 158, 11, 0.12);
  color: #f59e0b;
}

.btn-warn:hover {
  background: rgba(245, 158, 11, 0.25);
}

.btn-danger {
  background: rgba(239, 68, 68, 0.12);
  color: var(--danger, #ef4444);
}

.btn-danger:hover {
  background: rgba(239, 68, 68, 0.25);
}

.btn-danger-solid {
  padding: 0.5rem 1.2rem;
  background: var(--danger, #ef4444);
  border: none;
  border-radius: var(--radius-sm);
  color: #fff;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-danger-solid:hover {
  background: #dc2626;
}

/* ── Alert ───────────────────────────────────────────────────────────────── */
.alert-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--radius-md);
  color: #fca5a5;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

/* ── Loading / Empty ─────────────────────────────────────────────────────── */
.loading-state,
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.loading-state i {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  display: block;
}

/* ── Table ───────────────────────────────────────────────────────────────── */
.table-wrap {
  overflow-x: auto;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.admin-table thead {
  background: rgba(148, 163, 184, 0.05);
}

.admin-table th {
  padding: 0.7rem 1rem;
  text-align: left;
  color: var(--text-muted);
  font-weight: 600;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--border-color);
  white-space: nowrap;
}

.admin-table td {
  padding: 0.65rem 1rem;
  color: var(--text-secondary);
  border-bottom: 1px solid rgba(148, 163, 184, 0.07);
  vertical-align: middle;
}

.admin-table tbody tr:last-child td {
  border-bottom: none;
}

.admin-table tbody tr:hover {
  background: rgba(148, 163, 184, 0.04);
}

.row-blocked td {
  opacity: 0.55;
}

.cell-email {
  font-weight: 500;
  color: var(--text-primary);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-center { text-align: center; }

.cell-date {
  white-space: nowrap;
  font-size: 0.78rem;
  color: var(--text-muted);
}

.cell-id {
  font-size: 0.72rem;
  color: var(--text-muted);
  font-family: monospace;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-error {
  max-width: 380px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.78rem;
  color: #fca5a5;
}

.cell-actions {
  display: flex;
  gap: 0.35rem;
  white-space: nowrap;
}

/* ── Badges ──────────────────────────────────────────────────────────────── */
.badge {
  display: inline-block;
  padding: 0.18rem 0.55rem;
  border-radius: 99px;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.badge-admin   { background: rgba(99, 102, 241, 0.18); color: var(--primary-light); }
.badge-user    { background: rgba(148, 163, 184, 0.12); color: var(--text-muted); }
.badge-active  { background: rgba(16, 185, 129, 0.15); color: #6ee7b7; }
.badge-blocked { background: rgba(239, 68, 68, 0.15);  color: #fca5a5; }

/* ── Stats grid ──────────────────────────────────────────────────────────── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-card {
  position: relative;
  overflow: hidden;
  background: var(--bg-glass, rgba(30, 41, 59, 0.6));
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 1.25rem 1.25rem 1rem;
}

.stat-icon {
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
  opacity: 0.8;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
  margin-bottom: 0.35rem;
}

.stat-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 500;
}

.stat-accent {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.stat-card-users  .stat-icon { color: var(--primary-light); }
.stat-card-users  .stat-accent { background: var(--primary-light); }
.stat-card-reports .stat-icon { color: #6ee7b7; }
.stat-card-reports .stat-accent { background: #10b981; }
.stat-card-imports .stat-icon { color: #fbbf24; }
.stat-card-imports .stat-accent { background: #f59e0b; }
.stat-card-chats  .stat-icon { color: #a78bfa; }
.stat-card-chats  .stat-accent { background: #8b5cf6; }

/* ── AI monitor ──────────────────────────────────────────────────────────── */
.ai-error-banner {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.9rem 1.2rem;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.ai-error-banner i { color: #fca5a5; font-size: 1.1rem; }
.ai-error-banner strong { color: #fca5a5; }

.questions-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.question-row {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  padding: 0.6rem 0.9rem;
  background: var(--bg-glass, rgba(30, 41, 59, 0.5));
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
}

.question-rank {
  flex-shrink: 0;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  width: 24px;
}

.question-text {
  flex: 1;
  font-size: 0.85rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.question-count {
  flex-shrink: 0;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--primary-light);
}

/* ── Modal ───────────────────────────────────────────────────────────────── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
  padding: 1rem;
}

.modal-box {
  background: #1e293b;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 1.75rem;
  max-width: 420px;
  width: 100%;
  box-shadow: var(--shadow-md);
}

.modal-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.75rem;
}

.modal-body {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 1.25rem;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}
</style>
