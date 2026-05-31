import { defineStore } from 'pinia'
import api from '../services/api'

export const useAIChatsStore = defineStore('aiChats', {
  state: () => ({
    chats: [],
    currentChat: null,
    messages: [],
    loading: false,
    sending: false,
    error: null,
  }),

  getters: {
    sortedChats: (state) => [...state.chats].sort(
      (a, b) => new Date(b.updated_at) - new Date(a.updated_at)
    ),
  },

  actions: {
    async fetchChats() {
      this.loading = true
      this.error = null
      try {
        const res = await api.get('/ai/chats')
        this.chats = res.data
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Не удалось загрузить AI-чаты'
        throw err
      } finally {
        this.loading = false
      }
    },

    async createChat(title = null) {
      this.loading = true
      this.error = null
      try {
        const res = await api.post('/ai/chats', { title })
        this._upsertChat(res.data)
        this.currentChat = res.data
        this.messages = []
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Не удалось создать AI-чат'
        throw err
      } finally {
        this.loading = false
      }
    },

    async fetchChat(chatId) {
      this.loading = true
      this.error = null
      try {
        const res = await api.get(`/ai/chats/${chatId}`)
        const { messages = [], ...chat } = res.data
        this.currentChat = chat
        this.messages = messages
        this._upsertChat(chat)
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Не удалось открыть AI-чат'
        throw err
      } finally {
        this.loading = false
      }
    },

    async sendMessage(chatId, content) {
      this.sending = true
      this.error = null
      try {
        const res = await api.post(`/ai/chats/${chatId}/messages`, { content })
        this._appendMessage(res.data.user_message)
        this._appendMessage(res.data.assistant_message)
        this._upsertChat(res.data.chat)
        this.currentChat = res.data.chat
        if (res.data.error) this.error = res.data.error
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'AI сейчас недоступен'
        throw err
      } finally {
        this.sending = false
      }
    },

    async analyzeReport(reportId) {
      this.loading = true
      this.error = null
      try {
        const res = await api.post(`/ai/reports/${reportId}/analyze`)
        this._applyContextResponse(res.data)
        return res.data.chat
      } catch (err) {
        this.error = err.response?.data?.detail || 'Не удалось отправить отчет в AI'
        throw err
      } finally {
        this.loading = false
      }
    },

    async planGoal(goalId) {
      this.loading = true
      this.error = null
      try {
        const res = await api.post(`/ai/goals/${goalId}/plan`)
        this._applyContextResponse(res.data)
        return res.data.chat
      } catch (err) {
        this.error = err.response?.data?.detail || 'Не удалось составить план с AI'
        throw err
      } finally {
        this.loading = false
      }
    },

    _applyContextResponse(data) {
      this.currentChat = data.chat
      this.messages = [data.user_message, data.assistant_message]
      this._upsertChat(data.chat)
      if (data.error) this.error = data.error
    },

    _appendMessage(message) {
      const existingIndex = this.messages.findIndex(item => item.id === message.id)
      if (existingIndex === -1) {
        this.messages.push(message)
      } else {
        this.messages[existingIndex] = message
      }
    },

    async renameChat(chatId, title) {
      this.loading = true
      this.error = null
      try {
        const res = await api.patch(`/ai/chats/${chatId}`, { title })
        this._upsertChat(res.data)
        if (this.currentChat?.id === chatId) this.currentChat = res.data
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Не удалось переименовать чат'
        throw err
      } finally {
        this.loading = false
      }
    },

    async deleteChat(chatId) {
      this.loading = true
      this.error = null
      try {
        await api.delete(`/ai/chats/${chatId}`)
        this.chats = this.chats.filter(c => c.id !== chatId)
        if (this.currentChat?.id === chatId) {
          this.currentChat = null
          this.messages = []
        }
      } catch (err) {
        this.error = err.response?.data?.detail || 'Не удалось удалить чат'
        throw err
      } finally {
        this.loading = false
      }
    },

    _upsertChat(chat) {
      const index = this.chats.findIndex(item => item.id === chat.id)
      if (index === -1) {
        this.chats.unshift(chat)
      } else {
        this.chats[index] = chat
      }
    },
  },
})
