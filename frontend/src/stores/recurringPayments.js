import { defineStore } from 'pinia'
import api from '../services/api'

export const useRecurringPaymentsStore = defineStore('recurringPayments', {
  state: () => ({
    payments: [],
    loading: false,
    error: null,
  }),

  getters: {
    sortedPayments: (state) => [...state.payments].sort((a, b) =>
      new Date(a.nextPaymentDate) - new Date(b.nextPaymentDate)
    ),
  },

  actions: {
    async fetchPayments() {
      this.loading = true
      this.error = null
      try {
        const res = await api.get('/recurring-payments')
        this.payments = res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to fetch recurring payments'
      } finally {
        this.loading = false
      }
    },

    async createPayment(data) {
      this.loading = true
      this.error = null
      try {
        const res = await api.post('/recurring-payments', data)
        const existingIndex = this.payments.findIndex(payment => payment.id === res.data.id)
        if (existingIndex === -1) {
          this.payments.push(res.data)
        } else {
          this.payments[existingIndex] = res.data
        }
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to create recurring payment'
        throw err
      } finally {
        this.loading = false
      }
    },

    async updatePayment(id, data) {
      this.loading = true
      this.error = null
      try {
        const res = await api.put(`/recurring-payments/${id}`, data)
        const idx = this.payments.findIndex(payment => payment.id === id)
        if (idx !== -1) this.payments[idx] = res.data
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to update recurring payment'
        throw err
      } finally {
        this.loading = false
      }
    },

    async deletePayment(id) {
      this.loading = true
      this.error = null
      try {
        await api.delete(`/recurring-payments/${id}`)
        this.payments = this.payments.filter(payment => payment.id !== id)
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to delete recurring payment'
        throw err
      } finally {
        this.loading = false
      }
    },
  },
})
