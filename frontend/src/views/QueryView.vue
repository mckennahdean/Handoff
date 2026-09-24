<script setup>
import { ref } from 'vue'
import { apiFetch } from '../api.js'

const question = ref('')
const hasAsked = ref(false)
const responseState = ref('')
const isLoading = ref(false)
const answer = ref('')
const sourceProcedure = ref('')
const gapMessage = ref('')

const askHandoff = async () => {
  if (!question.value.trim()) {
    return
  }

  isLoading.value = true
  hasAsked.value = false
  responseState.value = ''
  answer.value = ''
  sourceProcedure.value = ''
  gapMessage.value = ''

  try {
    const response = await apiFetch('/api/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        question: question.value.trim()
      })
    })

    if (!response.ok) {
      throw new Error('Unable to get an answer from Handoff.')
    }

    const data = await response.json()

    responseState.value = data.status

    if (data.status === 'answered') {
      answer.value = data.answer
      sourceProcedure.value = data.source_procedure
    } else if (data.status === 'not_documented') {
      gapMessage.value =
        data.message ||
        'This information is not documented in the approved procedures.'
    }

    hasAsked.value = true
  } catch (error) {
    responseState.value = 'not_documented'
    gapMessage.value =
      'Handoff could not connect to the backend. Please try again.'

    hasAsked.value = true
    console.error(error)
  } finally {
    isLoading.value = false
  }
}

const clearQuestion = () => {
  question.value = ''
  hasAsked.value = false
  responseState.value = ''
  answer.value = ''
  sourceProcedure.value = ''
  gapMessage.value = ''
}

const useExample = () => {
  question.value = 'What should I do when closing the store?'
}
</script>

<template>
  <main class="query-page">

    <section class="page-header">
      <div>
        <p class="eyebrow">Handoff Knowledge Assistant</p>

        <h1>Ask Handoff</h1>

        <p>
          Ask a question about how something is done and get
          an answer grounded in your organization's approved
          procedures.
        </p>
      </div>
    </section>

    <section class="question-card">
      <div class="question-heading">

        <div class="assistant-icon">
          H
        </div>

        <div>
          <h2>
            What do you need to know?
          </h2>

          <p>
            Ask about a process, task, or procedure.
          </p>
        </div>

      </div>

      <form @submit.prevent="askHandoff">

        <label for="question">
          Your question
        </label>

        <textarea
          id="question"
          v-model="question"
          rows="5"
          placeholder="For example: What should I do when closing the store?"
          :disabled="isLoading"
        ></textarea>

        <div class="question-actions">

          <button
            type="button"
            class="example-button"
            @click="useExample"
            :disabled="isLoading"
          >
            Use Example
          </button>

          <div class="primary-actions">

            <button
              v-if="question"
              type="button"
              class="clear-button"
              @click="clearQuestion"
              :disabled="isLoading"
            >
              Clear
            </button>

            <button
              type="submit"
              class="ask-button"
              :disabled="!question.trim() || isLoading"
            >
              <span v-if="isLoading">
                Thinking...
              </span>

              <span v-else>
                Ask Handoff
              </span>
            </button>

          </div>

        </div>

      </form>
    </section>

    <section
      v-if="hasAsked && responseState === 'answered'"
      class="response-card answered-card"
    >

      <div class="response-header">

        <div class="response-icon">
          ✓
        </div>

        <div>
          <p class="response-label">
            Handoff Answer
          </p>

          <h2>
            Here's what I found
          </h2>
        </div>

      </div>

      <div class="answer-content">
        <p>
          {{ answer }}
        </p>
      </div>

      <div class="source-section">

        <span class="source-label">
          Based on approved procedure
        </span>

        <div class="source-card">

          <div class="source-icon">
            ✓
          </div>

          <div>
            <strong>
              {{ sourceProcedure }}
            </strong>

            <p>
              This procedure has been reviewed and approved
              by your organization's Owner.
            </p>
          </div>

        </div>

      </div>

      <div class="grounding-note">

        <span>i</span>

        <p>
          Handoff answers questions using approved organizational
          knowledge rather than guessing when information is missing.
        </p>

      </div>

    </section>

    <section
      v-if="hasAsked && responseState === 'not_documented'"
      class="response-card gap-card"
    >

      <div class="response-header">

        <div class="gap-icon">
          !
        </div>

        <div>
          <p class="response-label">
            Information Not Documented
          </p>

          <h2>
            Handoff couldn't confidently answer that.
          </h2>
        </div>

      </div>

      <div class="gap-content">

        <p>
          {{ gapMessage }}
        </p>

        <p>
          Instead of guessing, Handoff has identified this as
          a potential documentation gap for the Owner to review.
        </p>

      </div>

      <div class="gap-status">

        <div class="gap-status-icon">
          ✓
        </div>

        <div>
          <strong>
            Documentation gap identified
          </strong>

          <p>
            This question has been recorded through the
            documentation gap service.
          </p>
        </div>

      </div>

    </section>

    <section class="how-it-works">

      <div class="section-heading">

        <p class="eyebrow">
          Knowledge Grounding
        </p>

        <h2>
          How Handoff works
        </h2>

      </div>

      <div class="process-grid">

        <article class="process-card">

          <span class="process-number">
            1
          </span>

          <h3>
            Ask
          </h3>

          <p>
            Ask Handoff a question about a workplace process
            or task.
          </p>

        </article>

        <article class="process-card">

          <span class="process-number">
            2
          </span>

          <h3>
            Ground
          </h3>

          <p>
            Handoff searches approved organizational procedures
            for relevant knowledge.
          </p>

        </article>

        <article class="process-card">

          <span class="process-number">
            3
          </span>

          <h3>
            Answer or Abstain
          </h3>

          <p>
            Handoff provides a grounded answer or identifies
            a documentation gap when the information is not
            sufficiently documented.
          </p>

        </article>

      </div>

    </section>

  </main>
</template>

<style scoped>
.query-page {
  min-height: calc(100vh - 72px);
  padding: 42px 24px 70px;
  background: #f8f6f2;
}

.page-header {
  max-width: 1000px;
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
  max-width: 720px;
  margin: 10px 0 0;
  color: #65756f;
  font-size: 15px;
  line-height: 1.6;
}

.question-card {
  max-width: 1000px;
  margin: 0 auto;
  padding: 28px;
  border: 1px solid #e2ddd5;
  border-radius: 14px;
  background: white;
  box-shadow: 0 4px 16px rgba(31, 45, 40, 0.05);
}

.question-heading {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 22px;
}

.assistant-icon {
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: #275b4f;
  color: white;
  font-size: 20px;
  font-weight: 800;
}

.question-heading h2 {
  margin: 0;
  color: #173c35;
  font-size: 20px;
}

.question-heading p {
  margin: 4px 0 0;
  color: #75817c;
  font-size: 13px;
}

.question-card label {
  display: block;
  margin-bottom: 8px;
  color: #28473f;
  font-size: 13px;
  font-weight: 700;
}

.question-card textarea {
  width: 100%;
  box-sizing: border-box;
  resize: vertical;
  border: 1px solid #dcd5cc;
  border-radius: 9px;
  padding: 13px;
  background: #fffdfa;
  color: #183d36;
  font: inherit;
  font-size: 14px;
  line-height: 1.5;
}

.question-card textarea::placeholder {
  color: #a09d96;
}

.question-card textarea:focus {
  outline: none;
  border-color: #7da99b;
  box-shadow: 0 0 0 3px rgba(39, 91, 79, 0.08);
}

.question-card textarea:disabled {
  opacity: 0.7;
}

.question-actions {
  margin-top: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.primary-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.example-button,
.clear-button,
.ask-button {
  min-height: 40px;
  padding: 0 15px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.example-button,
.clear-button {
  border: 1px solid #d8d0c7;
  background: white;
  color: #496058;
}

.example-button:hover,
.clear-button:hover {
  background: #f7f3ed;
}

.ask-button {
  border: 1px solid #275b4f;
  background: #275b4f;
  color: white;
}

.ask-button:hover {
  background: #204d43;
}

.ask-button:disabled,
.example-button:disabled,
.clear-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.response-card {
  max-width: 1000px;
  margin: 20px auto 0;
  padding: 26px;
  border: 1px solid #e2ddd5;
  border-radius: 14px;
  background: white;
  box-shadow: 0 4px 16px rgba(31, 45, 40, 0.05);
}

.answered-card {
  border-color: #c9ddd5;
}

.gap-card {
  border-color: #e2d5c9;
}

.response-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.response-icon,
.gap-icon {
  flex: 0 0 auto;
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 800;
}

.response-icon {
  background: #dcebe5;
  color: #275b4f;
}

.gap-icon {
  background: #f5e4d9;
  color: #a45b38;
}

.response-label {
  margin: 0 0 4px;
  color: #d26f3d;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.response-header h2 {
  margin: 0;
  color: #173c35;
  font-size: 21px;
}

.answer-content {
  margin: 20px 0;
  padding: 20px;
  border-radius: 10px;
  background: #f7faf8;
}

.answer-content p {
  margin: 0;
  color: #29483f;
  font-size: 15px;
  line-height: 1.7;
}

.source-section {
  margin-top: 20px;
}

.source-label {
  display: block;
  margin-bottom: 8px;
  color: #75817c;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.source-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border: 1px solid #dce5e0;
  border-radius: 9px;
  background: #fbfcfa;
}

.source-icon {
  flex: 0 0 auto;
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 7px;
  background: #275b4f;
  color: white;
  font-size: 12px;
  font-weight: 700;
}

.source-card strong {
  display: block;
  color: #275b4f;
  font-size: 13px;
}

.source-card p {
  margin: 3px 0 0;
  color: #75817c;
  font-size: 12px;
}

.grounding-note {
  margin-top: 18px;
  padding: 13px;
  display: flex;
  align-items: flex-start;
  gap: 9px;
  border-radius: 8px;
  background: #f5f1eb;
}

.grounding-note span {
  flex: 0 0 auto;
  width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #e3ddd3;
  color: #6d6961;
  font-size: 11px;
  font-weight: 700;
}

.grounding-note p {
  margin: 0;
  color: #716f69;
  font-size: 12px;
  line-height: 1.5;
}

.gap-content {
  margin: 20px 0;
  padding: 18px;
  border-radius: 9px;
  background: #fbf5ef;
}

.gap-content p {
  margin: 0;
  color: #5e554e;
  font-size: 14px;
  line-height: 1.6;
}

.gap-content p + p {
  margin-top: 10px;
}

.gap-status {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 15px;
  border: 1px solid #e4ddd4;
  border-radius: 9px;
  background: #fffdfa;
}

.gap-status-icon {
  flex: 0 0 auto;
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 7px;
  background: #f0e6dc;
  color: #9c5d3e;
  font-size: 12px;
  font-weight: 700;
}

.gap-status strong {
  display: block;
  color: #6b5548;
  font-size: 13px;
}

.gap-status p {
  margin: 3px 0 0;
  color: #80766e;
  font-size: 12px;
}

.how-it-works {
  max-width: 1000px;
  margin: 32px auto 0;
}

.section-heading {
  margin-bottom: 14px;
}

.section-heading h2 {
  margin: 0;
  color: #173c35;
  font-size: 22px;
}

.section-heading .eyebrow {
  margin-bottom: 5px;
}

.process-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.process-card {
  padding: 20px;
  border: 1px solid #e2ddd5;
  border-radius: 10px;
  background: white;
}

.process-number {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #275b4f;
  color: white;
  font-size: 12px;
  font-weight: 700;
}

.process-card h3 {
  margin: 14px 0 6px;
  color: #173c35;
  font-size: 16px;
}

.process-card p {
  margin: 0;
  color: #707d78;
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 760px) {
  .query-page {
    padding: 28px 16px 50px;
  }

  .page-header h1 {
    font-size: 29px;
  }

  .question-card,
  .response-card {
    padding: 20px;
  }

  .process-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .question-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .primary-actions {
    width: 100%;
  }

  .example-button,
  .clear-button,
  .ask-button {
    flex: 1;
  }

  .response-header h2 {
    font-size: 18px;
  }
}
</style>