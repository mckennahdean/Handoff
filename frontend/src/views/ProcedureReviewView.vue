<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch } from '../api.js'

const router = useRouter()

const storedProcedure = localStorage.getItem('pendingProcedure')

const pendingProcedure = storedProcedure
  ? JSON.parse(storedProcedure)
  : null

const title = ref(
  pendingProcedure?.title || 'Customer Returns'
)

const captureDescription = computed(() => {
  if (pendingProcedure?.captureMethod === 'upload') {
    return `Captured using Uploaded audio${
      pendingProcedure.audioFileName
        ? ` — ${pendingProcedure.audioFileName}`
        : ''
    }`
  }

  if (pendingProcedure?.captureMethod === 'manual') {
    return 'Captured using Manual knowledge entry'
  }

  if (pendingProcedure?.captureMethod === 'record') {
    const duration = pendingProcedure.recordingDuration

    if (duration) {
      return `Captured using Owner recording — ${duration}`
    }

    return 'Captured using Owner recording'
  }

  return 'Captured using Owner recording'
})

const steps = ref(
  Array.isArray(pendingProcedure?.steps) &&
  pendingProcedure.steps.length > 0
    ? [...pendingProcedure.steps]
    : [
        'Verify the customer and original purchase information.',
        'Confirm that the item meets the return requirements.',
        'Process the return using the approved return method.',
        'Provide the customer with the appropriate confirmation.'
      ]
)

const warnings = ref(
  Array.isArray(pendingProcedure?.warnings)
    ? [...pendingProcedure.warnings]
    : [
        'Items outside the return policy require Owner review.',
        'Refunds should not be issued until the return requirements are verified.'
      ]
)

const showChangesModal = ref(false)
const changesComment = ref('')
const message = ref('')
const errorMessage = ref('')
const isSubmitting = ref(false)
const approvedLastConfirmed = ref(null)

const addStep = () => {
  steps.value.push('')
}

const removeStep = (index) => {
  steps.value.splice(index, 1)
}

const addWarning = () => {
  warnings.value.push('')
}

const removeWarning = (index) => {
  warnings.value.splice(index, 1)
}

const submitChanges = () => {
  if (!changesComment.value.trim()) {
    return
  }

  isSubmitting.value = true

  const changesRequest = {
    title: title.value,
    status: 'Needs Changes',
    comment: changesComment.value.trim(),
    steps: steps.value,
    warnings: warnings.value
  }

  localStorage.setItem(
    'procedureChanges',
    JSON.stringify(changesRequest)
  )

  setTimeout(() => {
    isSubmitting.value = false
    showChangesModal.value = false
    message.value = 'Procedure returned for changes.'
    errorMessage.value = ''
    changesComment.value = ''
  }, 400)
}

const approveProcedure = async () => {
  if (isSubmitting.value) {
    return
  }

  message.value = ''
  errorMessage.value = ''

  const cleanTitle = title.value.trim()

  const cleanSteps = steps.value
    .map((step) => step.trim())
    .filter((step) => step.length > 0)

  const cleanWarnings = warnings.value
    .map((warning) => warning.trim())
    .filter((warning) => warning.length > 0)

  if (!cleanTitle) {
    errorMessage.value =
      'Procedure title cannot be empty.'
    return
  }

  if (cleanSteps.length === 0) {
    errorMessage.value =
      'Procedure must contain at least one step.'
    return
  }

  isSubmitting.value = true

  try {
    const response = await apiFetch(
      '/api/approve-procedure',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: cleanTitle,
          steps: cleanSteps,
          warnings: cleanWarnings
        })
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.detail || 'Unable to approve procedure.'
      )
    }

    steps.value = cleanSteps
    warnings.value = cleanWarnings

    approvedLastConfirmed.value =
      data.last_confirmed || null

    localStorage.removeItem('pendingProcedure')

    message.value = 'Procedure approved successfully.'
  } catch (error) {
    console.error(error)

    errorMessage.value =
      error.message ||
      'Handoff could not approve the procedure.'
  } finally {
    isSubmitting.value = false
  }
}

const continueReviewing = () => {
  router.push('/procedures')
}

const goToDashboard = () => {
  router.push('/owner-dashboard')
}

const isApproved = computed(() => {
  return message.value === 'Procedure approved successfully.'
})

const formattedLastConfirmed = computed(() => {
  if (!approvedLastConfirmed.value) {
    return isApproved.value
      ? 'Confirmed'
      : 'Not yet approved'
  }

  const date = new Date(approvedLastConfirmed.value)

  if (Number.isNaN(date.getTime())) {
    return approvedLastConfirmed.value
  }

  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
})
</script>

<template>
  <main class="review-page">

    <section class="page-header">
      <div>
        <p class="eyebrow">Owner Workspace</p>

        <h1>Procedure Review</h1>

        <p>
          Review the AI-structured procedure before making it
          available to employees.
        </p>
      </div>

      <div class="workflow-status">
        <span class="workflow-step complete">
          1. Capture
        </span>

        <span class="workflow-arrow">→</span>

        <span class="workflow-step active">
          2. Review
        </span>

        <span class="workflow-arrow">→</span>

        <span
          class="workflow-step"
          :class="{ complete: isApproved }"
        >
          3. Approve
        </span>
      </div>
    </section>

    <section class="approval-notice">
      <div class="notice-icon">
        ✓
      </div>

      <div>
        <strong>Owner approval required</strong>

        <p>
          Handoff will not make this procedure available to
          employees until an Owner reviews and approves it.
        </p>
      </div>
    </section>

    <section
      v-if="message"
      class="success-message"
      :class="{ approved: isApproved }"
    >
      <span class="success-icon">✓</span>

      <div>
        <strong>{{ message }}</strong>

        <p v-if="isApproved">
          This procedure is now approved and available to
          employees through the knowledge base.
        </p>
      </div>
    </section>

    <section
      v-if="errorMessage"
      class="error-message"
    >
      <span class="error-icon">!</span>

      <div>
        <strong>Unable to approve procedure</strong>

        <p>
          {{ errorMessage }}
        </p>
      </div>
    </section>

    <section class="procedure-card">

      <div class="procedure-header">
        <div>
          <p class="structured-label">
            Structured Procedure
          </p>

          <h2>{{ title }}</h2>

          <p class="capture-description">
            {{ captureDescription }}
          </p>
        </div>

        <div class="version">
          <span>Version</span>
          <strong>1.0</strong>
        </div>
      </div>

      <section class="content-section">
        <div class="section-heading">
          <div>
            <h3>Procedure Steps</h3>

            <p>
              Review and edit the steps before approval.
            </p>
          </div>

          <span class="ai-badge">
            AI Structured
          </span>
        </div>

        <div class="steps-list">

          <div
            v-for="(step, index) in steps"
            :key="index"
            class="step-row"
          >
            <span class="step-number">
              {{ index + 1 }}
            </span>

            <textarea
              v-model="steps[index]"
              rows="2"
              :disabled="isApproved"
              :aria-label="`Procedure step ${index + 1}`"
            ></textarea>

            <button
              v-if="steps.length > 1 && !isApproved"
              type="button"
              class="remove-button"
              @click="removeStep(index)"
              :aria-label="`Remove step ${index + 1}`"
            >
              ×
            </button>
          </div>

        </div>

        <button
          v-if="!isApproved"
          type="button"
          class="add-item-button"
          @click="addStep"
        >
          + Add Step
        </button>
      </section>

      <section class="content-section warnings-section">
        <div class="section-heading">
          <div>
            <h3>Important Warnings</h3>

            <p>
              Confirm that exceptions and important cautions
              are accurately represented.
            </p>
          </div>
        </div>

        <div class="warnings-list">

          <div
            v-for="(warning, index) in warnings"
            :key="index"
            class="warning-row"
          >
            <span class="warning-icon">
              !
            </span>

            <textarea
              v-model="warnings[index]"
              rows="2"
              :disabled="isApproved"
              :aria-label="`Warning ${index + 1}`"
            ></textarea>

            <button
              v-if="warnings.length > 1 && !isApproved"
              type="button"
              class="remove-button"
              @click="removeWarning(index)"
              :aria-label="`Remove warning ${index + 1}`"
            >
              ×
            </button>
          </div>

        </div>

        <button
          v-if="!isApproved"
          type="button"
          class="add-item-button"
          @click="addWarning"
        >
          + Add Warning
        </button>
      </section>

      <section class="metadata-grid">

        <div class="metadata-card">
          <span>Last Confirmed</span>

          <strong>
            {{ formattedLastConfirmed }}
          </strong>
        </div>

        <div class="metadata-card">
          <span>Availability</span>

          <strong>
            {{
              isApproved
                ? 'Available to employees'
                : 'Owner review required'
            }}
          </strong>
        </div>

      </section>

      <section class="action-area">

        <div class="action-left">
          <button
            type="button"
            class="secondary-button"
            @click="goToDashboard"
          >
            Back to Dashboard
          </button>
        </div>

        <div class="action-right">

          <button
            v-if="!isApproved"
            type="button"
            class="secondary-button"
            @click="showChangesModal = true"
          >
            Needs Changes
          </button>

          <button
            v-if="!isApproved"
            type="button"
            class="primary-button"
            :disabled="isSubmitting"
            @click="approveProcedure"
          >
            {{
              isSubmitting
                ? 'Approving...'
                : 'Approve Procedure'
            }}
          </button>

          <button
            v-if="isApproved"
            type="button"
            class="primary-button"
            @click="continueReviewing"
          >
            View Procedures
          </button>

        </div>

      </section>

    </section>

    <section
      v-if="isApproved"
      class="post-approval"
    >
      <div>
        <span class="post-approval-icon">✓</span>

        <div>
          <strong>
            {{ title }} is now part of the approved knowledge base.
          </strong>

          <p>
            Employees can now access this procedure through
            Approved Procedures and Ask Handoff.
          </p>
        </div>
      </div>

      <button
        type="button"
        class="secondary-button"
        @click="continueReviewing"
      >
        View Approved Procedures
      </button>
    </section>

    <div
      v-if="showChangesModal"
      class="modal-backdrop"
      @click.self="showChangesModal = false"
    >
      <section
        class="changes-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="changes-title"
      >

        <div class="modal-header">
          <div>
            <p class="eyebrow">Owner Review</p>

            <h2 id="changes-title">
              Request Changes
            </h2>
          </div>

          <button
            type="button"
            class="close-button"
            aria-label="Close"
            @click="showChangesModal = false"
          >
            ×
          </button>
        </div>

        <p class="modal-description">
          Explain what needs to be corrected before this
          procedure can be approved.
        </p>

        <label for="changes-comment">
          Review Comment
        </label>

        <textarea
          id="changes-comment"
          v-model="changesComment"
          rows="5"
          placeholder="Describe the changes that are needed..."
        ></textarea>

        <div class="modal-actions">

          <button
            type="button"
            class="secondary-button"
            @click="showChangesModal = false"
          >
            Cancel
          </button>

          <button
            type="button"
            class="primary-button"
            :disabled="
              !changesComment.trim() || isSubmitting
            "
            @click="submitChanges"
          >
            {{
              isSubmitting
                ? 'Submitting...'
                : 'Submit Changes'
            }}
          </button>

        </div>

      </section>
    </div>

  </main>
</template>

<style scoped>
.review-page {
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

.page-header > div:first-child > p:last-child {
  margin: 10px 0 0;
  color: #65756f;
  font-size: 15px;
}

.workflow-status {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.workflow-step {
  padding: 8px 12px;
  border-radius: 999px;
  background: #ebe7df;
  color: #68766f;
  font-size: 12px;
  font-weight: 700;
}

.workflow-step.complete,
.workflow-step.active {
  background: #dcebe5;
  color: #275b4f;
}

.workflow-step.active {
  box-shadow: inset 0 0 0 1px #b9d5cb;
}

.workflow-arrow {
  color: #9a9f9b;
}

.approval-notice {
  max-width: 1120px;
  margin: 0 auto 24px;
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  border: 1px solid #bfd9cf;
  border-radius: 10px;
  background: #edf7f2;
}

.notice-icon,
.success-icon,
.post-approval-icon {
  flex: 0 0 auto;
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #275b4f;
  color: white;
  font-weight: 700;
}

.approval-notice strong {
  display: block;
  color: #1c5145;
  font-size: 14px;
}

.approval-notice p {
  margin: 4px 0 0;
  color: #5f716b;
  font-size: 13px;
}

.success-message {
  max-width: 1120px;
  margin: 0 auto 24px;
  padding: 15px 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  border: 1px solid #c9dcd4;
  border-radius: 10px;
  background: #f0f7f4;
}

.success-message strong {
  color: #275b4f;
}

.success-message p {
  margin: 4px 0 0;
  color: #64736e;
  font-size: 13px;
}

.error-message {
  max-width: 1120px;
  margin: 0 auto 24px;
  padding: 15px 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  border: 1px solid #e6c4b5;
  border-radius: 10px;
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
}

.error-message p {
  margin: 4px 0 0;
  color: #74594c;
  font-size: 13px;
}

.procedure-card {
  max-width: 1120px;
  margin: 0 auto;
  padding: 30px;
  border: 1px solid #e2ddd5;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 4px 16px rgba(31, 45, 40, 0.05);
}

.procedure-header {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e6e0d8;
}

.structured-label {
  margin: 0 0 8px;
  color: #d26f3d;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.procedure-header h2 {
  margin: 0;
  color: #173c35;
  font-size: 26px;
}

.capture-description {
  margin: 8px 0 0;
  color: #70807a;
  font-size: 13px;
}

.version {
  min-width: 80px;
  text-align: right;
}

.version span {
  display: block;
  color: #7a8580;
  font-size: 11px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.version strong {
  display: block;
  margin-top: 3px;
  color: #173c35;
  font-size: 14px;
}

.content-section {
  padding: 28px 0;
  border-bottom: 1px solid #e6e0d8;
}

.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}

.section-heading h3 {
  margin: 0;
  color: #173c35;
  font-size: 18px;
}

.section-heading p {
  margin: 5px 0 0;
  color: #71807a;
  font-size: 13px;
}

.ai-badge {
  padding: 6px 10px;
  border-radius: 999px;
  background: #f5eee5;
  color: #9a5d3b;
  font-size: 11px;
  font-weight: 700;
}

.steps-list,
.warnings-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.step-row,
.warning-row {
  display: grid;
  grid-template-columns: 26px 1fr auto;
  align-items: start;
  gap: 10px;
}

.step-number,
.warning-icon {
  width: 24px;
  height: 24px;
  margin-top: 4px;
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
  background: #f5e4d9;
  color: #b85f34;
}

textarea {
  width: 100%;
  box-sizing: border-box;
  resize: vertical;
  border: 1px solid #ded7ce;
  border-radius: 8px;
  padding: 11px;
  background: #fffdfa;
  color: #183d36;
  font: inherit;
  font-size: 13px;
  line-height: 1.5;
}

textarea:focus {
  outline: none;
  border-color: #7da99b;
  box-shadow: 0 0 0 3px rgba(39, 91, 79, 0.08);
}

textarea:disabled {
  opacity: 0.8;
  cursor: not-allowed;
}

.remove-button {
  width: 28px;
  height: 28px;
  margin-top: 2px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: #8c8c86;
  font-size: 20px;
  cursor: pointer;
}

.remove-button:hover {
  background: #f3eee8;
  color: #b85f34;
}

.add-item-button {
  margin-top: 14px;
  padding: 8px 0;
  border: 0;
  background: transparent;
  color: #275b4f;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.metadata-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  padding: 24px 0;
}

.metadata-card {
  padding: 16px;
  border-radius: 8px;
  background: #f8f5ef;
}

.metadata-card span {
  display: block;
  margin-bottom: 5px;
  color: #75817c;
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.metadata-card strong {
  color: #183d36;
  font-size: 13px;
}

.action-area {
  padding-top: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.action-left,
.action-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.secondary-button,
.primary-button {
  min-height: 42px;
  padding: 0 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.secondary-button {
  border: 1px solid #d8d0c7;
  background: white;
  color: #37534b;
}

.secondary-button:hover {
  background: #f7f3ed;
}

.primary-button {
  border: 1px solid #275b4f;
  background: #275b4f;
  color: white;
}

.primary-button:hover {
  background: #204d43;
}

.primary-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.post-approval {
  max-width: 1120px;
  margin: 20px auto 0;
  padding: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  border: 1px solid #c8ddd5;
  border-radius: 10px;
  background: #f0f7f4;
}

.post-approval > div {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.post-approval strong {
  display: block;
  color: #275b4f;
  font-size: 14px;
}

.post-approval p {
  margin: 4px 0 0;
  color: #687771;
  font-size: 13px;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(22, 39, 34, 0.42);
}

.changes-modal {
  width: min(100%, 520px);
  padding: 26px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.18);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
}

.modal-header h2 {
  margin: 0;
  color: #173c35;
  font-size: 23px;
}

.close-button {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 50%;
  background: #f3eee8;
  color: #53635d;
  font-size: 21px;
  cursor: pointer;
}

.modal-description {
  margin: 14px 0 20px;
  color: #687771;
  font-size: 13px;
  line-height: 1.5;
}

.changes-modal label {
  display: block;
  margin-bottom: 7px;
  color: #28473f;
  font-size: 13px;
  font-weight: 700;
}

.modal-actions {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 760px) {
  .review-page {
    padding: 28px 16px 50px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .workflow-status {
    justify-content: flex-start;
  }

  .procedure-card {
    padding: 20px;
  }

  .procedure-header {
    flex-direction: column;
  }

  .version {
    text-align: left;
  }

  .metadata-grid {
    grid-template-columns: 1fr;
  }

  .action-area {
    flex-direction: column;
    align-items: stretch;
  }

  .action-left,
  .action-right {
    width: 100%;
  }

  .action-left .secondary-button,
  .action-right .secondary-button,
  .action-right .primary-button {
    flex: 1;
  }

  .post-approval {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 560px) {
  .page-header h1 {
    font-size: 28px;
  }

  .procedure-header h2 {
    font-size: 23px;
  }

  .step-row,
  .warning-row {
    grid-template-columns: 24px 1fr;
  }

  .remove-button {
    display: none;
  }

  .action-right {
    flex-direction: column;
  }

  .action-right button {
    width: 100%;
  }
}
</style>