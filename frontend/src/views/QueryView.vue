<template>
  <main class="query">
    <!-- Page heading -->
    <section class="page-header">
      <p class="eyebrow">Employee Workspace</p>
      <h1>Ask Handoff</h1>
      <p>
        Ask a question about a business procedure and receive an answer based
        on approved documentation.
      </p>
    </section>

    <!-- Employee question form -->
    <section class="query-card">
      <div class="card-heading">
        <div class="question-icon">?</div>

        <div>
          <h2>What do you need to know?</h2>
          <p>
            Handoff searches approved procedures to find the most relevant
            answer.
          </p>
        </div>
      </div>

      <form @submit.prevent="submitQuery" class="query-form">
        <label for="question">Your question</label>

        <textarea
          id="question"
          v-model="question"
          placeholder="For example: What should I do if a customer does not have a receipt?"
          rows="5"
          required
        ></textarea>

        <div class="form-footer">
          <span class="helper-text">
            Answers are based on approved procedures.
          </span>

          <button type="submit" :disabled="loading">
            {{ loading ? 'Searching...' : 'Ask Handoff' }}
          </button>
        </div>
      </form>
    </section>

    <!-- Query result -->
    <section v-if="response" class="response-section">
      <!-- Answered response -->
      <div v-if="response.status === 'answered'" class="answer-card">
        <div class="response-heading">
          <span class="response-badge answered">Answered</span>
          <h2>Here's what you need to know</h2>
        </div>

        <p class="answer-text">
          {{ response.answer }}
        </p>

        <!-- Source information -->
        <div class="source">
          <div class="source-heading">
            <span>Source Procedure</span>
          </div>

          <div class="source-details">
            <div>
              <span>Procedure</span>
              <strong>{{ response.source_procedure }}</strong>
            </div>

            <div>
              <span>Version</span>
              <strong>{{ response.version }}</strong>
            </div>

            <div>
              <span>Last Confirmed</span>
              <strong>{{ response.last_confirmed }}</strong>
            </div>
          </div>
        </div>
      </div>

      <!-- Documentation gap response -->
      <div
        v-else-if="response.status === 'not_documented'"
        class="not-documented-card"
      >
        <div class="response-heading">
          <span class="response-badge not-documented">
            Not Documented
          </span>

          <h2>We couldn't find an approved answer</h2>
        </div>

        <p class="answer-text">
          {{ response.message }}
        </p>

        <div class="gap-notice">
          <strong>Documentation gap recorded</strong>
          <p>
            Your question has been logged so the owner can review whether this
            procedure should be added to the documentation.
          </p>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'

const question = ref('')
const response = ref(null)
const loading = ref(false)

// Temporary query responses used while the FastAPI endpoint is being developed.
// These will later be replaced with a request to POST /api/query.
const mockAnsweredResponse = {
  status: 'answered',
  answer:
    'Ask the customer for the receipt and verify that the purchase is eligible for return.',
  source_procedure: 'Customer Returns',
  procedure_id: 1,
  version: 1,
  last_confirmed: 'August 30, 2026'
}

const mockNotDocumentedResponse = {
  status: 'not_documented',
  answer: null,
  source_procedure: null,
  procedure_id: null,
  version: null,
  last_confirmed: null,
  message: 'This procedure is not currently documented.'
}

// Temporary query handler.
// This will later send the question to POST /api/query.
function submitQuery() {
  loading.value = true
  response.value = null

  setTimeout(() => {
    // Use the question to demonstrate both possible API responses.
    if (question.value.toLowerCase().includes('receipt')) {
      response.value = mockAnsweredResponse
    } else {
      response.value = mockNotDocumentedResponse
    }

    loading.value = false
  }, 500)
}
</script>

<style scoped>
.query {
  width: min(900px, calc(100% - 40px));
  margin: 0 auto;
  padding: 55px 0 70px;
}

.page-header {
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
  line-height: 1.6;
}

/* Main employee question card */
.query-card {
  padding: 30px;
  background: #ffffff;
  border: 1px solid #e4ddd7;
  border-radius: 14px;
  box-shadow: 0 4px 14px rgba(60, 45, 35, 0.06);
}

.card-heading {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  margin-bottom: 25px;
}

.question-icon {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: #f3e3d8;
  color: #914923;
  font-size: 20px;
  font-weight: 800;
}

.card-heading h2 {
  margin: 0 0 5px;
  color: #263238;
  font-size: 21px;
}

.card-heading p {
  margin: 0;
  color: #68747a;
  font-size: 14px;
  line-height: 1.5;
}

/* Question form */
.query-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.query-form label {
  color: #39484e;
  font-size: 14px;
  font-weight: 600;
}

textarea {
  width: 100%;
  padding: 14px;
  color: #263238;
  background: #ffffff;
  border: 1px solid #d8d0ca;
  border-radius: 8px;
  font-size: 16px;
  line-height: 1.5;
  resize: vertical;
  outline: none;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

textarea:focus {
  border-color: #b65f32;
  box-shadow: 0 0 0 3px #f3e3d8;
}

textarea::placeholder {
  color: #9aa3a7;
}

.form-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 15px;
  margin-top: 5px;
}

.helper-text {
  color: #68747a;
  font-size: 13px;
}

/* Query response area */
.response-section {
  margin-top: 30px;
}

.answer-card,
.not-documented-card {
  padding: 30px;
  background: #ffffff;
  border: 1px solid #e4ddd7;
  border-radius: 14px;
  box-shadow: 0 4px 14px rgba(60, 45, 35, 0.06);
}

.response-heading {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.response-heading h2 {
  margin: 0;
  color: #263238;
  font-size: 21px;
}

/* Response status badges */
.response-badge {
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.response-badge.answered {
  background: #e7f1eb;
  color: #35634a;
}

.response-badge.not-documented {
  background: #f3e3d8;
  color: #914923;
}

.answer-text {
  margin: 0;
  color: #39484e;
  font-size: 17px;
  line-height: 1.7;
}

/* Source procedure information */
.source {
  margin-top: 28px;
  padding-top: 22px;
  border-top: 1px solid #e4ddd7;
}

.source-heading {
  margin-bottom: 15px;
  color: #68747a;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.source-details {
  display: grid;
  grid-template-columns: 2fr 1fr 1.5fr;
  gap: 20px;
}

.source-details div {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.source-details span {
  color: #68747a;
  font-size: 12px;
}

.source-details strong {
  color: #263238;
  font-size: 14px;
}

/* Documentation gap notification */
.gap-notice {
  margin-top: 25px;
  padding: 18px 20px;
  background: #f3e3d8;
  border-radius: 10px;
}

.gap-notice strong {
  color: #914923;
  font-size: 14px;
}

.gap-notice p {
  margin: 6px 0 0;
  color: #80533c;
  font-size: 14px;
  line-height: 1.5;
}

@media (max-width: 700px) {
  .query {
    width: min(100% - 30px, 900px);
    padding: 40px 0 55px;
  }

  .query-card,
  .answer-card,
  .not-documented-card {
    padding: 22px;
  }

  .form-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .form-footer button {
    width: 100%;
  }

  .source-details {
    grid-template-columns: 1fr;
    gap: 15px;
  }
}
</style>
