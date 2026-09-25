<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { clearSession } from '../api.js'

const router = useRouter()

// Get the user's role from the frontend prototype session.
// This will eventually come from the Handoff backend.
const role = ref(localStorage.getItem('userRole'))

// Determine whether the current user is an Owner.
const isOwner = computed(() => {
  return role.value === 'owner'
})

// Determine which dashboard the user should return to.
const dashboardPath = computed(() => {
  return isOwner.value
    ? '/owner-dashboard'
    : '/employee-dashboard'
})

// Log the user out of the frontend prototype.
const logout = () => {
  clearSession()

  // Return to the login screen.
  router.push('/login')
}
</script>

<template>
  <nav class="navigation">

    <!-- Handoff brand and dashboard link -->
    <RouterLink
      :to="dashboardPath"
      class="brand"
    >
      <span class="brand-mark">H</span>
      <span>Handoff</span>
    </RouterLink>

    <div class="nav-links">

      <!-- Available to both Owners and Employees -->
      <RouterLink to="/procedures">
        Procedures
      </RouterLink>

      <!-- Owner-only navigation -->
      <RouterLink
        v-if="isOwner"
        to="/procedures"
      >
        Review Procedures
      </RouterLink>

      <!-- Owner-only navigation -->
      <RouterLink
        v-if="isOwner"
        to="/gaps"
      >
        Knowledge Gaps
      </RouterLink>

      <!-- Available to both Owners and Employees -->
      <RouterLink to="/query">
        Ask Handoff
      </RouterLink>

      <!-- Log out -->
      <button
        type="button"
        class="logout-button"
        @click="logout"
      >
        Log Out
      </button>

    </div>

  </nav>
</template>

<style scoped>

/* =========================================
   Navigation
   ========================================= */

.navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 30px;
  background: #ffffff;
  border-bottom: 1px solid #e4ddd7;
}


/* =========================================
   Handoff Brand
   ========================================= */

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #263238;
  text-decoration: none;
  font-size: 21px;
  font-weight: 700;
}


.brand-mark {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: #b65f32;
  color: #ffffff;
}


/* =========================================
   Navigation Links
   ========================================= */

.nav-links {
  display: flex;
  align-items: center;
  gap: 28px;
}


.nav-links a {
  color: #53646a;
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
}


.nav-links a:hover {
  color: #b65f32;
}


.nav-links a.router-link-active {
  color: #b65f32;
  font-weight: 700;
}


/* =========================================
   Logout Button
   ========================================= */

.logout-button {
  padding: 8px 15px;
  border: 1px solid #d8d2c8;
  border-radius: 7px;
  background: #ffffff;
  color: #53646a;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition:
    border-color 0.2s,
    color 0.2s,
    background 0.2s;
}


.logout-button:hover {
  border-color: #b65f32;
  background: #f5efe5;
  color: #b65f32;
}


/* =========================================
   Tablet
   ========================================= */

@media (max-width: 850px) {

  .navigation {
    padding: 15px 20px;
  }

  .nav-links {
    gap: 18px;
  }

}


/* =========================================
   Mobile
   ========================================= */

@media (max-width: 700px) {

  .navigation {
    flex-direction: column;
    gap: 15px;
    padding: 15px;
  }

  .nav-links {
    gap: 14px;
    flex-wrap: wrap;
    justify-content: center;
  }

}

</style>
