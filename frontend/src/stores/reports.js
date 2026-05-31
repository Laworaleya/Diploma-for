import { defineStore } from 'pinia'
import api from '../services/api'

export const useReportsStore = defineStore('reports', {
  state: () => ({
    reports: [],
    currentReport: null,
    loading: false,
    error: null,
  }),

  actions: {
    async fetchReports() {
      this.loading = true
      try {
        const res = await api.get('/reports')
        this.reports = res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to fetch reports'
      } finally {
        this.loading = false
      }
    },

    async fetchReport(id) {
      this.loading = true
      try {
        const res = await api.get(`/reports/${id}`)
        this.currentReport = res.data
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to fetch report'
        throw err
      } finally {
        this.loading = false
      }
    },

    async createReport(data) {
      this.loading = true
      try {
        const res = await api.post('/reports', data)
        this.reports.unshift(res.data)
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to create report'
        throw err
      } finally {
        this.loading = false
      }
    },

    async updateReport(id, data) {
      this.loading = true
      try {
        const res = await api.put(`/reports/${id}`, data)
        const idx = this.reports.findIndex(r => r.id === id)
        if (idx !== -1) this.reports[idx] = res.data
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to update report'
        throw err
      } finally {
        this.loading = false
      }
    },

    async deleteReport(id) {
      this.loading = true
      try {
        await api.delete(`/reports/${id}`)
        this.reports = this.reports.filter(r => r.id !== id)
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to delete report'
        throw err
      } finally {
        this.loading = false
      }
    },

    async importKaspiPdf(file) {
      this.loading = true
      this.error = null
      try {
        const formData = new FormData()
        formData.append('file', file)
        const res = await api.post('/reports/import-kaspi-pdf', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to import Kaspi PDF'
        throw err
      } finally {
        this.loading = false
      }
    },
  },
})
