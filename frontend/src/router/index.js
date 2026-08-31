import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),

  // Routes for the main Handoff frontend screens
  routes: [
    // Main landing page
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue')
    },

    // Owner procedure management
    {
      path: '/procedures',
      name: 'procedures',
      component: () => import('../views/ProceduresView.vue')
    },

    // Review and approval of a structured procedure
    {
      path: '/procedure-review',
      name: 'procedure-review',
      component: () => import('../views/ProcedureReviewView.vue')
    },

    // Owner view of documentation gaps
    {
      path: '/gaps',
      name: 'gaps',
      component: () => import('../views/GapsView.vue')
    },

    // Employee question and answer interface
    {
      path: '/query',
      name: 'query',
      component: () => import('../views/QueryView.vue')
    }
  ]
})

export default router
