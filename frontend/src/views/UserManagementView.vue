<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch, getCurrentUser, errorMessage } from '../api.js'

const router = useRouter()

const users = ref([])
const loading = ref(true)
const message = ref('')
const error = ref('')
const savingRoleId = ref(null)
const deletingUserId = ref(null)

const currentUser = getCurrentUser()

// Return to the Owner Dashboard.
const goToDashboard = () => {
  router.push('/owner-dashboard')
}

// Load the users who currently have access to the business.
const loadUsers = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await apiFetch('/api/business/users')

    if (!response.ok) {
      throw new Error(await errorMessage(response))
    }

    users.value = await response.json()
  } catch (err) {
    error.value = err.message || 'Unable to load users.'
  } finally {
    loading.value = false
  }
}

// Update a user's Owner or Employee role.
const updateRole = async (user) => {
  savingRoleId.value = user.id
  message.value = ''
  error.value = ''

  try {
    const response = await apiFetch(
  `/api/business/users/${user.id}/role`,
  {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      role: user.role
    })
  }
)

    if (!response.ok) {
      throw new Error(await errorMessage(response))
    }

    const updatedUser = await response.json()

    user.role = updatedUser.role
    message.value = `${user.name}'s role was updated.`
  } catch (err) {
    error.value = err.message || 'Unable to update the user role.'

    // Reload the list so the displayed role matches the database.
    await loadUsers()
  } finally {
    savingRoleId.value = null
  }
}

// Delete an employee account.
const deleteEmployee = async (user) => {
  if (user.role !== 'employee') {
    return
  }

  const confirmed = window.confirm(
    `Delete ${user.name}'s employee account? This cannot be undone.`
  )

  if (!confirmed) {
    return
  }

  deletingUserId.value = user.id
  message.value = ''
  error.value = ''

  try {
    const response = await apiFetch(
      `/api/business/users/${user.id}`,
      {
        method: 'DELETE'
      }
    )

    if (!response.ok) {
      throw new Error(await errorMessage(response))
    }

    users.value = users.value.filter(
      (existingUser) => existingUser.id !== user.id
    )

    message.value = `${user.name}'s account was deleted.`
  } catch (err) {
    error.value = err.message || 'Unable to delete the employee account.'
  } finally {
    deletingUserId.value = null
  }
}

onMounted(loadUsers)
</script>

<template>
  <main class="dashboard-shell">
    <section class="dashboard-header">
      <div>
        <p class="eyebrow">USER MANAGEMENT</p>
        <h1>Manage Users</h1>
        <p class="intro">
          Manage your team's accounts and assign Owner or Employee privileges.
        </p>
      </div>

      <button
        class="secondary-button"
        type="button"
        @click="goToDashboard"
      >
        Back to Dashboard
      </button>
    </section>

    <section class="content-card">
      <div class="section-heading">
        <div>
          <h2>Users</h2>
          <p>
            Owners can change user roles or remove employee accounts.
          </p>
        </div>
      </div>

      <p
        v-if="message"
        class="success-message"
      >
        {{ message }}
      </p>

      <p
        v-if="error"
        class="error-message"
      >
        {{ error }}
      </p>

      <div v-if="loading" class="empty-state">
        Loading users...
      </div>

      <div
        v-else-if="users.length === 0"
        class="empty-state"
      >
        No users were found.
      </div>

      <div v-else class="user-list">
        <div class="user-row user-header">
          <span>Name</span>
          <span>Email</span>
          <span>Role</span>
          <span>Actions</span>
        </div>

        <div
          v-for="user in users"
          :key="user.id"
          class="user-row"
        >
          <div>
            <strong>{{ user.name }}</strong>

            <span
              v-if="user.id === currentUser?.id"
              class="current-user"
            >
              You
            </span>
          </div>

          <span>{{ user.email }}</span>

          <select
            v-model="user.role"
            :disabled="
              user.id === currentUser?.id ||
              savingRoleId === user.id
            "
            aria-label="User role"
            @change="updateRole(user)"
          >
            <option value="employee">Employee</option>
            <option value="owner">Owner</option>
          </select>

          <button
            v-if="user.role === 'employee'"
            class="danger-button"
            type="button"
            :disabled="deletingUserId === user.id"
            @click="deleteEmployee(user)"
          >
            {{ deletingUserId === user.id ? 'Deleting...' : 'Delete' }}
          </button>

          <span
            v-else
            class="owner-label"
          >
            Owner
          </span>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
/* =========================================
   Overall User Management Page
   ========================================= */

.dashboard-shell {
  min-height: calc(100vh - 70px);
  padding: 55px 60px;
  box-sizing: border-box;
  background: #f5efe5;
}

/* =========================================
   Page Header
   ========================================= */

.dashboard-header {
  max-width: 1150px;
  margin: 0 auto 40px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 30px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #d26f3d;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 1.5px;
}

.dashboard-header h1 {
  margin: 0 0 12px;
  color: #275b4f;
  font-size: 38px;
  font-weight: 700;
  line-height: 1.2;
}

.intro {
  max-width: 650px;
  margin: 0;
  color: #666666;
  font-size: 16px;
  line-height: 1.6;
}

/* =========================================
   Buttons
   ========================================= */

.secondary-button {
  flex-shrink: 0;
  padding: 11px 18px;
  border: 1px solid #d26f3d;
  border-radius: 8px;
  background: #ffffff;
  color: #d26f3d;
  font-family: inherit;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.secondary-button:hover {
  background: #d26f3d;
  color: #ffffff;
}

/* =========================================
   Main User Card
   ========================================= */

.content-card {
  max-width: 1150px;
  margin: 0 auto;
  padding: 30px;
  box-sizing: border-box;
  border: 1px solid #ded8ce;
  border-radius: 14px;
  background: #ffffff;
}

.section-heading {
  margin-bottom: 22px;
}

.section-heading h2 {
  margin: 0 0 7px;
  color: #333333;
  font-size: 24px;
}

.section-heading p {
  margin: 0;
  color: #777777;
  font-size: 14px;
}

/* =========================================
   Messages
   ========================================= */

.success-message {
  margin: 0 0 18px;
  color: #275b4f;
  font-size: 14px;
  font-weight: 600;
}

.error-message {
  margin: 0 0 18px;
  color: #a44a3a;
  font-size: 14px;
  font-weight: 600;
}

/* =========================================
   User List
   ========================================= */

.user-list {
  overflow: hidden;
  border: 1px solid #ded8ce;
  border-radius: 10px;
}

.user-row {
  display: grid;
  grid-template-columns: 1.2fr 1.5fr 150px 110px;
  align-items: center;
  gap: 20px;
  min-height: 70px;
  padding: 0 20px;
  box-sizing: border-box;
  border-bottom: 1px solid #eee9e1;
}

.user-row:last-child {
  border-bottom: none;
}

.user-header {
  min-height: 48px;
  background: #f7f4eb;
  color: #666666;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.user-row strong {
  display: inline-block;
  color: #275b4f;
  font-size: 15px;
}

.user-row > span {
  color: #666666;
  font-size: 14px;
}

.current-user {
  margin-left: 8px;
  padding: 3px 7px;
  border-radius: 12px;
  background: #e7f0ec;
  color: #275b4f !important;
  font-size: 11px !important;
  font-weight: 700;
}

.user-row select {
  width: 100%;
  padding: 9px 10px;
  border: 1px solid #d8d2c8;
  border-radius: 7px;
  background: #ffffff;
  color: #333333;
  font-family: inherit;
  font-size: 14px;
}

.user-row select:focus {
  outline: none;
  border-color: #275b4f;
}

.user-row select:disabled {
  background: #f5f2ed;
  color: #777777;
  cursor: not-allowed;
}

/* =========================================
   User Actions
   ========================================= */

.danger-button {
  padding: 9px 14px;
  border: 1px solid #a44a3a;
  border-radius: 7px;
  background: #ffffff;
  color: #a44a3a;
  font-family: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.danger-button:hover {
  background: #a44a3a;
  color: #ffffff;
}

.danger-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.owner-label {
  color: #275b4f !important;
  font-size: 13px !important;
  font-weight: 700;
}

/* =========================================
   Loading / Empty State
   ========================================= */

.empty-state {
  padding: 35px 20px;
  border: 1px dashed #d8d2c8;
  border-radius: 10px;
  background: #faf8f4;
  color: #777777;
  font-size: 14px;
  text-align: center;
}

/* =========================================
   Tablet
   ========================================= */

@media (max-width: 850px) {
  .dashboard-shell {
    padding: 40px 30px;
  }

  .dashboard-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .user-row {
    grid-template-columns: 1fr 1fr;
    gap: 12px 20px;
    padding: 15px 20px;
  }

  .user-header {
    display: none;
  }
}

/* =========================================
   Mobile
   ========================================= */

@media (max-width: 500px) {
  .dashboard-shell {
    padding: 30px 18px;
  }

  .dashboard-header h1 {
    font-size: 30px;
  }

  .intro {
    font-size: 14px;
  }

  .content-card {
    padding: 20px;
  }

  .user-row {
    grid-template-columns: 1fr;
  }
}
</style>
