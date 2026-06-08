import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
    meta: { guest: true },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { auth: true },
  },
  {
    path: '/reports',
    name: 'reports',
    component: () => import('../views/ReportsView.vue'),
    meta: { auth: true },
  },
  {
    path: '/goals',
    name: 'goals',
    component: () => import('../views/GoalsView.vue'),
    meta: { auth: true },
  },
  {
    path: '/tracker',
    name: 'tracker',
    component: () => import('../views/TrackerView.vue'),
    meta: { auth: true },
  },
  {
    path: '/recurring-payments',
    name: 'recurring-payments',
    component: () => import('../views/RecurringPaymentsView.vue'),
    meta: { auth: true },
  },
  {
    path: '/ai',
    name: 'ai-chat',
    component: () => import('../views/AIChatView.vue'),
    meta: { auth: true },
  },
  {
    path: '/ai/:chatId',
    name: 'ai-chat-detail',
    component: () => import('../views/AIChatView.vue'),
    meta: { auth: true },
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('../views/AdminView.vue'),
    meta: { auth: true, adminOnly: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')

  if (to.meta.auth && !token) {
    next({ name: 'login' })
  } else if (to.meta.guest && token) {
    next({ name: 'dashboard' })
  } else if (to.meta.adminOnly && user?.role !== 'admin') {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router
