<template>
  <main class="review">
    <!-- Page heading -->
    <section class="page-header">
      <div>
        <p class="eyebrow">Owner Workspace</p>
        <h1>Review Procedure</h1>
        <p>
          Review and edit the AI-generated procedure before approving it.
        </p>
      </div>

      <span class="status pending">Pending Review</span>
    </section>

    <!-- Procedure editing form -->
    <form @submit.prevent="approveProcedure" class="review-form">
      <!-- Procedure details -->
      <section class="form-section">
        <div class="section-heading">
          <h2>Procedure Details</h2>
          <p>Review the procedure information before approval.</p>
        </div>

        <div class="form-group">
          <label for="title">Procedure Title</label>
          <input
            id="title"
            v-model="procedure.title"
            type="text"
            required
          />
        </div>
      </section>

      <!-- Structured procedure steps -->
      <section class="form-section">
        <div class="section-heading">
          <h2>Procedure Steps</h2>
          <p>Review the steps generated from the submitted transcript.</p>
        </div>

        <div
          v-for="(step, index) in procedure.steps"
          :key="index"
          class="step-row"
        >
          <span class="step-number">{{ index + 1 }}</span>

          <input
            v-model="procedure.steps[index]"
            type="text"
            :aria-label="`Procedure step ${index + 1}`"
            required
          />
        </div>
      </section>

      <!-- Procedure warnings -->
      <section class="form-section">
        <div class="section-heading">
          <h2>Warnings</h2>
          <p>Review any warnings that employees should be aware of.</p>
        </div>

        <div
          v-for="(warning, index) in procedure.warnings"
          :key="index"
          class="warning-row"
        >
          <span class="warning-icon" aria-hidden="true">!</span>

          <input
            v-model="procedure.warnings[index]"
            type="text"
            :aria-label="`Warning ${index + 1}`"
          />
        </div>
      </section>

      <!-- Procedure metadata -->
      <section class="metadata">
        <div>
          <span>Version</span>
          <strong>{{ procedure.version }}</strong>
        </div>

        <div>
          <span>Last Confirmed</span>
          <strong>{{ procedure.lastConfirmed }}</strong>
        </div>
      </section>

      <!-- Approval actions -->
      <div class="form-actions">
        <RouterLink to="/procedures" class="cancel-button">
          Back to Procedures
        </RouterLink>

        <button type="submit">
          Approve Procedure
        </button>
      </div>
    </form>

    <!-- Confirmation message -->
    <div v-if="approved" class="success-message">
      <strong>Procedure approved successfully.</strong>
      <span>
        This procedure is now ready to be used as approved documentation.
      </span>
    </div>
  </main>
</template>

<script setup>
import { ref } from 'vue'

// Temporary procedure data used while the FastAPI endpoints are being developed.
// This will later be replaced with data from the selected procedure.
const procedure = ref({
  id: 1,
  title: 'Customer Returns',
  steps: [
    'Ask the customer for the receipt.',
    'Check the purchase date.',
    'Verify that the item is eligible for return.'
  ],
  warnings: [
    'Ask a manager if the customer does not have a receipt.'
  ],
  version: 1,
  lastConfirmed: 'August 30, 2026'
})

const approved = ref(false)

// Temporary approval action.
// This will later send the finalized procedure to POST /api/approve-procedure.
function approveProcedure() {
  approved.value = true
}
</script>

<style scoped>
.review {
  width: min(1000px, calc(100% - 40px));
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

.status {
  display: inline-block;
  padding: 7px 13px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}

.status.pending {
  background: #f3e3d8;
  color: #914923;
}

/* Main procedure editing form */
.review-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Individual sections of the review form */
.form-section {
  padding: 28px;
  background: #ffffff;
  border: 1px solid #e4ddd7;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(60, 45, 35, 0.04);
}

.section-heading {
  margin-bottom: 22px;
}

.section-heading h2 {
  margin: 0 0 6px;
  color: #263238;
  font-size: 21px;
}

.section-heading p {
  margin: 0;
  color: #68747a;
  font-size: 14px;
}

/* Form fields */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

label {
  color: #39484e;
  font-size: 14px;
  font-weight: 600;
}

input {
  width: 100%;
  padding: 12px 14px;
  color: #263238;
  background: #ffffff;
  border: 1px solid #d8d0ca;
  border-radius: 8px;
  outline: none;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

input:focus {
  border-color: #b65f32;
  box-shadow: 0 0 0 3px #f3e3d8;
}

/* Numbered procedure steps */
.step-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.step-row:last-child {
  margin-bottom: 0;
}

.step-number {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f3e3d8;
  color: #914923;
  font-size: 13px;
  font-weight: 700;
}

/* Warning fields */
.warning-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.warning-icon {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f3e3d8;
  color: #914923;
  font-weight: 800;
}

/* Procedure version information */
.metadata {
  display: flex;
  gap: 50px;
  padding: 22px 28px;
  background: #f3e3d8;
  border-radius: 12px;
}

.metadata div {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.metadata span {
  color: #80533c;
  font-size: 13px;
}

.metadata strong {
  color: #263238;
  font-size: 15px;
}

/* Approval actions */
.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 15px;
  padding-top: 5px;
}

.cancel-button {
  padding: 11px 18px;
  color: #68747a;
  text-decoration: none;
  font-weight: 600;
}

.cancel-button:hover {
  color: #914923;
}

.form-actions button {
  padding: 12px 22px;
}

/* Approval confirmation */
.success-message {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-top: 25px;
  padding: 18px 22px;
  background: #e7f1eb;
  border: 1px solid #c8dfd0;
  border-radius: 10px;
  color: #35634a;
}

.success-message strong {
  font-size: 15px;
}

.success-message span {
  font-size: 14px;
}

@media (max-width: 700px) {
  .review {
    width: min(100% - 30px, 1000px);
    padding: 40px 0 55px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .form-section {
    padding: 22px;
  }

  .metadata {
    flex-direction: column;
    gap: 18px;
  }

  .form-actions {
    flex-direction: column-reverse;
    align-items: stretch;
  }

  .form-actions button,
  .cancel-button {
    width: 100%;
    text-align: center;
  }
}
</style>
