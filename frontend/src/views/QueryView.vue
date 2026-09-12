<script setup>
import { ref } from 'vue'

/*
 * Prototype question entered by the employee.
 *
 * The completed application will send this value to:
 * POST /api/query
 */
const question = ref('')

/*
 * Tracks whether the prototype is currently showing a response.
 */
const hasAsked = ref(false)

/*
 * Prototype response state.
 *
 * Possible values:
 * - answered
 * - not_documented
 */
const responseState = ref('')

/*
 * Prevents the button from being submitted repeatedly.
 */
const isLoading = ref(false)

/*
 * Holds the response displayed to the user.
 */
const answer = ref('')

/*
 * Procedure used as the source for the prototype answer.
 *
 * The completed backend will return grounded source information
 * from the approved knowledge base.
 */
const sourceProcedure = ref('')

/*
 * Documentation gap message shown when Handoff cannot
 * confidently answer a question.
 */
const gapMessage = ref('')

/*
 * Submit a question to Handoff.
 *
 * This currently uses prototype responses so the frontend can
 * be demonstrated before the FastAPI backend is connected.
 *
 * Future implementation:
 *
 * POST /api/query
 *
 * Request:
 * {
 *   "question": "..."
 * }
 *
 * Response:
 * {
 *   "status": "answered",
 *   "answer": "...",
 *   "sources": [...]
 * }
 *
 * OR:
 *
 * {
 *   "status": "not_documented",
 *   "message": "...",
 *   "gap_id": "..."
 * }
 */
const askHandoff = () => {
  if (!question.value.trim()) {
    return
  }

  isLoading.value = true
  hasAsked.value = false
  responseState.value = ''
  answer.value = ''
  sourceProcedure.value = ''
  gapMessage.value = ''

  /*
   * Temporary delay to make the prototype feel like a real
   * request is being processed.
   */
  setTimeout(() => {
    const normalizedQuestion = question.value.toLowerCase()

    /*
     * If the question relates to closing the store, demonstrate
     * an answer grounded in the newly approved Store Closed
     * procedure.
     */
    if (
      normalizedQuestion.includes('close') ||
      normalizedQuestion.includes('closing') ||
      normalizedQuestion.includes('store closed')
    ) {
      responseState.value = 'answered'

      answer.value =
        'Before closing the store, verify that all customers have been assisted, complete the required closing tasks, secure the store, and confirm that the closing process is complete.'

      sourceProcedure.value = 'Store Closed'
    } else {
      /*
       * For questions that are not represented by the prototype
       * knowledge base, demonstrate the required abstention state.
       */
      responseState.value = 'not_documented'

      gapMessage.value =
        'I could not find an approved procedure that confidently answers this question. The information may not be documented yet.'
    }

    hasAsked.value = true
    isLoading.value = false
  }, 700)
}

/*
 * Clear the current question and response.
 */
const clearQuestion = () => {
  question.value = ''
  hasAsked.value = false
  responseState.value = ''
  answer.value = ''
  sourceProcedure.value = ''
  gapMessage.value = ''
}

/*
 * Put an example question into the input so the user can
 * quickly demonstrate the Ask Handoff workflow.
 */
const useExample = () => {
  question.value = 'What should I do when closing the store?'
}
</script>

<template>
  <main class="query-page">

    <!-- =========================================
         Page Header
         ========================================= -->
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


    <!-- =========================================
         Question Card
         ========================================= -->
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


    <!-- =========================================
         Answered State
         ========================================= -->
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


      <!-- =========================================
           Source Procedure
           ========================================= -->
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


    <!-- =========================================
         Not Documented State
         ========================================= -->
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
            The completed application will record this question
            through the documentation gap service.
          </p>
        </div>

      </div>

    </section>


    <!-- =========================================
         How Ask Handoff Works
         ========================================= -->
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


    <!-- =========================================
         Prototype Notice
         ========================================= -->
    <section class="prototype-note">

      <strong>
        Prototype note
      </strong>

      <p>
        The response shown here is currently simulated for
        frontend demonstration. The completed application will
        connect this interface to the Handoff API using
        POST /api/query.
      </p>

    </section>

  </main>
</template>

<style scoped>
/* =========================================
   Page Layout
   ========================================= */

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


/* =========================================
   Question Card
   ========================================= */

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


/* =========================================
   Question Actions
   ========================================= */

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


/* =========================================
   Response Cards
   ========================================= */

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


/* =========================================
   Answer
   ========================================= */

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


/* =========================================
   Source
   ========================================= */

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


/* =========================================
   Grounding Note
   ========================================= */

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


/* =========================================
   Documentation Gap
   ========================================= */

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


/* =========================================
   How It Works
   ========================================= */

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


/* =========================================
   Prototype Notice
   ========================================= */

.prototype-note {
  max-width: 1000px;
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
