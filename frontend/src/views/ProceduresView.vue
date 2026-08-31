<template>
  <main class="procedures">
    <!-- Page heading -->
    <section class="page-header">
      <div>
        <p class="eyebrow">Owner Workspace</p>
        <h1>Procedures</h1>
        <p>
          View documented procedures and review their current status.
        </p>
      </div>

      <!-- Future procedure creation action -->
      <button class="add-button" type="button">
        + Add Procedure
      </button>
    </section>

    <!-- Procedure summary -->
    <section class="summary">
      <div class="summary-item">
        <span class="summary-label">Total Procedures</span>
        <strong>{{ procedures.length }}</strong>
      </div>

      <div class="summary-item">
        <span class="summary-label">Approved</span>
        <strong>{{ approvedCount }}</strong>
      </div>

      <div class="summary-item">
        <span class="summary-label">Pending Review</span>
        <strong>{{ pendingCount }}</strong>
      </div>
    </section>

    <!-- Procedure list -->
    <section class="procedure-list">
      <article
        v-for="procedure in procedures"
        :key="procedure.id"
        class="procedure-card"
      >
        <div class="procedure-info">
          <div class="title-row">
            <h2>{{ procedure.title }}</h2>

            <span
              class="status"
              :class="procedure.status.toLowerCase()"
            >
              {{ procedure.status }}
            </span>
          </div>

          <p>
            Last confirmed: {{ procedure.lastConfirmed }}
          </p>
        </div>

        <!-- Opens the procedure review screen -->
        <RouterLink
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

    <!-- Documentation gap link -->
    <div class="bottom-action">
      <RouterLink to="/gaps" class="secondary-link">
        View Documentation Gaps →
      </RouterLink>
    </div>
  </main>
</template>

<script setup>
// Temporary data used while the FastAPI endpoint is being developed.
// This will later be replaced with data from GET /api/procedures.
const procedures = [
  {
    id: 1,
    title: 'Customer Returns',
    status: 'Approved',
    lastConfirmed: 'August 30, 2026'
  },
  {
    id: 2,
    title: 'Opening Procedure',
    status: 'Approved',
    lastConfirmed: 'August 28, 2026'
  },
  {
    id: 3,
    title: 'New Employee Setup',
    status: 'Pending',
    lastConfirmed: 'August 25, 2026'
  }
]

// Calculate procedure totals for the summary section.
const approvedCount = procedures.filter(
  (procedure) => procedure.status === 'Approved'
).length

const pendingCount = procedures.filter(
  (procedure) => procedure.status === 'Pending'
).length
</script>

<style scoped>
.procedures {
  width: min(1100px, calc(100% - 40px));
  margin: 0 auto;
  padding: 55px 0 70px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 30px;
  margin-bottom: 35px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #b65f32;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 1.3px;
  text-transform: uppercase;
}

.page-header h1 {
  margin: 0 0 10px;
  color: #263238;
  font-size: 40px;
}

.page-header p {
  margin: 0;
  color: #68747a;
  font-size: 17px;
  line-height: 1.5;
}

.add-button {
  white-space: nowrap;
}

/* Procedure statistics */
.summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  margin-bottom: 28px;
}

.summary-item {
  padding: 22px 24px;
  background: #ffffff;
  border: 1px solid #e4ddd7;
  border-radius: 12px;
}

.summary-label {
  display: block;
  margin-bottom: 8px;
  color: #68747a;
  font-size: 14px;
}

.summary-item strong {
  color: #263238;
  font-size: 28px;
}

/* Individual procedure cards */
.procedure-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.procedure-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 25px;
  padding: 24px;
  background: #ffffff;
  border: 1px solid #e4ddd7;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(60, 45, 35, 0.04);
}

.procedure-info {
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.procedure-card h2 {
  margin: 0;
  color: #263238;
  font-size: 20px;
}

.procedure-card p {
  margin: 8px 0 0;
  color: #68747a;
  font-size: 14px;
}

/* Procedure status indicators */
.status {
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
}

.status.approved {
  background: #e7f1eb;
  color: #35634a;
}

.status.pending {
  background: #f3e3d8;
  color: #914923;
}

/* Procedure review action */
.review-button {
  flex-shrink: 0;
  padding: 10px 18px;
  border-radius: 8px;
  background: #b65f32;
  color: #ffffff;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  transition:
    background-color 0.2s ease,
    transform 0.15s ease,
    box-shadow 0.2s ease;
}

.review-button:hover {
  background: #914923;
  color: #ffffff;
  box-shadow: 0 3px 8px rgba(80, 45, 30, 0.18);
  transform: translateY(-1px);
}

/* Link to the documentation gaps page */
.bottom-action {
  margin-top: 28px;
}

.secondary-link {
  color: #b65f32;
  font-weight: 600;
  text-decoration: none;
}

.secondary-link:hover {
  color: #914923;
}

@media (max-width: 700px) {
  .procedures {
    width: min(100% - 30px, 1100px);
    padding: 40px 0 55px;
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
    flex-direction: column;
  }

  .review-button {
    width: 100%;
    text-align: center;
  }
}
</style>
