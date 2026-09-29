<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { apiFetch } from '../api.js'

// Read-only view of one procedure, opened from the Procedures page.
// The backend returns 404 to employees for anything not approved,
// so an employee can only ever see approved knowledge here.

const route = useRoute()
const procedureId = Number(route.query.id)

const procedure = ref(null)
const isLoading = ref(true)
const errorMessage = ref('')

const formatDate = (dateValue) => {
  if (!dateValue) {
    return 'Not yet confirmed'
  }

  const date = new Date(dateValue)

  if (Number.isNaN(date.getTime())) {
    return dateValue
  }

  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const loadProcedure = async () => {
  isLoading.value = true
  errorMessage.value = ''

  if (!Number.isInteger(procedureId) || procedureId < 1) {
    errorMessage.value = 'This procedure link is not valid.'
    isLoading.value = false
    return
  }

  try {
    const response = await apiFetch(
      `/api/procedures/${procedureId}`
    )

    // A non-JSON error page should still show a readable message.
    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(
        data.detail || 'Unable to load this procedure.'
      )
    }

    procedure.value = data
  } catch (error) {
    console.error(error)

    errorMessage.value =
      error.message ||
      'Handoff could not connect to the procedure service.'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadProcedure()
})
</script>

<template>
  <main class="procedure-detail">

    <!-- =========================================
         Loading State
         ========================================= -->
    <section
      v-if="isLoading"
      class="status-message"
    >
      <strong>Loading procedure...</strong>

      <p>
        Handoff is retrieving this procedure.
      </p>
    </section>

    <!-- =========================================
         Error State
         ========================================= -->
    <section
      v-else-if="errorMessage"
      class="error-message"
    >
      <div class="error-icon">
        !
      </div>

      <div>
        <strong>Unable to open this procedure</strong>

        <p>
          {{ errorMessage }}
        </p>

        <RouterLink
          to="/procedures"
          class="back-button"
        >
          Back to Procedures
        </RouterLink>
      </div>
    </section>

    <!-- =========================================
         Procedure
         ========================================= -->
    <template v-else-if="procedure">
      <section class="page-header">
        <div>
          <p class="eyebrow">
            {{
              procedure.status === 'approved'
                ? 'Approved Procedure'
                : 'Draft, not visible to employees'
            }}
          </p>

          <h1>{{ procedure.title }}</h1>

          <p>
            Version {{ procedure.version }}.
            Last confirmed {{ formatDate(procedure.last_confirmed) }}.
          </p>
        </div>

        <RouterLink
          to="/procedures"
          class="back-button"
        >
          Back to Procedures
        </RouterLink>
      </section>

      <section class="content-card">
        <h2>Steps</h2>

        <ol class="step-list">
          <li
            v-for="(step, index) in procedure.steps"
            :key="index"
          >
            <span class="step-number">
              {{ index + 1 }}
            </span>

            <p>{{ step }}</p>
          </li>
        </ol>
      </section>

      <section
        v-if="procedure.warnings.length > 0"
        class="content-card"
      >
        <h2>Important Warnings</h2>

        <ul class="warning-list">
          <li
            v-for="(warning, index) in procedure.warnings"
            :key="index"
          >
            <span class="warning-icon">
              !
            </span>

            <p>{{ warning }}</p>
          </li>
        </ul>
      </section>

      <section class="employee-note">
        <div class="note-icon">
          i
        </div>

        <div>
          <strong>
            Question not covered here?
          </strong>

          <p>
            <RouterLink to="/query">Ask Handoff</RouterLink>.
            If no approved procedure has the answer, your question
            goes to the owner as a knowledge gap.
          </p>
        </div>
      </section>
    </template>

  </main>
</template>

<style scoped>
/* =========================================
   Page Layout
   ========================================= */

.procedure-detail {
  min-height: calc(100vh - 72px);
  padding: 42px 24px 70px;
  background: #f8f6f2;
}

.page-header,
.content-card,
.status-message,
.error-message,
.employee-note {
  max-width: 880px;
  margin-left: auto;
  margin-right: auto;
}

.page-header {
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #d26f3d;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.page-header h1 {
  margin: 0;
  color: #173c35;
  font-size: 34px;
  line-height: 1.1;
}

.page-header p:last-child {
  margin: 10px 0 0;
  color: #65756f;
  font-size: 15px;
}

.back-button {
  flex: 0 0 auto;
  display: inline-block;
  padding: 9px 14px;
  border: 1px solid #d7d0c7;
  border-radius: 7px;
  color: #275b4f;
  background: white;
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
}

.back-button:hover {
  background: #f7f3ed;
}

/* =========================================
   Loading / Error States
   ========================================= */

.status-message,
.error-message {
  margin-bottom: 24px;
  padding: 22px;
  border: 1px solid #e2ddd5;
  border-radius: 10px;
  background: white;
}

.status-message strong {
  color: #173c35;
  font-size: 14px;
}

.status-message p {
  margin: 5px 0 0;
  color: #75817c;
  font-size: 13px;
}

.error-message {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  border-color: #e6c4b5;
  background: #fbf1ec;
}

.error-icon {
  flex: 0 0 auto;
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #b85f34;
  color: white;
  font-weight: 700;
}

.error-message strong {
  color: #9a4f2d;
  font-size: 14px;
}

.error-message p {
  margin: 4px 0 12px;
  color: #74594c;
  font-size: 13px;
}

/* =========================================
   Steps and Warnings
   ========================================= */

.content-card {
  margin-bottom: 16px;
  padding: 24px;
  border: 1px solid #e2ddd5;
  border-radius: 10px;
  background: white;
  box-shadow: 0 3px 12px rgba(31, 45, 40, 0.04);
}

.content-card h2 {
  margin: 0 0 16px;
  color: #173c35;
  font-size: 20px;
}

.step-list,
.warning-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-list li,
.warning-list li {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.step-list p,
.warning-list p {
  margin: 3px 0 0;
  color: #34443f;
  font-size: 15px;
  line-height: 1.55;
}

.step-number,
.warning-icon {
  flex: 0 0 auto;
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
}

.step-number {
  background: #275b4f;
  color: white;
}

.warning-icon {
  background: #f5e1d6;
  color: #b85f34;
}

/* =========================================
   Ask Handoff Note
   ========================================= */

.employee-note {
  margin-top: 24px;
  padding: 18px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  border: 1px solid #ddd8d0;
  border-radius: 10px;
  background: #f3efe9;
}

.note-icon {
  flex: 0 0 auto;
  width: 25px;
  height: 25px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #275b4f;
  color: white;
  font-size: 13px;
  font-weight: 700;
}

.employee-note strong {
  color: #31544b;
  font-size: 13px;
}

.employee-note p {
  margin: 4px 0 0;
  color: #6e7974;
  font-size: 13px;
  line-height: 1.5;
}

.employee-note a {
  color: #275b4f;
  font-weight: 700;
}

/* =========================================
   Responsive Layout
   ========================================= */

@media (max-width: 760px) {
  .procedure-detail {
    padding: 28px 16px 50px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 560px) {
  .page-header h1 {
    font-size: 28px;
  }
}
</style>