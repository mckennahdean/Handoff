<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch, getCurrentUser, errorMessage } from '../api.js'

const router = useRouter()

// The signed-in owner, saved at login.
const user = getCurrentUser() || { name: 'Owner' }

// Dashboard statistics loaded from the Handoff backend.
const procedureCount = ref('...')
const documentationGaps = ref('...')

// Unapproved drafts currently live only in this browser.
// This becomes a real server-side count in the next step.
const pendingReviews = ref(
  localStorage.getItem('pendingProcedure') ? 1 : 0
)

// Invite code the owner shares with new employees.
const businessName = ref('')
const inviteCode = ref('')
const inviteMessage = ref('')

const loadStats = async () => {
  try {
    // Request both at the same time instead of one after the other.
    const [proceduresResponse, gapsResponse] = await Promise.all([
      apiFetch('/api/procedures'),
      apiFetch('/api/gaps')
    ])

    if (proceduresResponse.ok) {
      procedureCount.value = (await proceduresResponse.json()).length
    }

    if (gapsResponse.ok) {
      documentationGaps.value = (await gapsResponse.json()).length
    }
  } catch {
    // Keep the placeholders if the server cannot be reached.
  }
}

const loadInviteCode = async () => {
  try {
    const response = await apiFetch('/api/business/invite-code')
    const data = await response.json()

    if (!response.ok) {
      inviteMessage.value = errorMessage(data, 'Unable to load invite code.')
      return
    }

    businessName.value = data.business_name
    inviteCode.value = data.invite_code
  } catch {
    inviteMessage.value = 'Unable to reach the Handoff server.'
  }
}

const copyInviteCode = async () => {
  try {
    await navigator.clipboard.writeText(inviteCode.value)
    inviteMessage.value = 'Invite code copied.'
  } catch {
    inviteMessage.value = 'Copy failed. Please copy the code manually.'
  }
}

const regenerateInviteCode = async () => {
  const confirmed = window.confirm(
    'Create a new invite code? The current code will stop working ' +
    'immediately. Existing employee accounts are not affected.'
  )

  if (!confirmed) {
    return
  }

  try {
    const response = await apiFetch(
      '/api/business/invite-code/regenerate',
      { method: 'POST' }
    )

    const data = await response.json()

    if (!response.ok) {
      inviteMessage.value = errorMessage(data, 'Unable to create a new code.')
      return
    }

    inviteCode.value = data.invite_code
    inviteMessage.value =
      'New invite code created. The old code no longer works.'
  } catch {
    inviteMessage.value = 'Unable to reach the Handoff server.'
  }
}

onMounted(() => {
  loadStats()
  loadInviteCode()
})

// Navigate to a specific Handoff feature.
const goTo = (path) => {
  router.push(path)
}
</script>

<template>
  <main class="dashboard-page">

    <!-- Dashboard header -->
    <section class="dashboard-header">

      <div>
        <p class="eyebrow">OWNER DASHBOARD</p>

        <h1>
          Welcome back, {{ user.name }}
        </h1>

        <p class="intro">
          Manage your team's knowledge and keep important
          business procedures moving forward.
        </p>
      </div>

    </section>

    <!-- Overview cards -->
    <section class="stats-grid">

      <!-- Procedures -->
      <button
        class="stat-card"
        @click="goTo('/procedures')"
      >
        <span class="stat-label">Procedures</span>
        <strong>{{ procedureCount }}</strong>
        <span class="stat-description">
          Approved procedures in your knowledge base
        </span>
      </button>

      <!-- Reviews -->
      <button
        class="stat-card"
        @click="goTo('/procedure-review')"
      >
        <span class="stat-label">Pending Reviews</span>
        <strong>{{ pendingReviews }}</strong>
        <span class="stat-description">
          Procedures waiting for your approval
        </span>
      </button>

      <!-- Documentation gaps -->
      <button
        class="stat-card"
        @click="goTo('/gaps')"
      >
        <span class="stat-label">Knowledge Gaps</span>
        <strong>{{ documentationGaps }}</strong>
        <span class="stat-description">
          Questions that need documentation
        </span>
      </button>

    </section>

    <!-- Team access: invite code for new employees -->
    <section class="section">

      <div class="section-heading">
        <h2>Team Access</h2>

        <p>
          Share this code with new employees so they can create
          their {{ businessName || 'Handoff' }} account.
        </p>
      </div>

      <div class="invite-card">
        <span class="invite-code">
          {{ inviteCode || '........' }}
        </span>

        <div class="invite-actions">
          <button
            type="button"
            class="invite-button"
            @click="copyInviteCode"
          >
            Copy Code
          </button>

          <button
            type="button"
            class="invite-button secondary"
            @click="regenerateInviteCode"
          >
            New Code
          </button>
        </div>
      </div>

      <p v-if="inviteMessage" class="invite-message">
        {{ inviteMessage }}
      </p>

    </section>

    <!-- Main actions -->
    <section class="section">

      <div class="section-heading">
        <h2>Manage Knowledge</h2>

        <p>
          Capture, review, and maintain the knowledge your
          employees rely on.
        </p>
      </div>

      <div class="action-grid">

        <!-- Record / upload -->
        <button
          class="action-card"
          @click="goTo('/procedures')"
        >
          <div class="action-icon">
            +
          </div>

          <div>
            <h3>Capture a Procedure</h3>

            <p>
              Record or upload an experienced employee's
              knowledge for Handoff to structure.
            </p>
          </div>
        </button>

        <!-- Review -->
        <button
          class="action-card"
          @click="goTo('/procedure-review')"
        >
          <div class="action-icon">
            ✓
          </div>

          <div>
            <h3>Review Procedures</h3>

            <p>
              Review AI-generated procedures and approve
              them before they become available to employees.
            </p>
          </div>
        </button>

        <!-- Gaps -->
        <button
          class="action-card"
          @click="goTo('/gaps')"
        >
          <div class="action-icon">
            !
          </div>

          <div>
            <h3>Documentation Gaps</h3>

            <p>
              See questions Handoff could not answer and
              identify knowledge that still needs to be captured.
            </p>
          </div>
        </button>

        <!-- Query -->
        <button
          class="action-card"
          @click="goTo('/query')"
        >
          <div class="action-icon">
            ?
          </div>

          <div>
            <h3>Ask Handoff</h3>

            <p>
              Test the knowledge base by asking questions
              about documented business procedures.
            </p>
          </div>
        </button>

      </div>

    </section>

  </main>
</template>

<style scoped>

/* =========================================
   Overall Dashboard
   ========================================= */

.dashboard-page {
  min-height: calc(100vh - 70px);
  padding: 55px 60px;
  box-sizing: border-box;
  background: #f5efe5;
}


/* =========================================
   Header
   ========================================= */

.dashboard-header {
  max-width: 1150px;
  margin: 0 auto 40px;
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
   Statistics
   ========================================= */

.stats-grid {
  max-width: 1150px;
  margin: 0 auto 50px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}


.stat-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 25px;
  border: 1px solid #ded8ce;
  border-radius: 14px;
  background: #ffffff;
  text-align: left;
  cursor: pointer;
  transition:
    transform 0.15s,
    box-shadow 0.15s,
    border-color 0.15s;
}


.stat-card:hover {
  transform: translateY(-2px);
  border-color: #275b4f;
  box-shadow:
    0 8px 25px rgba(39, 91, 79, 0.1);
}


.stat-label {
  color: #666666;
  font-size: 14px;
  font-weight: 600;
}


.stat-card strong {
  margin: 8px 0;
  color: #275b4f;
  font-size: 34px;
}


.stat-description {
  color: #888888;
  font-size: 13px;
  line-height: 1.4;
}


/* =========================================
   Main Section
   ========================================= */

.section {
  max-width: 1150px;
  margin: 0 auto;
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
   Action Cards
   ========================================= */

.action-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 18px;
}


.action-card {
  display: flex;
  align-items: flex-start;
  gap: 18px;
  padding: 25px;
  border: 1px solid #ded8ce;
  border-radius: 14px;
  background: #ffffff;
  text-align: left;
  cursor: pointer;
  transition:
    transform 0.15s,
    box-shadow 0.15s,
    border-color 0.15s;
}


.action-card:hover {
  transform: translateY(-2px);
  border-color: #275b4f;
  box-shadow:
    0 8px 25px rgba(39, 91, 79, 0.1);
}


.action-icon {
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #275b4f;
  color: #ffffff;
  font-size: 21px;
  font-weight: 700;
}


.action-card h3 {
  margin: 2px 0 7px;
  color: #275b4f;
  font-size: 17px;
}


.action-card p {
  margin: 0;
  color: #777777;
  font-size: 14px;
  line-height: 1.55;
}

/* =========================================
   Team Access / Invite Code
   ========================================= */

.invite-card {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 22px 24px;
  border: 1px solid #d8d2c8;
  border-radius: 14px;
  background: #ffffff;
}


.invite-code {
  color: #275b4f;
  font-family: 'Courier New', monospace;
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 6px;
}


.invite-actions {
  display: flex;
  gap: 10px;
}


.invite-button {
  padding: 11px 18px;
  border: none;
  border-radius: 8px;
  background: #275b4f;
  color: #ffffff;
  font-family: inherit;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}


.invite-button.secondary {
  border: 1px solid #d26f3d;
  background: #ffffff;
  color: #d26f3d;
}


.invite-button:hover {
  opacity: 0.9;
}


.invite-message {
  margin: 12px 0 0;
  color: #275b4f;
  font-size: 13px;
}

/* =========================================
   Tablet
   ========================================= */

@media (max-width: 850px) {

  .dashboard-page {
    padding: 40px 30px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .action-grid {
    grid-template-columns: 1fr;
  }

}


/* =========================================
   Mobile
   ========================================= */

@media (max-width: 500px) {

  .dashboard-page {
    padding: 30px 18px;
  }

  .dashboard-header h1 {
    font-size: 30px;
  }

  .intro {
    font-size: 14px;
  }

  .stat-card,
  .action-card {
    padding: 20px;
  }

}

</style>
