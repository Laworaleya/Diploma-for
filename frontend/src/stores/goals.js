import { defineStore } from 'pinia'
import api from '../services/api'

export const useGoalsStore = defineStore('goals', {
  state: () => ({
    goals: [],
    loading: false,
    error: null,
  }),

  getters: {
    activeGoals: (state) => state.goals.filter(g => g.status === 'active'),
    completedGoals: (state) => state.goals.filter(g => g.status === 'completed'),
  },

  actions: {
    async fetchGoals() {
      this.loading = true
      try {
        const res = await api.get('/goals')
        this.goals = res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to fetch goals'
      } finally {
        this.loading = false
      }
    },

    async createGoal(data) {
      this.loading = true
      try {
        const res = await api.post('/goals', data)
        this.goals.unshift(res.data)
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to create goal'
        throw err
      } finally {
        this.loading = false
      }
    },

    async updateGoal(id, data) {
      this.loading = true
      try {
        const res = await api.put(`/goals/${id}`, data)
        const idx = this.goals.findIndex(g => g.id === id)
        if (idx !== -1) this.goals[idx] = res.data
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to update goal'
        throw err
      } finally {
        this.loading = false
      }
    },

    async deleteGoal(id) {
      this.loading = true
      try {
        await api.delete(`/goals/${id}`)
        this.goals = this.goals.filter(g => g.id !== id)
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to delete goal'
        throw err
      } finally {
        this.loading = false
      }
    },
  },
})
