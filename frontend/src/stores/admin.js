import { defineStore } from 'pinia'
import api from '../services/api'

export const useAdminStore = defineStore('admin', {
  state: () => ({
    users: [],
    stats: null,
    aiStats: null,
    importErrors: [],
    loading: false,
    error: null,
  }),

  actions: {
    async fetchUsers() {
      this.loading = true
      this.error = null
      try {
        const res = await api.get('/admin/users')
        this.users = res.data.users
      } catch (err) {
        this.error = err.response?.data?.detail || 'Ошибка загрузки пользователей'
        throw err
      } finally {
        this.loading = false
      }
    },

    async blockUser(userId) {
      try {
        await api.post(`/admin/users/${userId}/block`)
        const user = this.users.find(u => u.id === userId)
        if (user) user.is_blocked = true
      } catch (err) {
        this.error = err.response?.data?.detail || 'Ошибка блокировки'
        throw err
      }
    },

    async deleteUser(userId) {
      try {
        await api.delete(`/admin/users/${userId}`)
        this.users = this.users.filter(u => u.id !== userId)
      } catch (err) {
        this.error = err.response?.data?.detail || 'Ошибка удаления'
        throw err
      }
    },

    async fetchStats() {
      this.loading = true
      this.error = null
      try {
        const res = await api.get('/admin/stats')
        this.stats = res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Ошибка загрузки статистики'
        throw err
      } finally {
        this.loading = false
      }
    },

    async fetchAiStats() {
      this.loading = true
      this.error = null
      try {
        const res = await api.get('/admin/ai-stats')
        this.aiStats = res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Ошибка загрузки AI статистики'
        throw err
      } finally {
        this.loading = false
      }
    },

    async fetchImportErrors() {
      this.loading = true
      this.error = null
      try {
        const res = await api.get('/admin/import-errors')
        this.importErrors = res.data.errors
      } catch (err) {
        this.error = err.response?.data?.detail || 'Ошибка загрузки ошибок импорта'
        throw err
      } finally {
        this.loading = false
      }
    },
  },
})
