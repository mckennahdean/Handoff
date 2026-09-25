<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch, errorMessage as apiErrorMessage } from '../api.js'

const router = useRouter()

const gaps = ref([])
const selectedGap = ref(null)
const showDetails = ref(false)
const searchQuery = ref('')
const statusFilter = ref('open')
const isLoading = ref(true)
const errorMessage = ref('')
const actionMessage = ref('')

const formatDate = (dateValue) => {
  if (!dateValue) {
    return 'Unknown'
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

const formatSimilarity = (similarity) => {
  if (
    similarity === null ||
    similarity === undefined ||
    Number.isNaN(Number(similarity))
  ) {
    return 'Not available'
  }

  return `${(Number(similarity) * 100).toFixed(1)}%`
}

const statusLabel = (status) => {
  const labels = {
    open: 'Open',
    resolved: 'Resolved',
    dismissed: 'Dismissed'
  }

  return labels[status] || 'Unknown'
}

const askedLabel = (count) => {
  return count === 1 ? 'Asked once' : `Asked ${count} times`
}

const loadGaps = async () => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await apiFetch('/api/gaps')
    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        apiErrorMessage(data, 'Unable to load knowledge gaps.')
      )
    }

    gaps.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error(error)

    errorMessage.value =
      error.message ||
      'Handoff could not connect to the knowledge gap service.'
  } finally {
    isLoading.value = false
  }
}

const openGaps = computed(() =>
  gaps.value.filter((gap) => gap.status === 'open')
)

const resolvedCount = computed(() =>
  gaps.value.filter((gap) => gap.status === 'resolved').length
)

// Total times employees asked questions that are still unanswered.
const openAskedCount = computed(() =>
  openGaps.value.reduce(
    (total, gap) => total + (gap.frequency_count || 1),
    0
  )
)

const visibleGaps = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return gaps.value.filter((gap) => {
    const matchesStatus =
      statusFilter.value === 'all' || gap.status === statusFilter.value

    const matchesSearch =
      !query || gap.question?.toLowerCase().includes(query)

    return matchesStatus && matchesSearch
  })
})

const viewGap = (gap) => {
  selectedGap.value = gap
  showDetails.value = true
}

const closeDetails = () => {
  showDetails.value = false
  selectedGap.value = null
}

const clearFilters = () => {
  searchQuery.value = ''
  statusFilter.value = 'open'
}

const dismissGap = async (gap) => {
  const confirmed = window.confirm(
    'Dismiss this question? Use this for questions no procedure ' +
    'should cover. It will move to the Dismissed list.'
  )

  if (!confirmed) {
    return
  }

  try {
    const response = await apiFetch(`/api/gaps/${gap.id}/dismiss`, {
      method: 'POST'
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        apiErrorMessage(data, 'Unable to dismiss this gap.')
      )
    }

    closeDetails()
    actionMessage.value = 'Gap dismissed.'
    await loadGaps()
  } catch (error) {
    actionMessage.value = error.message
  }
}

const captureProcedure = () => {
  router.push('/capture-procedure')
}

onMounted(loadGaps)
</script>

<template>
  <main class="gaps-page">

    <!-- =========================================
         Page Header
         ========================================= -->
    <section class="page-header">

      <div>
        <p class="eyebrow">Owner Workspace</p>

        <h1>Knowledge Gaps</h1>

        <p>
          Review questions Handoff could not confidently answer
          and identify opportunities to document missing knowledge.
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
      <strong>Loading documentation gaps...</strong>

      <p>
        Handoff is retrieving unanswered employee questions.
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
        <strong>Unable to load documentation gaps</strong>

        <p>
          {{ errorMessage }}
        </p>

        <button
          type="button"
          class="retry-button"
          @click="loadGaps"
        >
          Try Again
        </button>
      </div>
    </section>

    <template v-else>

      <!-- =========================================
           Summary Cards
           ========================================= -->
      <section class="summary">

        <div class="summary-card">
          <span class="summary-label">
            Open Gaps
          </span>

          <strong>
            {{ openGaps.length }}
          </strong>

          <p>
            Need Owner attention
          </p>
        </div>

        <div class="summary-card">
          <span class="summary-label">
            Times Asked
          </span>

          <strong>
            {{ openAskedCount }}
          </strong>

          <p>
            Employee questions still unanswered
          </p>
        </div>

        <div class="summary-card">
          <span class="summary-label">
            Resolved
          </span>

          <strong>
            {{ resolvedCount }}
          </strong>

          <p>
            Answered by newly approved procedures
          </p>
        </div>

      </section>

      <!-- =========================================
           Explanation Banner
           ========================================= -->
      <section class="info-banner">

        <div class="info-icon">
          i
        </div>

        <div>
          <strong>
            Why documentation gaps matter
          </strong>

          <p>
            Handoff is designed to avoid guessing when approved
            knowledge does not contain enough information to answer
            a question. These gaps help Owners identify processes
            that should be documented.
          </p>
        </div>

      </section>

      <!-- =========================================
           Search
           ========================================= -->
      <section class="filters">

        <div class="search-wrapper">

          <label for="gap-search">
            Search questions
          </label>

          <input
            id="gap-search"
            v-model="searchQuery"
            type="search"
            placeholder="Search documentation gaps..."
          />

        </div>

        <div class="search-wrapper">
          <label for="gap-status">
            Show
          </label>

          <select
            id="gap-status"
            v-model="statusFilter"
            class="status-select"
          >
            <option value="open">Open</option>
            <option value="resolved">Resolved</option>
            <option value="dismissed">Dismissed</option>
            <option value="all">All</option>
          </select>
        </div>

        <button
          type="button"
          class="clear-filter-button"
          @click="clearFilters"
        >
          Clear Search
        </button>

      </section>

      <!-- =========================================
           Gap List
           ========================================= -->

      <p
        v-if="actionMessage"
        class="action-message"
      >
        {{ actionMessage }}
      </p>

      <section class="gap-list">

        <div
          v-if="visibleGaps.length === 0"
          class="empty-state"
        >
          <div class="empty-icon">
            ✓
          </div>

          <h2>
            No documentation gaps found
          </h2>

          <p>
            {{
              gaps.length === 0
                ? 'Handoff has not logged any unanswered questions yet.'
                : 'Try changing your search.'
            }}
          </p>
        </div>

        <article
          v-for="gap in visibleGaps"
          :key="gap.id"
          class="gap-card"
        >

          <div class="gap-card-main">

            <div class="question-icon">
              ?
            </div>

            <div class="gap-content">

              <div class="gap-title-row">

                <h2>
                  {{ gap.question }}
                </h2>

                <span
                  class="status"
                  :class="gap.status"
                >
                  {{ statusLabel(gap.status) }}
                </span>

              </div>

              <div class="gap-meta">
                <span class="asked-count">
                  {{ askedLabel(gap.frequency_count) }}
                </span>

                <span>
                  Last asked {{ formatDate(gap.last_asked_at) }}
                </span>

                <span>
                  Closest match: {{ formatSimilarity(gap.similarity) }}
                </span>

                <span
                  v-if="gap.status === 'resolved'"
                  class="resolved-note"
                >
                  Resolved by {{ gap.resolved_by_title || 'a new procedure' }}
                </span>
              </div>

            </div>

          </div>

          <button
            type="button"
            class="view-button"
            @click="viewGap(gap)"
          >
            Review
          </button>

        </article>

      </section>

      <!-- =========================================
           Gap Details Modal
           ========================================= -->
      <div
        v-if="showDetails && selectedGap"
        class="modal-backdrop"
        @click.self="closeDetails"
      >

        <section
          class="gap-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="gap-modal-title"
        >

          <div class="modal-header">

            <div>
              <p class="eyebrow">
                Knowledge Gap
              </p>

              <h2 id="gap-modal-title">
                Review Question
              </h2>
            </div>

            <button
              type="button"
              class="close-button"
              aria-label="Close"
              @click="closeDetails"
            >
              ×
            </button>

          </div>

          <!-- Question -->
          <div class="modal-section">

            <span class="modal-label">
              Employee Question
            </span>

            <div class="question-box">
              {{ selectedGap.question }}
            </div>

          </div>

          <!-- Gap Information -->
          <div class="modal-grid">

            <div class="modal-info">

              <span>
                Status
              </span>

              <strong>
                {{ statusLabel(selectedGap.status) }}
              </strong>

            </div>

            <div class="modal-info">

              <span>
                Closest Match
              </span>

              <strong>
                {{ formatSimilarity(selectedGap.similarity) }}
              </strong>

            </div>

            <div class="modal-info">

              <span>
                Times Asked
              </span>

              <strong>
                {{ selectedGap.frequency_count }}
              </strong>

            </div>

          </div>

          <!-- Recommended Action -->
          <div
            v-if="selectedGap.status === 'open'"
            class="recommendation"
          >

            <div class="recommendation-icon">
              →
            </div>

            <div>

              <strong>
                Recommended action
              </strong>

              <p>
                Consider documenting a procedure that answers
                this question so Handoff can provide employees
                with a grounded answer in the future.
              </p>

            </div>

          </div>

          <!-- Modal Actions -->
          <div class="modal-actions">

            <button
              v-if="selectedGap.status === 'open'"
              type="button"
              class="secondary-button"
              @click="dismissGap(selectedGap)"
            >
              Dismiss
            </button>

            <button
              v-if="selectedGap.status === 'open'"
              type="button"
              class="capture-button"
              @click="captureProcedure"
            >
              Capture a Procedure
            </button>

            <button
              type="button"
              class="secondary-button"
              @click="closeDetails"
            >
              Close
            </button>

          </div>

        </section>

      </div>
    </template>
  </main>
</template>

<style scoped>
/* =========================================
   Page Layout
   ========================================= */

.gaps-page {
  min-height: calc(100vh - 72px);
  padding: 42px 24px 70px;
  background: #f8f6f2;
}

.page-header {
  max-width: 1120px;
  margin: 0 auto 24px;
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
  max-width: 760px;
  margin: 10px 0 0;
  color: #65756f;
  font-size: 15px;
  line-height: 1.6;
}


/* =========================================
   Loading / Error
   ========================================= */

.status-message,
.error-message {
  max-width: 1120px;
  margin: 0 auto 24px;
  padding: 20px;
  border: 1px solid #e2ddd5;
  border-radius: 10px;
  background: white;
}

.status-message strong {
  color: #173c35;
}

.status-message p {
  margin: 5px 0 0;
  color: #75817c;
  font-size: 13px;
}

.error-message {
  display: flex;
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
  margin: 0 auto 20px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.summary-card {
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

.summary-card strong {
  display: block;
  margin-top: 6px;
  color: #173c35;
  font-size: 28px;
}

.summary-card p {
  margin: 4px 0 0;
  color: #7c8580;
  font-size: 12px;
}


/* =========================================
   Information Banner
   ========================================= */

.info-banner {
  max-width: 1120px;
  margin: 0 auto 24px;
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  border: 1px solid #ddd7ce;
  border-radius: 10px;
  background: #f3efe9;
}

.info-icon {
  flex: 0 0 auto;
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #275b4f;
  color: white;
  font-size: 12px;
  font-weight: 700;
}

.info-banner strong {
  display: block;
  color: #31544b;
  font-size: 13px;
}

.info-banner p {
  margin: 4px 0 0;
  color: #6e7974;
  font-size: 12px;
  line-height: 1.5;
}


/* =========================================
   Search
   ========================================= */

.filters {
  max-width: 1120px;
  margin: 0 auto 16px;
  padding: 16px;
  display: grid;
  grid-template-columns: minmax(240px, 1fr) auto;
  align-items: end;
  gap: 12px;
  border: 1px solid #e2ddd5;
  border-radius: 10px;
  background: white;
}

.search-wrapper {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filters label {
  color: #52655d;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.filters input {
  height: 40px;
  box-sizing: border-box;
  border: 1px solid #dcd5cc;
  border-radius: 7px;
  background: #fffdfa;
  color: #29483f;
  padding: 0 11px;
  font: inherit;
  font-size: 13px;
}

.filters input:focus {
  outline: none;
  border-color: #7da99b;
  box-shadow: 0 0 0 3px rgba(39, 91, 79, 0.08);
}

.clear-filter-button {
  height: 40px;
  padding: 0 14px;
  border: 1px solid #d8d0c7;
  border-radius: 7px;
  background: white;
  color: #496058;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.clear-filter-button:hover {
  background: #f7f3ed;
}


/* =========================================
   Gap List
   ========================================= */

.gap-list {
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.gap-card {
  padding: 19px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  border: 1px solid #e2ddd5;
  border-radius: 10px;
  background: white;
  box-shadow: 0 3px 12px rgba(31, 45, 40, 0.04);
}

.gap-card-main {
  min-width: 0;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.question-icon {
  flex: 0 0 auto;
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: #f5e5d9;
  color: #a55d3a;
  font-size: 15px;
  font-weight: 800;
}

.gap-content {
  min-width: 0;
}

.gap-title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 9px;
}

.gap-title-row h2 {
  margin: 0;
  color: #173c35;
  font-size: 15px;
}

.gap-meta {
  margin-top: 7px;
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  color: #7c8580;
  font-size: 11px;
}

.status {
  display: inline-flex;
  align-items: center;
  padding: 5px 9px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
}

.status.open {
  background: #f5e4d9;
  color: #a45b38;
}


/* =========================================
   Review Button
   ========================================= */

.view-button {
  flex: 0 0 auto;
  min-height: 38px;
  padding: 0 14px;
  border: 1px solid #d8d0c7;
  border-radius: 7px;
  background: white;
  color: #275b4f;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.view-button:hover {
  background: #f7f3ed;
}


/* =========================================
   Empty State
   ========================================= */

.empty-state {
  padding: 50px 20px;
  border: 1px dashed #d8d0c7;
  border-radius: 10px;
  background: #fbf9f5;
  text-align: center;
}

.empty-icon {
  width: 42px;
  height: 42px;
  margin: 0 auto 12px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #dcebe5;
  color: #275b4f;
  font-weight: 800;
}

.empty-state h2 {
  margin: 0;
  color: #31544b;
  font-size: 17px;
}

.empty-state p {
  margin: 6px 0 0;
  color: #7c8580;
  font-size: 12px;
}


/* =========================================
   Modal
   ========================================= */

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(22, 39, 34, 0.42);
}

.gap-modal {
  width: min(100%, 600px);
  max-height: calc(100vh - 40px);
  overflow-y: auto;
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

.modal-section {
  margin-top: 22px;
}

.modal-label {
  display: block;
  margin-bottom: 7px;
  color: #75817c;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.question-box {
  padding: 15px;
  border: 1px solid #e0d9d0;
  border-radius: 8px;
  background: #fbf9f5;
  color: #29483f;
  font-size: 14px;
  line-height: 1.5;
}

.modal-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.modal-info {
  padding: 13px;
  border-radius: 8px;
  background: #f7f4ef;
}

.modal-info span {
  display: block;
  margin-bottom: 5px;
  color: #7b847f;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.modal-info strong {
  color: #31544b;
  font-size: 12px;
}


/* =========================================
   Recommendation
   ========================================= */

.recommendation {
  margin-top: 18px;
  padding: 15px;
  display: flex;
  align-items: flex-start;
  gap: 11px;
  border: 1px solid #ddd8cf;
  border-radius: 8px;
  background: #f8f5ef;
}

.recommendation-icon {
  flex: 0 0 auto;
  width: 25px;
  height: 25px;
  display: grid;
  place-items: center;
  border-radius: 6px;
  background: #275b4f;
  color: white;
  font-size: 13px;
  font-weight: 700;
}

.recommendation strong {
  display: block;
  color: #31544b;
  font-size: 13px;
}

.recommendation p {
  margin: 4px 0 0;
  color: #6e7974;
  font-size: 12px;
  line-height: 1.5;
}


/* =========================================
   Modal Actions
   ========================================= */

.modal-actions {
  margin-top: 22px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.secondary-button {
  min-height: 40px;
  padding: 0 16px;
  border: 1px solid #d8d0c7;
  border-radius: 8px;
  background: white;
  color: #496058;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.secondary-button:hover {
  background: #f7f3ed;
}


/* =========================================
   Live Data Notice
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
   Knowledge Gap Statuses and Actions
   ========================================= */

.status.resolved {
  background: #e6f2ee;
  color: #275b4f;
}


.status.dismissed {
  background: #efefef;
  color: #777777;
}


.asked-count {
  color: #d26f3d;
  font-weight: 700;
}


.resolved-note {
  color: #275b4f;
  font-weight: 600;
}


.status-select {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #d8d2c8;
  border-radius: 8px;
  background: #ffffff;
  font-family: inherit;
  font-size: 15px;
}


.action-message {
  margin: 0 0 16px;
  color: #275b4f;
  font-weight: 600;
}


.capture-button {
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

/* =========================================
   Responsive Layout
   ========================================= */

@media (max-width: 760px) {
  .gaps-page {
    padding: 28px 16px 50px;
  }

  .page-header h1 {
    font-size: 29px;
  }

  .summary {
    grid-template-columns: 1fr;
  }

  .filters {
    grid-template-columns: 1fr;
  }

  .gap-card {
    align-items: flex-start;
  }

  .modal-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .gap-card {
    flex-direction: column;
  }

  .view-button {
    width: 100%;
  }

  .modal-actions {
    flex-direction: column;
  }

  .modal-actions button {
    width: 100%;
  }
}
</style>