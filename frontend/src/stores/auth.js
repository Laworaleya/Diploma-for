import { defineStore } from 'pinia'
import api from '../services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    token: localStorage.getItem('token') || null,
    loading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
    userLanguage: (state) => state.user?.preferred_language || 'ru',
    userCurrency: (state) => state.user?.currency || 'KZT',
  },

  actions: {
    async register(data) {
      this.loading = true
      this.error = null
      try {
        const res = await api.post('/auth/register', data)
        this._setAuth(res.data)
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Registration failed'
        throw err
      } finally {
        this.loading = false
      }
    },

    async login(email, password) {
      this.loading = true
      this.error = null
      try {
        const res = await api.post('/auth/login', { email, password })
        this._setAuth(res.data)
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Login failed'
        throw err
      } finally {
        this.loading = false
      }
    },

    async updateProfile(data) {
      this.loading = true
      try {
        const res = await api.put('/auth/me', data)
        this.user = res.data
        localStorage.setItem('user', JSON.stringify(res.data))
        return res.data
      } catch (err) {
        this.error = err.response?.data?.detail || 'Update failed'
        throw err
      } finally {
        this.loading = false
      }
    },

    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },

    _setAuth(data) {
      this.token = data.access_token
      this.user = data.user
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
    },
  },
})
