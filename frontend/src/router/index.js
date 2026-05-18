import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Suites',
    component: () => import('../views/Suites.vue'),
  },
  {
    path: '/suites/:id',
    name: 'SuiteDetail',
    component: () => import('../views/SuiteDetail.vue'),
    props: true,
  },
  {
    path: '/functions',
    name: 'Functions',
    component: () => import('../views/Functions.vue'),
  },
  {
    path: '/functions/:id',
    name: 'FunctionDetail',
    component: () => import('../views/FunctionDetail.vue'),
    props: true,
  },
  {
    path: '/executions/:id',
    name: 'ExecutionDetail',
    component: () => import('../views/ExecutionDetail.vue'),
    props: true,
  },
  {
    path: '/documents',
    name: 'Documents',
    component: () => import('../views/Documents.vue'),
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
