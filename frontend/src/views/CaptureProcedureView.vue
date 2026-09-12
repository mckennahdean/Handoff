<script setup>
import { ref, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// =========================================
// Procedure Information
// =========================================

// Stores the title entered by the Owner.
const title = ref('')

// Stores the knowledge entered when using manual entry.
const manualNotes = ref('')

// The selected capture method.
const captureMethod = ref('record')

// =========================================
// Audio Recording
// =========================================

// Frontend prototype recording state.
const isRecording = ref(false)
const recordingSeconds = ref(0)

// Stores the selected uploaded audio file.
const selectedFile = ref(null)

// Timer used by the prototype recording experience.
let recordingTimer = null

// =========================================
// Submission State
// =========================================

const message = ref('')
const isSubmitting = ref(false)
const submissionError = ref(false)


// =========================================
// Recording Functions
// =========================================

// Start the prototype recording timer.
const startRecording = () => {
  if (isRecording.value) {
    return
  }

  isRecording.value = true
  recordingSeconds.value = 0

  recordingTimer = setInterval(() => {
    recordingSeconds.value += 1
  }, 1000)
}


// Stop the prototype recording timer.
const stopRecording = () => {
  isRecording.value = false

  if (recordingTimer) {
    clearInterval(recordingTimer)
    recordingTimer = null
  }
}


// Format the recording time as MM:SS.
const formattedTime = () => {
  const minutes = Math.floor(recordingSeconds.value / 60)
  const seconds = recordingSeconds.value % 60

  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}


// =========================================
// File Upload
// =========================================

// Save the selected audio file for the prototype.
const handleFileUpload = (event) => {
  const file = event.target.files[0]

  if (file) {
    selectedFile.value = file
    message.value = ''
    submissionError.value = false
  }
}


// =========================================
// Capture Method
// =========================================

// Change the selected capture method and
// clear any previous validation message.
const selectMethod = (method) => {
  captureMethod.value = method
  message.value = ''
  submissionError.value = false
}


// =========================================
// Validation
// =========================================

// Make sure the Owner has provided everything
// required for the selected capture method.
const validateForm = () => {
  if (!title.value.trim()) {
    return 'Please enter a procedure title before continuing.'
  }

  if (captureMethod.value === 'record') {
    if (recordingSeconds.value === 0) {
      return 'Please record some audio before continuing.'
    }
  }

  if (captureMethod.value === 'upload') {
    if (!selectedFile.value) {
      return 'Please select an audio file to upload.'
    }
  }

  if (captureMethod.value === 'manual') {
    if (!manualNotes.value.trim()) {
      return 'Please enter some procedure knowledge before continuing.'
    }
  }

  return ''
}


// =========================================
// Submit Procedure
// =========================================

// Submit the captured knowledge for AI structuring.
const submitProcedure = () => {
  const validationMessage = validateForm()

  if (validationMessage) {
    message.value = validationMessage
    submissionError.value = true
    return
  }

  isSubmitting.value = true
  message.value = ''
  submissionError.value = false

  // Save temporary prototype data so the next
  // screen can display the captured procedure.
  const pendingProcedure = {
    title: title.value.trim(),
    captureMethod: captureMethod.value,
    manualNotes: manualNotes.value.trim(),
    audioFileName: selectedFile.value
      ? selectedFile.value.name
      : null,
    recordingDuration: recordingSeconds.value,
    status: 'Pending Review'
  }

  localStorage.setItem(
    'pendingProcedure',
    JSON.stringify(pendingProcedure)
  )

  // Simulate the AI structuring process.
  setTimeout(() => {
    isSubmitting.value = false

    message.value =
      'Knowledge captured successfully. Handoff is preparing the procedure for Owner review.'

    // Move into the existing approval workflow.
    setTimeout(() => {
      router.push('/procedure-review')
    }, 1200)
  }, 1000)
}


// =========================================
// Cancel
// =========================================

// Return to the Procedures page without submitting.
const cancel = () => {
  if (recordingTimer) {
    clearInterval(recordingTimer)
    recordingTimer = null
  }

  router.push('/procedures')
}


// Clean up the recording timer if the
// component is removed from the page.
onBeforeUnmount(() => {
  if (recordingTimer) {
    clearInterval(recordingTimer)
  }
})
</script>


<template>
  <main class="capture-page">

    <!-- =========================================
         Page Header
         ========================================= -->
    <section class="page-header">
      <div>
        <p class="eyebrow">
          Owner Workspace
        </p>

        <h1>
          Capture a Procedure
        </h1>

        <p class="intro">
          Capture the knowledge behind a business process so Handoff
          can structure it for review and approval.
        </p>
      </div>
    </section>


    <!-- =========================================
         Workflow Indicator
         ========================================= -->
    <section class="workflow">

      <div class="workflow-step active">
        <span class="step-number">
          1
        </span>

        <div>
          <strong>Capture</strong>
          <span>Provide your knowledge</span>
        </div>
      </div>

      <div class="workflow-line"></div>

      <div class="workflow-step">
        <span class="step-number">
          2
        </span>

        <div>
          <strong>Structure</strong>
          <span>AI organizes the procedure</span>
        </div>
      </div>

      <div class="workflow-line"></div>

      <div class="workflow-step">
        <span class="step-number">
          3
        </span>

        <div>
          <strong>Review</strong>
          <span>Owner approves the procedure</span>
        </div>
      </div>

    </section>


    <!-- =========================================
         Capture Form
         ========================================= -->
    <section class="capture-card">

      <div class="section-heading">
        <div>
          <p class="section-label">
            Procedure Information
          </p>

          <h2>
            What knowledge are you capturing?
          </h2>

          <p>
            Give the procedure a clear name that employees will
            recognize later.
          </p>
        </div>
      </div>


      <!-- =========================================
           Procedure Title
           ========================================= -->
      <div class="form-group">

        <label for="procedure-title">
          Procedure Title
        </label>

        <input
          id="procedure-title"
          v-model="title"
          type="text"
          placeholder="Example: Customer Returns"
        />

        <span class="field-help">
          Use a short, descriptive name for this procedure.
        </span>

      </div>


      <!-- =========================================
           Capture Method
           ========================================= -->
      <div class="method-section">

        <div class="method-heading">

          <label>
            How would you like to capture the knowledge?
          </label>

          <p>
            Choose the option that works best for documenting
            the procedure.
          </p>

        </div>


        <div class="method-options">

          <!-- Record Audio -->
          <button
            type="button"
            class="method-option"
            :class="{
              selected: captureMethod === 'record'
            }"
            @click="selectMethod('record')"
          >

            <span class="method-icon">
              🎙️
            </span>

            <span class="method-content">
              <strong>
                Record Audio
              </strong>

              <span>
                Explain the procedure in your own words.
              </span>
            </span>

            <span
              v-if="captureMethod === 'record'"
              class="selected-check"
            >
              ✓
            </span>

          </button>


          <!-- Upload Audio -->
          <button
            type="button"
            class="method-option"
            :class="{
              selected: captureMethod === 'upload'
            }"
            @click="selectMethod('upload')"
          >

            <span class="method-icon">
              📁
            </span>

            <span class="method-content">
              <strong>
                Upload Audio
              </strong>

              <span>
                Use an existing recording of the procedure.
              </span>
            </span>

            <span
              v-if="captureMethod === 'upload'"
              class="selected-check"
            >
              ✓
            </span>

          </button>


          <!-- Enter Manually -->
          <button
            type="button"
            class="method-option"
            :class="{
              selected: captureMethod === 'manual'
            }"
            @click="selectMethod('manual')"
          >

            <span class="method-icon">
              ✍️
            </span>

            <span class="method-content">
              <strong>
                Enter Manually
              </strong>

              <span>
                Provide the procedure knowledge as written notes.
              </span>
            </span>

            <span
              v-if="captureMethod === 'manual'"
              class="selected-check"
            >
              ✓
            </span>

          </button>

        </div>
      </div>


      <!-- =========================================
           Record Audio
           ========================================= -->
      <div
        v-if="captureMethod === 'record'"
        class="capture-area"
      >

        <div class="capture-icon">
          🎙️
        </div>

        <h3>
          {{
            isRecording
              ? 'Recording procedure...'
              : 'Record your procedure'
          }}
        </h3>

        <p>
          Explain the process step-by-step as if you were
          teaching it to a new employee.
        </p>


        <!-- Recording timer -->
        <div
          v-if="isRecording"
          class="recording-status"
        >
          <span class="recording-dot"></span>

          <span>
            {{ formattedTime() }}
          </span>
        </div>


        <!-- Start recording -->
        <button
          v-if="!isRecording && recordingSeconds === 0"
          type="button"
          class="primary-capture-button"
          @click="startRecording"
        >
          Start Recording
        </button>


        <!-- Stop recording -->
        <button
          v-if="isRecording"
          type="button"
          class="stop-button"
          @click="stopRecording"
        >
          Stop Recording
        </button>


        <!-- Recording captured state -->
        <div
          v-if="recordingSeconds > 0 && !isRecording"
          class="recording-complete"
        >
          <span class="complete-icon">
            ✓
          </span>

          <div>
            <strong>
              Recording captured
            </strong>

            <span>
              Duration: {{ formattedTime() }}
            </span>
          </div>

          <button
            type="button"
            class="record-again-button"
            @click="startRecording"
          >
            Record Again
          </button>
        </div>

      </div>


      <!-- =========================================
           Upload Audio
           ========================================= -->
      <div
        v-if="captureMethod === 'upload'"
        class="capture-area"
      >

        <div class="capture-icon">
          📁
        </div>

        <h3>
          Upload an audio recording
        </h3>

        <p>
          Select an audio recording containing the procedure
          you want Handoff to structure.
        </p>


        <label
          for="audio-upload"
          class="upload-button"
        >
          Choose Audio File
        </label>

        <input
          id="audio-upload"
          class="hidden-file-input"
          type="file"
          accept="audio/*"
          @change="handleFileUpload"
        />


        <!-- Selected file -->
        <div
          v-if="selectedFile"
          class="selected-file"
        >
          <span class="file-check">
            ✓
          </span>

          <div>
            <strong>
              {{ selectedFile.name }}
            </strong>

            <span>
              Ready for submission
            </span>
          </div>
        </div>

      </div>


      <!-- =========================================
           Manual Entry
           ========================================= -->
      <div
        v-if="captureMethod === 'manual'"
        class="capture-area manual-area"
      >

        <div class="capture-icon">
          ✍️
        </div>

        <h3>
          Enter procedure knowledge
        </h3>

        <p>
          Write the information you want Handoff to organize
          into a structured procedure.
        </p>

        <textarea
          v-model="manualNotes"
          placeholder="Describe the procedure, important steps, warnings, exceptions, or anything an employee should know..."
        ></textarea>

        <span class="character-help">
          Include as much detail as possible. Handoff will
          organize the information during the structuring step.
        </span>

      </div>


      <!-- =========================================
           Prototype Information
           ========================================= -->
      <div class="prototype-note">

        <div class="note-icon">
          i
        </div>

        <div>
          <strong>
            How this works in the Handoff system
          </strong>

          <p>
            The captured knowledge will eventually be sent to
            Handoff's AI structuring service. The AI will organize
            the information into a draft procedure, which must be
            reviewed and approved by the Owner before employees
            can use it.
          </p>
        </div>

      </div>


      <!-- =========================================
           Status Message
           ========================================= -->
      <div
        v-if="message"
        class="message"
        :class="{ error: submissionError }"
      >
        {{ message }}
      </div>


      <!-- =========================================
           Form Actions
           ========================================= -->
      <div class="form-actions">

        <button
          type="button"
          class="cancel-button"
          @click="cancel"
        >
          Cancel
        </button>

        <button
          type="button"
          class="submit-button"
          :disabled="isSubmitting"
          @click="submitProcedure"
        >
          <span v-if="isSubmitting">
            Structuring Knowledge...
          </span>

          <span v-else>
            Submit for AI Structuring →
          </span>
        </button>

      </div>

    </section>

  </main>
</template>


<style scoped>
/* =========================================
   Overall Capture Page
   ========================================= */

.capture-page {
  width: min(1000px, calc(100% - 40px));
  margin: 0 auto;
  padding: 55px 0 75px;
}


/* =========================================
   Page Header
   ========================================= */

.page-header {
  margin-bottom: 32px;
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

.intro {
  max-width: 720px;
  margin: 0;
  color: #68747a;
  font-size: 17px;
  line-height: 1.5;
}


/* =========================================
   Workflow Indicator
   ========================================= */

.workflow {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
  padding: 18px 22px;
  background: #ffffff;
  border: 1px solid #e4ddd7;
  border-radius: 12px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #8a9296;
}

.workflow-step.active {
  color: #275b4f;
}

.workflow-step > div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.workflow-step strong {
  font-size: 13px;
}

.workflow-step span:last-child {
  font-size: 11px;
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #eee9e3;
  color: #68747a;
  font-size: 12px;
  font-weight: 700;
}

.workflow-step.active .step-number {
  background: #275b4f;
  color: #ffffff;
}

.workflow-line {
  flex: 1;
  height: 1px;
  margin: 0 18px;
  background: #ded7d0;
}


/* =========================================
   Main Capture Card
   ========================================= */

.capture-card {
  padding: 34px;
  background: #ffffff;
  border: 1px solid #e4ddd7;
  border-radius: 14px;
  box-shadow: 0 3px 12px rgba(60, 45, 35, 0.05);
}


/* =========================================
   Section Heading
   ========================================= */

.section-heading {
  margin-bottom: 28px;
}

.section-label {
  margin: 0 0 6px;
  color: #b65f32;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.section-heading h2 {
  margin: 0 0 7px;
  color: #263238;
  font-size: 24px;
}

.section-heading p {
  margin: 0;
  color: #68747a;
  font-size: 14px;
}


/* =========================================
   Form Fields
   ========================================= */

.form-group {
  margin-bottom: 34px;
}

.form-group label,
.method-heading label {
  display: block;
  margin-bottom: 8px;
  color: #263238;
  font-size: 14px;
  font-weight: 700;
}

.form-group input {
  width: 100%;
  box-sizing: border-box;
  padding: 13px 14px;
  border: 1px solid #d8d0c9;
  border-radius: 8px;
  background: #fffdfa;
  color: #263238;
  font-family: inherit;
  font-size: 15px;
  outline: none;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.form-group input:focus {
  border-color: #275b4f;
  box-shadow: 0 0 0 3px rgba(39, 91, 79, 0.1);
}

.field-help {
  display: block;
  margin-top: 7px;
  color: #899196;
  font-size: 12px;
}


/* =========================================
   Capture Method Options
   ========================================= */

.method-section {
  margin-bottom: 28px;
}

.method-heading {
  margin-bottom: 14px;
}

.method-heading p {
  margin: 0;
  color: #68747a;
  font-size: 13px;
}

.method-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.method-option {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-height: 110px;
  padding: 17px;
  border: 1px solid #ded7d0;
  border-radius: 10px;
  background: #fffdfa;
  color: #263238;
  text-align: left;
  font-family: inherit;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    background-color 0.2s ease,
    box-shadow 0.2s ease;
}

.method-option:hover {
  border-color: #b9b0a8;
  box-shadow: 0 2px 8px rgba(60, 45, 35, 0.05);
}

.method-option.selected {
  border-color: #275b4f;
  background: #f3f8f5;
  box-shadow: 0 0 0 2px rgba(39, 91, 79, 0.08);
}

.method-icon {
  flex-shrink: 0;
  font-size: 22px;
}

.method-content {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.method-content strong {
  font-size: 14px;
}

.method-content span {
  color: #68747a;
  font-size: 12px;
  line-height: 1.4;
}

.selected-check {
  position: absolute;
  top: 10px;
  right: 11px;
  color: #275b4f;
  font-size: 14px;
  font-weight: 700;
}


/* =========================================
   Capture Area
   ========================================= */

.capture-area {
  display: flex;
  align-items: center;
  flex-direction: column;
  padding: 38px 25px;
  border: 1px dashed #cfc6be;
  border-radius: 12px;
  background: #faf7f2;
  text-align: center;
}

.capture-icon {
  margin-bottom: 12px;
  font-size: 32px;
}

.capture-area h3 {
  margin: 0 0 7px;
  color: #263238;
  font-size: 19px;
}

.capture-area > p {
  max-width: 560px;
  margin: 0 0 20px;
  color: #68747a;
  font-size: 13px;
  line-height: 1.5;
}


/* =========================================
   Recording
   ========================================= */

.primary-capture-button,
.stop-button,
.upload-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 155px;
  padding: 11px 18px;
  border: none;
  border-radius: 8px;
  background: #275b4f;
  color: #ffffff;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition:
    background-color 0.2s ease,
    transform 0.15s ease;
}

.primary-capture-button:hover,
.stop-button:hover,
.upload-button:hover {
  background: #1e473d;
  transform: translateY(-1px);
}

.stop-button {
  background: #b65f32;
}

.stop-button:hover {
  background: #914923;
}

.recording-status {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 15px;
  color: #914923;
  font-size: 18px;
  font-weight: 700;
}

.recording-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #b65f32;
  animation: pulse 1.2s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.35;
  }
}


/* =========================================
   Recording Complete
   ========================================= */

.recording-complete {
  display: flex;
  align-items: center;
  gap: 12px;
  width: min(100%, 480px);
  box-sizing: border-box;
  padding: 13px 15px;
  border: 1px solid #c8ddd1;
  border-radius: 9px;
  background: #eaf4ee;
  text-align: left;
}

.complete-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 27px;
  height: 27px;
  border-radius: 50%;
  background: #275b4f;
  color: #ffffff;
  font-size: 13px;
  font-weight: 700;
}

.recording-complete > div {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 2px;
}

.recording-complete strong {
  color: #35634a;
  font-size: 13px;
}

.recording-complete div span {
  color: #68747a;
  font-size: 11px;
}

.record-again-button {
  padding: 7px 10px;
  border: 1px solid #b9cec1;
  border-radius: 6px;
  background: #ffffff;
  color: #275b4f;
  font-family: inherit;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
}


/* =========================================
   File Upload
   ========================================= */

.hidden-file-input {
  display: none;
}

.selected-file {
  display: flex;
  align-items: center;
  gap: 10px;
  width: min(100%, 480px);
  box-sizing: border-box;
  margin-top: 18px;
  padding: 12px 14px;
  border: 1px solid #c8ddd1;
  border-radius: 9px;
  background: #eaf4ee;
  text-align: left;
}

.file-check {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 25px;
  height: 25px;
  border-radius: 50%;
  background: #275b4f;
  color: #ffffff;
  font-size: 12px;
  font-weight: 700;
}

.selected-file div {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 2px;
}

.selected-file strong {
  overflow: hidden;
  color: #35634a;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-file span:last-child {
  color: #68747a;
  font-size: 11px;
}


/* =========================================
   Manual Entry
   ========================================= */

.manual-area textarea {
  width: min(100%, 700px);
  min-height: 180px;
  box-sizing: border-box;
  resize: vertical;
  padding: 14px;
  border: 1px solid #d8d0c9;
  border-radius: 8px;
  background: #ffffff;
  color: #263238;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  outline: none;
}

.manual-area textarea:focus {
  border-color: #275b4f;
  box-shadow: 0 0 0 3px rgba(39, 91, 79, 0.1);
}

.character-help {
  display: block;
  width: min(100%, 700px);
  margin-top: 7px;
  color: #899196;
  font-size: 11px;
  text-align: left;
}


/* =========================================
   Prototype Information
   ========================================= */

.prototype-note {
  display: flex;
  align-items: flex-start;
  gap: 13px;
  margin-top: 24px;
  padding: 16px;
  border: 1px solid #e4ddd7;
  border-radius: 10px;
  background: #f5efe5;
}

.note-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 25px;
  height: 25px;
  border-radius: 50%;
  background: #ffffff;
  color: #275b4f;
  font-size: 13px;
  font-weight: 700;
}

.prototype-note strong {
  display: block;
  margin-bottom: 4px;
  color: #275b4f;
  font-size: 13px;
}

.prototype-note p {
  margin: 0;
  color: #68747a;
  font-size: 12px;
  line-height: 1.5;
}


/* =========================================
   Status Message
   ========================================= */

.message {
  margin-top: 20px;
  padding: 13px 15px;
  border: 1px solid #c8ddd1;
  border-radius: 8px;
  background: #eaf4ee;
  color: #35634a;
  font-size: 13px;
  line-height: 1.4;
}

.message.error {
  border-color: #e2c4b5;
  background: #f9eee8;
  color: #914923;
}


/* =========================================
   Form Actions
   ========================================= */

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid #eee8e2;
}

.cancel-button,
.submit-button {
  padding: 11px 18px;
  border-radius: 8px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition:
    background-color 0.2s ease,
    transform 0.15s ease;
}

.cancel-button {
  border: 1px solid #d8d0c9;
  background: #ffffff;
  color: #68747a;
}

.cancel-button:hover {
  background: #f7f4f0;
}

.submit-button {
  border: none;
  background: #b65f32;
  color: #ffffff;
}

.submit-button:hover:not(:disabled) {
  background: #914923;
  transform: translateY(-1px);
}

.submit-button:disabled {
  opacity: 0.65;
  cursor: wait;
}


/* =========================================
   Mobile
   ========================================= */

@media (max-width: 750px) {
  .capture-page {
    width: min(100% - 30px, 1000px);
    padding: 40px 0 55px;
  }

  .page-header h1 {
    font-size: 34px;
  }

  .workflow {
    align-items: flex-start;
    flex-direction: column;
    gap: 12px;
  }

  .workflow-line {
    width: 1px;
    height: 15px;
    margin: 0 0 0 14px;
  }

  .capture-card {
    padding: 24px;
  }

  .method-options {
    grid-template-columns: 1fr;
  }

  .method-option {
    min-height: auto;
  }

  .recording-complete {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .record-again-button {
    margin-left: 39px;
  }

  .form-actions {
    flex-direction: column-reverse;
  }

  .cancel-button,
  .submit-button {
    width: 100%;
  }
}
</style>
