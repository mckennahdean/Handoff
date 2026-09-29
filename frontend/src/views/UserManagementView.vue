<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch, getCurrentUser, errorMessage } from '../api.js'

const router = useRouter()

const users = ref([])
const loading = ref(true)
const message = ref('')
const error = ref('')
const savingRoleId = ref(null)
const deletingUserId = ref(null)
const approvingUserId = ref(null)
const issuingUserId = ref(null)

// Recovery codes just issued by the owner, shown once.
const issuedCodes = ref(null)

const currentUser = getCurrentUser()

// New signups wait here until an owner approves or rejects them.
const pendingUsers = computed(() =>
  users.value.filter((user) => user.status === 'pending')
)

const activeUsers = computed(() =>
  users.value.filter((user) => user.status !== 'pending')
)

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
    const data = await response.json()

    if (!response.ok) {
      throw new Error(errorMessage(data, 'Unable to load users.'))
    }

    users.value = data
  } catch (err) {
    error.value = err.message || 'Unable to load users.'
  } finally {
    loading.value = false
  }
}

// Update a user's Owner or Employee role.
const updateRole = async (user) => {
  // Owner access is the most powerful permission, so confirm first.
  const granting = user.role === 'owner'

  const confirmed = window.confirm(
    granting
      ? `Give ${user.name} owner access? Owners can approve and delete ` +
        'procedures, see knowledge gaps, and manage every account.'
      : `Remove ${user.name}'s owner access? They will become an employee.`
  )

  if (!confirmed) {
    // The dropdown already changed, so put it back.
    user.role = granting ? 'employee' : 'owner'
    return
  }

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

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        errorMessage(data, 'Unable to update the user role.')
      )
    }

    user.role = data.role
    message.value = `${user.name}'s role was updated.`
  } catch (err) {
    // Reload first so the list matches the database. Reloading
    // clears old messages, so set the error afterward.
    await loadUsers()
    error.value = err.message || 'Unable to update the user role.'
  } finally {
    savingRoleId.value = null
  }
}

// Let a pending account sign in.
const approveUser = async (user) => {
  approvingUserId.value = user.id
  message.value = ''
  error.value = ''

  try {
    const response = await apiFetch(
      `/api/business/users/${user.id}/approve`,
      { method: 'POST' }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        errorMessage(data, 'Unable to approve the account.')
      )
    }

    user.status = data.status
    message.value = `${user.name} can now sign in.`
  } catch (err) {
    // Reload first so the list matches the database. Reloading
    // clears old messages, so set the error afterward.
    await loadUsers()
    error.value = err.message || 'Unable to approve the account.'
  } finally {
    approvingUserId.value = null
  }
}

// Delete an employee account, or reject a pending signup.
// Both remove the account, so they share one request.
const removeAccount = async (user, question, doneMessage) => {
  if (user.role !== 'employee') {
    return
  }

  const confirmed = window.confirm(question)

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

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        errorMessage(data, 'Unable to remove the account.')
      )
    }

    users.value = users.value.filter(
      (existingUser) => existingUser.id !== user.id
    )

    message.value = doneMessage
  } catch (err) {
    error.value = err.message || 'Unable to remove the account.'
  } finally {
    deletingUserId.value = null
  }
}

const deleteEmployee = (user) => removeAccount(
  user,
  `Delete ${user.name}'s employee account? This cannot be undone.`,
  `${user.name}'s account was deleted.`
)

const rejectUser = (user) => removeAccount(
  user,
  `Reject ${user.name}'s request? Their pending account will be deleted.`,
  `${user.name}'s request was rejected.`
)

// Give someone a fresh set of recovery codes, shown here once
// so the owner can hand them over. The old set stops working.
const issueCodes = async (user) => {
  const confirmed = window.confirm(
    `Create new recovery codes for ${user.name}? ` +
    'Their old codes will stop working.'
  )

  if (!confirmed) {
    return
  }

  issuingUserId.value = user.id
  issuedCodes.value = null
  message.value = ''
  error.value = ''

  try {
    const response = await apiFetch(
      `/api/business/users/${user.id}/recovery-codes`,
      { method: 'POST' }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        errorMessage(data, 'Unable to create recovery codes.')
      )
    }

    issuedCodes.value = { name: user.name, codes: data.codes }
  } catch (err) {
    error.value = err.message || 'Unable to create recovery codes.'
  } finally {
    issuingUserId.value = null
  }
}

const copyIssuedCodes = async () => {
  try {
    await navigator.clipboard.writeText(issuedCodes.value.codes.join('\n'))
    message.value = 'Codes copied.'
  } catch {
    error.value = 'Copy failed. Please copy the codes manually.'
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
          Approve new employees, and manage your team's accounts and roles.
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

    <!-- Success and error messages for every action on this page -->
    <div class="page-messages">
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
    </div>

    <!-- Recovery codes the owner just issued, shown once -->
    <section
      v-if="issuedCodes"
      class="content-card issued-codes"
    >
      <div class="section-heading">
        <h2>New Recovery Codes for {{ issuedCodes.name }}</h2>

        <p>
          Give these to them directly. They are shown only once, and
          each code works once on the login page.
        </p>
      </div>

      <ol class="code-grid">
        <li v-for="code in issuedCodes.codes" :key="code">
          {{ code }}
        </li>
      </ol>

      <div class="code-actions">
        <button
          type="button"
          class="codes-button"
          @click="copyIssuedCodes"
        >
          Copy Codes
        </button>

        <button
          type="button"
          class="approve-button"
          @click="issuedCodes = null"
        >
          Done
        </button>
      </div>
    </section>

    <!-- New signups waiting for an owner's decision -->
    <section class="content-card pending-requests">
      <div class="section-heading">
        <h2>Waiting for Approval</h2>

        <p>
          New employees sign up on their own. They cannot see or do
          anything until an owner approves them.
        </p>
      </div>

      <div v-if="loading" class="empty-state">
        Loading requests...
      </div>

      <div
        v-else-if="pendingUsers.length === 0"
        class="empty-state"
      >
        No one is waiting for approval.
      </div>

      <div v-else class="user-list">
        <div class="user-row user-header">
          <span>Name</span>
          <span>Email</span>
          <span>Actions</span>
          <span></span>
        </div>

        <div
          v-for="user in pendingUsers"
          :key="user.id"
          class="user-row"
        >
          <div>
            <strong>{{ user.name }}</strong>
          </div>

          <span>{{ user.email }}</span>

          <button
            class="approve-button"
            type="button"
            :disabled="approvingUserId === user.id"
            @click="approveUser(user)"
          >
            {{ approvingUserId === user.id ? 'Approving...' : 'Approve' }}
          </button>

          <button
            class="danger-button"
            type="button"
            :disabled="deletingUserId === user.id"
            @click="rejectUser(user)"
          >
            {{ deletingUserId === user.id ? 'Rejecting...' : 'Reject' }}
          </button>
        </div>
      </div>
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

      <div v-if="loading" class="empty-state">
        Loading users...
      </div>

      <div
        v-else-if="activeUsers.length === 0"
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
          v-for="user in activeUsers"
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

          <div class="row-actions">
            <button
              class="codes-button"
              type="button"
              :disabled="issuingUserId === user.id"
              @click="issueCodes(user)"
            >
              {{ issuingUserId === user.id ? 'Creating...' : 'New Codes' }}
            </button>

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
  grid-template-columns: 1.2fr 1.5fr 150px 210px;
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
   Messages and Pending Requests
   ========================================= */

.page-messages {
  max-width: 1150px;
  margin: 0 auto;
}

.pending-requests {
  margin-bottom: 24px;
}

.approve-button {
  padding: 9px 14px;
  border: none;
  border-radius: 7px;
  background: #275b4f;
  color: #ffffff;
  font-family: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.approve-button:hover {
  opacity: 0.9;
}

.approve-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* =========================================
   Recovery Codes
   ========================================= */

.issued-codes {
  margin-bottom: 24px;
  border-color: #275b4f;
}

.row-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.codes-button {
  padding: 9px 14px;
  border: 1px solid #275b4f;
  border-radius: 7px;
  background: #ffffff;
  color: #275b4f;
  font-family: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.codes-button:hover {
  background: #275b4f;
  color: #ffffff;
}

.codes-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.code-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 30px;
  margin: 0 0 20px;
  padding: 18px 18px 18px 42px;
  border: 1px dashed #d8d2c8;
  border-radius: 10px;
  background: #faf8f4;
  color: #275b4f;
  font-family: 'Courier New', monospace;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 2px;
}

.code-actions {
  display: flex;
  gap: 10px;
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