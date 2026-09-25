import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn } from '../api.js'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),

  routes: [
    // =========================================
    // Authentication
    // =========================================

    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue')
    },

    {
      path: '/signup',
      name: 'signup',
      component: () => import('../views/SignupView.vue')
    },

    // =========================================
    // Owner Dashboard
    // =========================================

    {
      path: '/owner-dashboard',
      name: 'owner-dashboard',
      component: () => import('../views/OwnerDashboardView.vue'),
      meta: {
        requiresAuth: true,
        ownerOnly: true
      }
    },

    // =========================================
    // Employee Dashboard
    // =========================================

    {
      path: '/employee-dashboard',
      name: 'employee-dashboard',
      component: () => import('../views/EmployeeDashboardView.vue'),
      meta: {
        requiresAuth: true
      }
    },

    // =========================================
    // Capture Procedure
    // Owner-only procedure creation workflow
    // =========================================

    {
      path: '/capture-procedure',
      name: 'capture-procedure',
      component: () => import('../views/CaptureProcedureView.vue'),
      meta: {
        requiresAuth: true,
        ownerOnly: true
      }
    },

    // =========================================
    // Procedures
    // =========================================

    {
      path: '/procedures',
      name: 'procedures',
      component: () => import('../views/ProceduresView.vue'),
      meta: {
        requiresAuth: true
      }
    },

    // =========================================
    // Procedure Review
    // Owner-only approval workflow
    // =========================================

    {
      path: '/procedure-review',
      name: 'procedure-review',
      component: () => import('../views/ProcedureReviewView.vue'),
      meta: {
        requiresAuth: true,
        ownerOnly: true
      }
    },

    // =========================================
    // Documentation Gaps
    // Owner-only gap management
    // =========================================

    {
      path: '/gaps',
      name: 'gaps',
      component: () => import('../views/GapsView.vue'),
      meta: {
        requiresAuth: true,
        ownerOnly: true
      }
    },

    // =========================================
    // Ask Handoff
    // Available to authenticated users
    // =========================================

    {
      path: '/query',
      name: 'query',
      component: () => import('../views/QueryView.vue'),
      meta: {
        requiresAuth: true
      }
    },

    // =========================================
    // Default Route
    // =========================================

    {
      path: '/',
      redirect: '/login'
    }
  ]
})


// =========================================
// Authentication / Role Guard
// =========================================

router.beforeEach((to) => {
  // Retrieve the prototype session information.
  const loggedIn = isLoggedIn()
  const role = localStorage.getItem('userRole')

  // Prevent unauthenticated users from accessing
  // pages that require a logged-in user.
  if (to.meta.requiresAuth && !loggedIn) {
    return '/login'
  }

  // Prevent Employees from accessing Owner-only pages.
  if (to.meta.ownerOnly && role !== 'owner') {
    return '/employee-dashboard'
  }

  // Prevent an Employee from manually navigating
  // to the Owner Dashboard.
  if (
    to.name === 'owner-dashboard' &&
    role !== 'owner'
  ) {
    return '/employee-dashboard'
  }

  // Prevent an Owner from navigating to the
  // Employee Dashboard.
  if (
    to.name === 'employee-dashboard' &&
    role === 'owner'
  ) {
    return '/owner-dashboard'
  }

  // If an authenticated user tries to visit the
  // Login or Signup page, send them to the
  // appropriate dashboard.
  if (
    (to.name === 'login' || to.name === 'signup') &&
    loggedIn
  ) {
    if (role === 'owner') {
      return '/owner-dashboard'
    }

    return '/employee-dashboard'
  }

  return true
})

export default router
