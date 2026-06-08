<template>
  <div class="ai-page" :class="{ 'has-chat': !!activeChatId }">
    <!-- Mobile back button (only in chat view) -->
    <div class="mobile-chat-header" v-if="activeChatId && aiStore.currentChat">
      <button class="back-btn" @click="goBack">
        <i class="pi pi-arrow-left"></i>
      </button>
      <div class="mobile-chat-title">
        <span>{{ aiStore.currentChat.title }}</span>
      </div>
      <button class="icon-btn" @click="chatMenu.toggle($event)">
        <i class="pi pi-ellipsis-v"></i>
      </button>
      <Menu ref="chatMenu" :model="chatMenuItems" popup />
    </div>

    <div class="ai-layout">
      <!-- Sidebar: chat list -->
      <aside class="chat-sidebar">
        <div class="sidebar-top">
          <span class="sidebar-title">{{ $t('ai.history') }}</span>
          <button class="btn-primary-gradient new-chat-btn" type="button" @click="handleNewChat" :disabled="aiStore.loading">
            <i class="pi pi-plus"></i>
            <span class="new-chat-label">{{ $t('ai.new_chat') }}</span>
          </button>
        </div>

        <div v-if="aiStore.loading && !aiStore.chats.length" class="sidebar-loading">
          <span class="spinner"></span>
          <span>{{ $t('ai.loading') }}</span>
        </div>

        <div v-if="aiStore.error" class="sidebar-error">{{ aiStore.error }}</div>

        <div
          v-for="chat in aiStore.sortedChats"
          :key="chat.id"
          class="chat-item"
          :class="{ active: chat.id === activeChatId }"
          @click="openChat(chat.id)"
        >
          <div class="chat-item-body">
            <span class="chat-item-title">{{ chat.title }}</span>
            <span class="chat-item-meta">{{ chat.source_label || sourceLabel(chat.source) }}</span>
          </div>
          <button
            class="chat-item-menu-btn"
            @click.stop="openItemMenu($event, chat)"
          >
            <i class="pi pi-ellipsis-v"></i>
          </button>
        </div>

        <div v-if="!aiStore.loading && !aiStore.chats.length" class="empty-sidebar">
          <i class="pi pi-comments"></i>
          <p>{{ $t('ai.no_chats') }}</p>
        </div>
      </aside>

      <!-- Chat Panel -->
      <section class="chat-panel">
        <!-- Analyzing overlay: shown while a context analysis is in progress -->
        <div v-if="aiStore.analyzing" class="chat-empty analyzing-state">
          <div class="analyzing-spinner">
            <span class="spinner spinner-lg"></span>
          </div>
          <h2>{{ $t('ai.analyzing') }}</h2>
          <p>{{ $t('ai.analyzing_wait') }}</p>
        </div>

        <div v-else-if="!aiStore.currentChat" class="chat-empty">
          <i class="pi pi-comments empty-icon-lg"></i>
          <h2>{{ $t('ai.select_chat') }}</h2>
          <p>{{ $t('ai.select_chat_desc') }}</p>
          <button class="btn-primary-gradient" type="button" @click="handleNewChat">
            <i class="pi pi-plus"></i> {{ $t('ai.new_chat') }}
          </button>
        </div>

        <template v-else>
          <div class="panel-header desktop-header">
            <div class="panel-header-info">
              <h2>{{ aiStore.currentChat.title }}</h2>
              <span>{{ aiStore.currentChat.source_label || sourceLabel(aiStore.currentChat.source) }}</span>
            </div>
            <button class="icon-btn" @click="desktopChatMenu.toggle($event)">
              <i class="pi pi-ellipsis-v"></i>
            </button>
            <Menu ref="desktopChatMenu" :model="chatMenuItems" popup />
          </div>

          <div ref="messagesBox" class="messages-list">
            <div
              v-for="msg in aiStore.messages"
              :key="msg.id"
              class="msg-row"
              :class="msg.role"
            >
              <div class="msg-bubble" :class="{ error: msg.is_error }">
                <div class="msg-author">{{ msg.role === 'user' ? $t('ai.user_label') : $t('ai.ai_label') }}</div>
                <div class="msg-text">{{ msg.content }}</div>
              </div>
            </div>

            <div v-if="aiStore.sending" class="msg-row assistant">
              <div class="msg-bubble typing">
                <span class="spinner"></span>
                <span>{{ $t('ai.thinking') }}</span>
              </div>
            </div>
          </div>

          <form class="chat-input-area" @submit.prevent="handleSend">
            <textarea
              v-model="draft"
              class="form-control-dark chat-textarea"
              rows="2"
              :placeholder="$t('ai.input_placeholder')"
              :disabled="aiStore.sending"
              @keydown.enter.exact.prevent="handleSend"
            ></textarea>
            <button
              class="btn-primary-gradient send-btn"
              type="submit"
              :disabled="!draft.trim() || aiStore.sending"
            >
              <i class="pi pi-send"></i>
            </button>
          </form>
        </template>
      </section>
    </div>

    <!-- Context menu for chat items -->
    <Menu ref="itemMenu" :model="itemMenuItems" popup />

    <!-- Rename Dialog -->
    <Dialog
      v-model:visible="renameDialog"
      modal
      :header="$t('ai.rename_dialog')"
      :style="{ width: '360px' }"
      :draggable="false"
    >
      <input
        v-model="renameTitle"
        class="form-control-dark rename-input"
        :placeholder="$t('ai.chat_title_placeholder')"
        @keydown.enter="saveRename"
        ref="renameInput"
      />
      <template #footer>
        <button class="btn-glass btn-sm-f" @click="renameDialog = false">{{ $t('common.cancel') }}</button>
        <button class="btn-primary-gradient btn-sm-f" @click="saveRename" :disabled="!renameTitle.trim()">
          {{ $t('common.save') }}
        </button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Dialog from 'primevue/dialog'
import Menu from 'primevue/menu'
import { useAIChatsStore } from '../stores/aiChats'

const { t } = useI18n()

const route = useRoute()
const router = useRouter()
const aiStore = useAIChatsStore()

const draft = ref('')
const messagesBox = ref(null)
const chatMenu = ref(null)
const desktopChatMenu = ref(null)
const itemMenu = ref(null)
const renameInput = ref(null)

const renameDialog = ref(false)
const renameTitle = ref('')
const renameChatId = ref(null)
const itemMenuTarget = ref(null)

const activeChatId = computed(() => route.params.chatId || aiStore.currentChat?.id)

const chatMenuItems = computed(() => [
  {
    label: t('ai.rename'),
    icon: 'pi pi-pencil',
    command: () => openRename(aiStore.currentChat),
  },
  {
    label: t('ai.delete_chat'),
    icon: 'pi pi-trash',
    command: () => handleDeleteChat(aiStore.currentChat?.id),
  },
])

const itemMenuItems = computed(() => [
  {
    label: t('ai.rename'),
    icon: 'pi pi-pencil',
    command: () => openRename(itemMenuTarget.value),
  },
  {
    label: t('common.delete'),
    icon: 'pi pi-trash',
    command: () => handleDeleteChat(itemMenuTarget.value?.id),
  },
])

onMounted(async () => {
  await aiStore.fetchChats()
  if (route.params.chatId) {
    await aiStore.fetchChat(route.params.chatId)
  }
})

watch(
  () => route.params.chatId,
  async (chatId) => {
    if (!chatId) {
      aiStore.currentChat = null
      aiStore.messages = []
      return
    }
    await aiStore.fetchChat(chatId)
  }
)

watch(() => aiStore.messages.length, () => nextTick(scrollToBottom))
// Scroll as soon as the typing indicator appears
watch(() => aiStore.sending, (val) => { if (val) nextTick(scrollToBottom) })
// Navigate to the chat once a context analysis completes
watch(() => aiStore.pendingChatId, (chatId) => {
  if (chatId) {
    router.push({ name: 'ai-chat-detail', params: { chatId } })
    aiStore.pendingChatId = null
  }
})

async function handleNewChat() {
  const chat = await aiStore.createChat()
  await router.push({ name: 'ai-chat-detail', params: { chatId: chat.id } })
}

async function openChat(chatId) {
  if (chatId === route.params.chatId) return
  await router.push({ name: 'ai-chat-detail', params: { chatId } })
}

function goBack() {
  router.push({ name: 'ai-chat' })
}

async function handleSend() {
  const content = draft.value.trim()
  if (!content || aiStore.sending) return

  let chat = aiStore.currentChat
  try {
    if (!chat) {
      chat = await aiStore.createChat()
      await router.push({ name: 'ai-chat-detail', params: { chatId: chat.id } })
    }
    draft.value = ''
    await aiStore.sendMessage(chat.id, content)
    await nextTick(scrollToBottom)
  } catch {
    draft.value = content
  }
}

function openItemMenu(event, chat) {
  itemMenuTarget.value = chat
  itemMenu.value.toggle(event)
}

function openRename(chat) {
  if (!chat) return
  renameChatId.value = chat.id
  renameTitle.value = chat.title || ''
  renameDialog.value = true
  nextTick(() => renameInput.value?.focus())
}

async function saveRename() {
  if (!renameTitle.value.trim() || !renameChatId.value) return
  await aiStore.renameChat(renameChatId.value, renameTitle.value.trim())
  renameDialog.value = false
}

async function handleDeleteChat(chatId) {
  if (!chatId) return
  if (!confirm(t('ai.delete_confirm'))) return
  const wasActive = chatId === route.params.chatId
  await aiStore.deleteChat(chatId)
  if (wasActive) router.push({ name: 'ai-chat' })
}

function sourceLabel(source) {
  return { manual: t('ai.source_manual'), financial_report: t('ai.source_report'), goal: t('ai.source_goal') }[source] || 'AI-чат'
}

function scrollToBottom() {
  if (messagesBox.value) messagesBox.value.scrollTop = messagesBox.value.scrollHeight
}
</script>

<style scoped>
.ai-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  padding: 1rem 1.5rem;
  max-width: 1600px;
  width: 96%;
  margin: 0 auto;
  box-sizing: border-box;
}

/* Mobile top bar shown only when a chat is open */
.mobile-chat-header {
  display: none;
}

.ai-layout {
  display: grid;
  grid-template-columns: minmax(260px, 300px) minmax(0, 1fr);
  gap: 1rem;
  flex: 1;
  min-height: 0;
}

/* ── Sidebar ── */
.chat-sidebar {
  background: var(--bg-glass);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1rem;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.sidebar-title {
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--text-secondary);
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.85rem;
  font-size: 0.8rem;
}

.new-chat-label {
  display: inline;
}

.sidebar-loading,
.sidebar-error,
.empty-sidebar {
  padding: 1rem;
  color: var(--text-muted);
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sidebar-error {
  color: var(--danger-light);
}

.empty-sidebar {
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 0.5rem;
}

.empty-sidebar i {
  font-size: 2rem;
  opacity: 0.3;
}

.chat-sidebar > .chat-item {
  flex-shrink: 0;
}

/* Scrollable area */
.chat-sidebar {
  overflow-y: auto;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.65rem 0.85rem;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
  transition: background var(--transition-fast);
}

.chat-item:hover {
  background: rgba(99, 102, 241, 0.07);
}

.chat-item.active {
  background: rgba(99, 102, 241, 0.12);
  border-left: 3px solid var(--primary);
}

.chat-item-body {
  flex: 1;
  min-width: 0;
}

.chat-item-title {
  display: block;
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-item-meta {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.15rem;
}

.chat-item-menu-btn,
.icon-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0.3rem 0.4rem;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.chat-item-menu-btn:hover,
.icon-btn:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.back-btn {
  background: none;
  border: none;
  color: var(--text-primary);
  cursor: pointer;
  padding: 0.5rem;
  font-size: 1rem;
}

/* ── Chat Panel ── */
.chat-panel {
  background: var(--bg-glass);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.chat-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem;
  text-align: center;
}

.analyzing-state {
  gap: 1rem;
}

.analyzing-spinner {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(99, 102, 241, 0.12);
  border-radius: 50%;
  border: 1px solid rgba(99, 102, 241, 0.25);
}

.spinner-lg {
  width: 24px;
  height: 24px;
  border-width: 3px;
}

.empty-icon-lg {
  font-size: 3rem;
  color: var(--text-muted);
  opacity: 0.4;
}

.chat-empty h2 {
  font-size: 1.2rem;
  color: var(--text-primary);
  margin: 0;
}

.chat-empty p {
  color: var(--text-muted);
  margin: 0;
  max-width: 380px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.85rem 1.25rem;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.panel-header-info h2 {
  font-size: 1rem;
  color: var(--text-primary);
  margin: 0 0 0.15rem;
}

.panel-header-info span {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.messages-list {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.msg-row {
  display: flex;
}

.msg-row.user {
  justify-content: flex-end;
}

.msg-bubble {
  max-width: min(720px, 82%);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 0.75rem 1rem;
  background: rgba(15, 23, 42, 0.5);
}

.msg-row.user .msg-bubble {
  background: rgba(99, 102, 241, 0.18);
  border-color: rgba(99, 102, 241, 0.3);
}

.msg-bubble.error {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.25);
  color: var(--danger-light);
}

.msg-bubble.typing {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  color: var(--text-secondary);
}

.msg-author {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-muted);
  margin-bottom: 0.3rem;
}

.msg-text {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  line-height: 1.55;
  color: var(--text-primary);
}

.chat-input-area {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
}

.chat-textarea {
  resize: none;
  min-height: 52px;
  max-height: 160px;
}

.send-btn {
  align-self: stretch;
  min-width: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
}

/* Rename dialog inputs */
.rename-input {
  width: 100%;
  margin-bottom: 0.5rem;
}

.btn-sm-f {
  padding: 0.45rem 1rem;
  font-size: 0.85rem;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .ai-page {
    padding: 0;
    height: calc(100vh - 52px - 60px);
  }

  .ai-layout {
    grid-template-columns: 1fr;
    height: 100%;
    gap: 0;
  }

  /* On mobile: sidebar visible when no chat, hidden when chat is open */
  .chat-sidebar {
    border-radius: 0;
    border-left: none;
    border-right: none;
    border-top: none;
  }

  .chat-panel {
    border-radius: 0;
    border: none;
  }

  /* Default mobile: show sidebar, hide panel */
  .chat-panel {
    display: none;
  }

  /* When chat is open: show panel, hide sidebar */
  .has-chat .chat-sidebar {
    display: none;
  }

  .has-chat .chat-panel {
    display: flex;
    height: 100%;
  }

  /* Mobile header bar */
  .mobile-chat-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.6rem 1rem;
    background: rgba(15, 23, 42, 0.9);
    border-bottom: 1px solid var(--border-color);
    flex-shrink: 0;
  }

  .mobile-chat-title {
    flex: 1;
    font-weight: 600;
    font-size: 0.95rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--text-primary);
  }

  .desktop-header {
    display: none;
  }

  .msg-bubble {
    max-width: 94%;
  }

  .chat-input-area {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 0.5rem;
    padding: 0.75rem;
  }

  .new-chat-label {
    display: none;
  }

  .new-chat-btn {
    padding: 0.4rem 0.6rem;
  }
}
</style>
