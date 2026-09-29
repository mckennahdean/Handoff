<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch, getCurrentUser, errorMessage } from '../api.js'

const router = useRouter()
const user = getCurrentUser()

const codes = ref([])
const loading = ref(true)
const error = ref('')
const notice = ref('')
const saved = ref(false)

const codesText = computed(() => codes.value.join('\n'))

// Create a fresh set. The server keeps only hashes, so this page
// is the only place the plain codes ever appear.
onMounted(async () => {
  try {
    const response = await apiFetch('/api/auth/recovery-codes', {
      method: 'POST'
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        errorMessage(data, 'Unable to create recovery codes.')
      )
    }

    codes.value = data.codes
  } catch (err) {
    error.value = err.message || 'Unable to create recovery codes.'
  } finally {
    loading.value = false
  }
})

const copyCodes = async () => {
  try {
    await navigator.clipboard.writeText(codesText.value)
    notice.value = 'Codes copied.'
  } catch {
    notice.value = 'Copy failed. Please write the codes down.'
  }
}

// Save the codes as a small text file.
const downloadCodes = () => {
  const text =
    `Handoff recovery codes for ${user?.email || 'your account'}\n` +
    'Each code works once.\n\n' +
    codesText.value + '\n'

  const url = URL.createObjectURL(
    new Blob([text], { type: 'text/plain' })
  )

  const link = document.createElement('a')
  link.href = url
  link.download = 'handoff-recovery-codes.txt'
  link.click()
  URL.revokeObjectURL(url)
}

const continueToDashboard = () => {
  router.push(
    user?.role === 'owner' ? '/owner-dashboard' : '/employee-dashboard'
  )
}
</script>

<template>
  <main class="dashboard-shell">
    <section class="dashboard-header">
      <div>
        <p class="eyebrow">ACCOUNT RECOVERY</p>
        <h1>Save Your Recovery Codes</h1>
        <p class="intro">
          If you ever forget your password, one of these codes lets you
          set a new one from the login page. Each code works once.
          This is the only time they are shown.
        </p>
      </div>
    </section>

    <section class="content-card">
      <div v-if="loading" class="empty-state">
        Creating your codes...
      </div>

      <p v-else-if="error" class="error-message">
        {{ error }}
      </p>

      <template v-else>
        <ol class="code-grid">
          <li v-for="code in codes" :key="code">
            {{ code }}
          </li>
        </ol>

        <div class="code-actions">
          <button
            type="button"
            class="secondary-button"
            @click="copyCodes"
          >
            Copy Codes
          </button>

          <button
            type="button"
            class="secondary-button"
            @click="downloadCodes"
          >
            Download as Text File
          </button>
        </div>

        <p v-if="notice" class="notice">
          {{ notice }}
        </p>

        <label class="saved-check">
          <input v-model="saved" type="checkbox" />
          I saved these codes somewhere safe.
        </label>
      </template>

      <button
        type="button"
        class="primary-button"
        :disabled="!saved && !error"
        @click="continueToDashboard"
      >
        Continue
      </button>

      <p class="fallback-note">
        Lost your codes later? Your business owner can issue a new set
        from User Management.
      </p>
    </section>
  </main>
</template>

<style scoped>
.dashboard-shell {
  min-height: calc(100vh - 70px);
  padding: 55px 60px;
  box-sizing: border-box;
  background: #f5efe5;
}

.dashboard-header {
  max-width: 760px;
  margin: 0 auto 32px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #d26f3d;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 1.5px;
}

.dashboard-header h1 {
  margin: 0 0 12px;
  color: #275b4f;
  font-size: 38px;
  font-weight: 700;
  line-height: 1.2;
}

.intro {
  margin: 0;
  color: #666666;
  font-size: 16px;
  line-height: 1.6;
}

.content-card {
  max-width: 760px;
  margin: 0 auto;
  padding: 30px;
  box-sizing: border-box;
  border: 1px solid #ded8ce;
  border-radius: 14px;
  background: #ffffff;
}

.code-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 30px;
  margin: 0 0 24px;
  padding: 20px 20px 20px 45px;
  border: 1px dashed #d8d2c8;
  border-radius: 10px;
  background: #faf8f4;
  color: #275b4f;
  font-family: 'Courier New', monospace;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 2px;
}

.code-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.secondary-button {
  padding: 11px 18px;
  border: 1px solid #d26f3d;
  border-radius: 8px;
  background: #ffffff;
  color: #d26f3d;
  font-family: inherit;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.secondary-button:hover {
  background: #d26f3d;
  color: #ffffff;
}

.primary-button {
  display: block;
  width: 100%;
  margin-top: 24px;
  padding: 14px;
  border: none;
  border-radius: 8px;
  background: #275b4f;
  color: #ffffff;
  font-family: inherit;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
}

.primary-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.notice {
  margin: 12px 0 0;
  color: #275b4f;
  font-size: 13px;
}

.saved-check {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 24px;
  color: #333333;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.error-message {
  margin: 0;
  color: #a44a3a;
  font-size: 14px;
  font-weight: 600;
}

.empty-state {
  padding: 35px 20px;
  border: 1px dashed #d8d2c8;
  border-radius: 10px;
  background: #faf8f4;
  color: #777777;
  font-size: 14px;
  text-align: center;
}

.fallback-note {
  margin: 16px 0 0;
  color: #777777;
  font-size: 13px;
  text-align: center;
}

@media (max-width: 600px) {
  .dashboard-shell {
    padding: 30px 18px;
  }

  .dashboard-header h1 {
    font-size: 30px;
  }

  .code-grid {
    grid-template-columns: 1fr;
    font-size: 18px;
  }
}
</style>