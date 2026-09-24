<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch } from '../api.js'

const router = useRouter()

const role = localStorage.getItem('userRole')

const isOwner = computed(() => {
  return role === 'owner'
})

const procedures = ref([])
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

const formatStatus = (status) => {
  if (!status) {
    return 'Unknown'
  }

  return status
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

const statusClass = (status) => {
  if (!status) {
    return ''
  }

  const normalizedStatus = status
    .toLowerCase()
    .replaceAll('_', '-')
    .replaceAll(' ', '-')

  if (normalizedStatus === 'approved') {
    return 'approved'
  }

  if (normalizedStatus === 'pending') {
    return 'pending'
  }

  if (normalizedStatus === 'needs-changes') {
    return 'needs'
  }

  return ''
}

const loadProcedures = async () => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await apiFetch(
      '/api/procedures'
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.detail || 'Unable to load procedures.'
      )
    }

    procedures.value = Array.isArray(data)
      ? data
      : []
  } catch (error) {
    console.error(error)

    errorMessage.value =
      error.message ||
      'Handoff could not connect to the procedure service.'
  } finally {
    isLoading.value = false
  }
}

const visibleProcedures = computed(() => {
  if (isOwner.value) {
    return procedures.value
  }

  return procedures.value.filter(
    (procedure) =>
      procedure.status?.toLowerCase() === 'approved'
  )
})

const approvedCount = computed(() => {
  return procedures.value.filter(
    (procedure) =>
      procedure.status?.toLowerCase() === 'approved'
  ).length
})

const pendingCount = computed(() => {
  return procedures.value.filter(
    (procedure) =>
      procedure.status?.toLowerCase() === 'pending'
  ).length
})

const addProcedure = () => {
  router.push('/capture-procedure')
}

onMounted(() => {
  loadProcedures()
})
</script>

<template>
  <main class="procedures">

    <!-- =========================================
         Owner Page Header
         ========================================= -->
    <section
      v-if="isOwner"
      class="page-header"
    >
      <div>
        <p class="eyebrow">Owner Workspace</p>

        <h1>Procedures</h1>

        <p>
          View documented procedures and review their current status.
        </p>
      </div>

      <button
        class="add-button"
        type="button"
        @click="addProcedure"
      >
        + Add Procedure
      </button>
    </section>

    <!-- =========================================
         Employee Page Header
         ========================================= -->
    <section
      v-else
      class="page-header employee-header"
    >
      <div>
        <p class="eyebrow">Employee Knowledge Base</p>

        <h1>Approved Procedures</h1>

        <p>
          Browse the procedures your organization has reviewed
          and approved for employees.
        </p>
      </div>
    </section>

    <!-- =========================================
         Loading State
         ========================================= -->
    <section
      v-if="isLoading"
      class="status-message"
    >
      <strong>Loading procedures...</strong>

      <p>
        Handoff is retrieving the current knowledge base.
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
        <strong>Unable to load procedures</strong>

        <p>
          {{ errorMessage }}
        </p>

        <button
          type="button"
          class="retry-button"
          @click="loadProcedures"
        >
          Try Again
        </button>
      </div>
    </section>

    <template v-else>

      <!-- =========================================
           Owner Procedure Summary
           ========================================= -->
      <section
        v-if="isOwner"
        class="summary"
      >
        <div class="summary-item">
          <span class="summary-label">
            Total Procedures
          </span>

          <strong>
            {{ procedures.length }}
          </strong>
        </div>

        <div class="summary-item">
          <span class="summary-label">
            Approved
          </span>

          <strong>
            {{ approvedCount }}
          </strong>
        </div>

        <div class="summary-item">
          <span class="summary-label">
            Pending Review
          </span>

          <strong>
            {{ pendingCount }}
          </strong>
        </div>
      </section>

      <!-- =========================================
           Employee Procedure Summary
           ========================================= -->
      <section
        v-else
        class="employee-summary"
      >
        <div class="employee-summary-item">
          <span class="summary-label">
            Available Procedures
          </span>

          <strong>
            {{ visibleProcedures.length }}
          </strong>

          <p>
            Approved and available for your use
          </p>
        </div>
      </section>

      <!-- =========================================
           Empty State
           ========================================= -->
      <section
        v-if="visibleProcedures.length === 0"
        class="empty-state"
      >
        <strong>
          {{
            isOwner
              ? 'No procedures have been added yet.'
              : 'No approved procedures are available yet.'
          }}
        </strong>

        <p>
          {{
            isOwner
              ? 'Capture and approve a procedure to begin building the Handoff knowledge base.'
              : 'Approved procedures will appear here after they are reviewed by the Owner.'
          }}
        </p>

        <button
          v-if="isOwner"
          type="button"
          class="add-button"
          @click="addProcedure"
        >
          + Add Procedure
        </button>
      </section>

      <!-- =========================================
           Procedure List
           ========================================= -->
      <section
        v-else
        class="procedure-list"
      >

        <article
          v-for="procedure in visibleProcedures"
          :key="procedure.id"
          class="procedure-card"
        >

          <div class="procedure-info">

            <div class="title-row">

              <h2>
                {{ procedure.title }}
              </h2>

              <span
                v-if="isOwner"
                class="status"
                :class="statusClass(procedure.status)"
              >
                {{ formatStatus(procedure.status) }}
              </span>

              <span
                v-else
                class="status approved"
              >
                Approved
              </span>

            </div>

            <p>
              Last confirmed:
              {{ formatDate(procedure.last_confirmed) }}
            </p>

          </div>

          <RouterLink
            v-if="isOwner"
            :to="{
              path: '/procedure-review',
              query: { id: procedure.id }
            }"
            class="review-button"
          >
            Review
          </RouterLink>

        </article>

      </section>

      <!-- =========================================
           Employee Information
           ========================================= -->
      <section
        v-if="!isOwner && visibleProcedures.length > 0"
        class="employee-note"
      >
        <div class="note-icon">
          i
        </div>

        <div>
          <strong>
            Approved knowledge
          </strong>

          <p>
            These procedures have been reviewed and approved
            by your organization's owner. If you cannot find
            the information you need, ask Handoff a question.
          </p>
        </div>
      </section>

      <!-- =========================================
           Live Data Notice
           ========================================= -->
      <section class="prototype-note">
        <strong>Connected knowledge base</strong>

        <p>
          Procedure data is retrieved from the Handoff API
          and PostgreSQL knowledge base.
        </p>
      </section>

    </template>

  </main>
</template>

<style scoped>
/* =========================================
   Page Layout
   ========================================= */

.procedures {
  min-height: calc(100vh - 72px);
  padding: 42px 24px 70px;
  background: #f8f6f2;
}

.page-header {
  max-width: 1120px;
  margin: 0 auto 24px;
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

.add-button {
  min-height: 42px;
  padding: 0 18px;
  border: 1px solid #275b4f;
  border-radius: 8px;
  background: #275b4f;
  color: white;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.add-button:hover {
  background: #204d43;
}


/* =========================================
   Loading / Error / Empty States
   ========================================= */

.status-message,
.error-message,
.empty-state {
  max-width: 1120px;
  margin: 0 auto 24px;
  padding: 22px;
  border: 1px solid #e2ddd5;
  border-radius: 10px;
  background: white;
}

.status-message strong,
.empty-state strong {
  color: #173c35;
  font-size: 14px;
}

.status-message p,
.empty-state p {
  margin: 5px 0 0;
  color: #75817c;
  font-size: 13px;
  line-height: 1.5;
}

.empty-state .add-button {
  margin-top: 16px;
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
  margin: 4px 0 10px;
  color: #74594c;
  font-size: 13px;
}

.retry-button {
  padding: 8px 13px;
  border: 1px solid #d7c2b7;
  border-radius: 7px;
  background: white;
  color: #8f4d2e;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}


/* =========================================
   Summary
   ========================================= */

.summary {
  max-width: 1120px;
  margin: 0 auto 24px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.summary-item {
  padding: 20px;
  border: 1px solid #e2ddd5;
  border-radius: 10px;
  background: white;
}

.summary-label {
  display: block;
  color: #75817c;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.summary-item strong {
  display: block;
  margin-top: 6px;
  color: #173c35;
  font-size: 28px;
}


/* =========================================
   Employee Summary
   ========================================= */

.employee-summary {
  max-width: 1120px;
  margin: 0 auto 24px;
}

.employee-summary-item {
  padding: 20px;
  border: 1px solid #e2ddd5;
  border-radius: 10px;
  background: white;
}

.employee-summary-item strong {
  display: block;
  margin-top: 6px;
  color: #173c35;
  font-size: 28px;
}

.employee-summary-item p {
  margin: 5px 0 0;
  color: #75817c;
  font-size: 13px;
}


/* =========================================
   Procedure List
   ========================================= */

.procedure-list {
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.procedure-card {
  padding: 20px 22px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  border: 1px solid #e2ddd5;
  border-radius: 10px;
  background: white;
  box-shadow: 0 3px 12px rgba(31, 45, 40, 0.04);
}

.procedure-info {
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.title-row h2 {
  margin: 0;
  color: #173c35;
  font-size: 18px;
}

.procedure-info > p {
  margin: 7px 0 0;
  color: #7a8580;
  font-size: 13px;
}


/* =========================================
   Status Badges
   ========================================= */

.status {
  display: inline-flex;
  align-items: center;
  padding: 5px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.status.approved {
  background: #dcebe5;
  color: #275b4f;
}

.status.pending {
  background: #f5e7d9;
  color: #9a5d3b;
}

.status.needs {
  background: #f3dddd;
  color: #a04e4e;
}


/* =========================================
   Review Button
   ========================================= */

.review-button {
  flex: 0 0 auto;
  padding: 9px 14px;
  border: 1px solid #d7d0c7;
  border-radius: 7px;
  color: #275b4f;
  background: white;
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
}

.review-button:hover {
  background: #f7f3ed;
}


/* =========================================
   Employee Information
   ========================================= */

.employee-note {
  max-width: 1120px;
  margin: 24px auto 0;
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


/* =========================================
   Knowledge Base Notice
   ========================================= */

.prototype-note {
  max-width: 1120px;
  margin: 24px auto 0;
  padding: 16px;
  border: 1px dashed #d8d0c6;
  border-radius: 9px;
  background: #fbf9f5;
}

.prototype-note strong {
  color: #6b665e;
  font-size: 12px;
}

.prototype-note p {
  margin: 5px 0 0;
  color: #88827a;
  font-size: 12px;
  line-height: 1.5;
}


/* =========================================
   Responsive Layout
   ========================================= */

@media (max-width: 760px) {
  .procedures {
    padding: 28px 16px 50px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary {
    grid-template-columns: 1fr;
  }

  .procedure-card {
    align-items: flex-start;
  }
}

@media (max-width: 560px) {
  .page-header h1 {
    font-size: 28px;
  }

  .procedure-card {
    flex-direction: column;
  }

  .review-button {
    width: 100%;
    box-sizing: border-box;
    text-align: center;
  }
}
</style>