<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch, errorMessage } from '../api.js'

// Allows navigation between pages.
const router = useRouter()

// Stores the values entered into the reset form.
const email = ref('')
const recoveryCode = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

// Controls whether the password fields are visible.
const showPassword = ref(false)

// Same live rules as the sign-up page. The backend enforces them.
const passwordChecks = computed(() => {
  const value = newPassword.value

  return [
    { label: 'At least 12 characters', met: value.length >= 12 },
    { label: 'One uppercase letter', met: /[A-Z]/.test(value) },
    { label: 'One lowercase letter', met: /[a-z]/.test(value) },
    { label: 'One number', met: /[0-9]/.test(value) },
    { label: 'One special character', met: /[^A-Za-z0-9]/.test(value) }
  ]
})

const passwordIsValid = computed(() =>
  passwordChecks.value.every((check) => check.met)
)

// Displays a message after the user takes an action.
const message = ref('')

// Sets a new password with one of the user's recovery codes.
const resetPassword = async () => {
  message.value = ''

  if (newPassword.value !== confirmPassword.value) {
    message.value = 'Passwords do not match. Please try again.'
    return
  }

  if (!passwordIsValid.value) {
    message.value =
      'Please choose a password that meets all of the requirements.'
    return
  }

  try {
    const response = await apiFetch('/api/auth/recover', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: email.value,
        recovery_code: recoveryCode.value,
        new_password: newPassword.value
      })
    })

    const data = await response.json()

    if (!response.ok) {
      message.value = errorMessage(data, 'Unable to reset your password.')
      return
    }

    router.push({ path: '/login', query: { recovered: '1' } })
  } catch {
    message.value =
      'Unable to reach the Handoff server. Please try again.'
  }
}

// Returns the user to the login screen.
const goToLogin = () => {
  router.push('/login')
}
</script>

<template>
  <main class="login-page">

    <!-- Main login card -->
    <section class="login-card">

      <!-- Left branding panel -->
      <div class="brand-panel">
        <div class="brand-content">

          <!-- Logo container -->
          <div class="logo-card">
            <img
              src="/images/Handoff_Icon.png"
              alt="Handoff logo"
              class="handoff-logo"
            />
          </div>

          <!-- Branding message -->
          <div class="brand-message">
            <h2>Keep your team's knowledge moving forward.</h2>

            <p>
              Give your team one place to capture, share, and
              find the knowledge they need.
            </p>
          </div>

        </div>
      </div>

      <!-- Right login panel -->
      <div class="form-panel">
        <div class="form-content">

          <!-- Heading -->
          <div class="heading-section">
            <h1>Reset Your Password</h1>

            <p>
              Enter your email, one of your recovery codes, and a
              new password. Each code works once.
            </p>
          </div>

          <!-- Reset form -->
          <form @submit.prevent="resetPassword">

            <!-- Email -->
            <div class="form-group">
              <label for="email">Email Address</label>

              <input
                id="email"
                v-model="email"
                type="email"
                placeholder="you@example.com"
                required
              />
            </div>

            <!-- Recovery code -->
            <div class="form-group">
              <label for="recovery-code">Recovery Code</label>

              <input
                id="recovery-code"
                v-model="recoveryCode"
                type="text"
                placeholder="For example, K7QPM-2XH9R"
                autocomplete="off"
                required
              />
            </div>

            <!-- New password -->
            <div class="form-group">
              <label for="new-password">New Password</label>

              <div class="password-input">
                <input
                  id="new-password"
                  v-model="newPassword"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="Choose a new password"
                  autocomplete="new-password"
                  required
                />

                <!-- Password visibility toggle -->
                <button
                  type="button"
                  class="password-toggle"
                  :aria-label="
                    showPassword ? 'Hide password' : 'Show password'
                  "
                  @click="showPassword = !showPassword"
                >

                  <!-- Hidden password icon -->
                  <svg
                    v-if="!showPassword"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"
                    />

                    <circle
                      cx="12"
                      cy="12"
                      r="2.5"
                    />
                  </svg>

                  <!-- Visible password icon -->
                  <svg
                    v-else
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path d="M3 3l18 18" />

                    <path
                      d="M10.6 6.2A10.8 10.8 0 0 1 12 6c6.5 0 10 6 10 6a17.4 17.4 0 0 1-3.1 3.8"
                    />

                    <path
                      d="M6.1 6.1C3.5 8.1 2 12 2 12s3.5 6 10 6c1.4 0 2.7-.3 3.8-.8"
                    />
                  </svg>

                </button>
              </div>

              <!-- Live password requirements -->
              <ul class="password-rules">
                <li
                  v-for="check in passwordChecks"
                  :key="check.label"
                  :class="{ met: check.met }"
                >
                  {{ check.met ? '✓' : '○' }} {{ check.label }}
                </li>
              </ul>
            </div>

            <!-- Confirm new password -->
            <div class="form-group">
              <label for="confirm-password">Confirm New Password</label>

              <input
                id="confirm-password"
                v-model="confirmPassword"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Re-enter your new password"
                autocomplete="new-password"
                required
              />
            </div>

            <!-- Reset button -->
            <button
              type="submit"
              class="signin-button"
            >
              Reset Password
            </button>

          </form>

          <!-- Back to sign in -->
          <div class="signup-link">
            <span>Remembered it?</span>

            <button
              type="button"
              class="signup-link-button"
              @click="goToLogin"
            >
              Sign In
            </button>
          </div>

          <!-- Temporary message -->
          <p
            v-if="message"
            class="message"
          >
            {{ message }}
          </p>

          <!-- Footer -->
          <p class="footer-note">
            Your knowledge. Your business. Your Handoff.
          </p>

        </div>
      </div>

    </section>
  </main>
</template>

<style scoped>

/* =========================================
   Overall Login Page
   ========================================= */

.login-page {
  min-height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  box-sizing: border-box;
  background: #f5efe5;
}


/* =========================================
   Main Login Card
   ========================================= */

.login-card {
  width: 100%;
  max-width: 1050px;
  min-height: 650px;
  display: grid;
  grid-template-columns: 46% 54%;
  overflow: hidden;
  background: #ffffff;
  border-radius: 20px;
  box-shadow:
    0 20px 50px rgba(39, 91, 79, 0.12);
}


/* =========================================
   Left Branding Panel
   ========================================= */

.brand-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 55px 45px;
  box-sizing: border-box;
  background: #275b4f;
}


.brand-content {
  width: 100%;
  max-width: 390px;
  text-align: center;
}


/* =========================================
   Logo Card
   ========================================= */

.logo-card {
  width: 100%;
  max-width: 360px;
  margin: 0 auto 42px;
  padding: 22px;
  box-sizing: border-box;
  background: #f7f4eb;
  border-radius: 16px;
  box-shadow:
    0 8px 25px rgba(0, 0, 0, 0.12);
}


.handoff-logo {
  display: block;
  width: 100%;
  height: auto;
}


/* =========================================
   Branding Message
   ========================================= */

.brand-message {
  max-width: 330px;
  margin: 0 auto;
  color: #ffffff;
}


.brand-message h2 {
  margin: 0 0 14px;
  font-size: 24px;
  font-weight: 600;
  line-height: 1.3;
}


.brand-message p {
  margin: 0;
  font-size: 15px;
  line-height: 1.7;
  opacity: 0.9;
}


/* =========================================
   Right Form Panel
   ========================================= */

.form-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 55px 70px;
  box-sizing: border-box;
  background: #ffffff;
}


.form-content {
  width: 100%;
  max-width: 410px;
}


/* =========================================
   Heading
   ========================================= */

.heading-section {
  margin-bottom: 32px;
}


.heading-section h1 {
  margin: 0 0 10px;
  color: #275b4f;
  font-size: 34px;
  font-weight: 700;
  line-height: 1.2;
}


.heading-section p {
  margin: 0;
  color: #6b6b6b;
  font-size: 15px;
  line-height: 1.6;
}


/* =========================================
   Form Fields
   ========================================= */

.form-group {
  margin-bottom: 22px;
}


.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #333333;
  font-size: 14px;
  font-weight: 600;
}


.form-group input {
  width: 100%;
  padding: 13px 15px;
  box-sizing: border-box;
  border: 1px solid #d8d2c8;
  border-radius: 8px;
  background: #ffffff;
  color: #333333;
  font-family: inherit;
  font-size: 15px;
  outline: none;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}


.form-group input::placeholder {
  color: #a5a5a5;
}


.form-group input:focus {
  border-color: #275b4f;
  box-shadow:
    0 0 0 3px rgba(39, 91, 79, 0.12);
}


/* =========================================
   Password Label Row
   ========================================= */

.password-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}


.password-label-row label {
  margin-bottom: 8px;
}


.password-rules {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 12px;
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
  color: #a0a0a0;
  font-size: 12px;
}


.password-rules li.met {
  color: #275b4f;
  font-weight: 600;
}


/* =========================================
   Password Input
   ========================================= */

.password-input {
  position: relative;
}


.password-input input {
  padding-right: 48px;
}


/* =========================================
   Password Visibility Toggle
   ========================================= */

.password-toggle {
  position: absolute;
  top: 50%;
  right: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  background: none;
  color: #275b4f;
  cursor: pointer;
  transform: translateY(-50%);
}


.password-toggle svg {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}


.password-toggle:hover {
  color: #d26f3d;
}


/* =========================================
   Sign In Button
   ========================================= */

.signin-button {
  width: 100%;
  margin-top: 5px;
  padding: 15px;
  border: none;
  border-radius: 8px;
  background: #d26f3d;
  color: #ffffff;
  font-family: inherit;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition:
    transform 0.15s,
    opacity 0.15s,
    box-shadow 0.15s;
}


.signin-button:hover {
  opacity: 0.92;
  transform: translateY(-1px);
  box-shadow:
    0 5px 15px rgba(210, 111, 61, 0.2);
}


.signin-button:active {
  transform: translateY(0);
}


/* =========================================
   Sign-Up Link
   ========================================= */

.signup-link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  margin-top: 24px;
  color: #666666;
  font-size: 14px;
}


.signup-link-button {
  padding: 0;
  border: none;
  background: none;
  color: #275b4f;
  font-family: inherit;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}


.signup-link-button:hover {
  text-decoration: underline;
}


/* =========================================
   Temporary Message
   ========================================= */

.message {
  margin: 20px 0 0;
  padding: 12px;
  border-radius: 7px;
  background: #f5efe5;
  color: #275b4f;
  font-size: 13px;
  line-height: 1.4;
  text-align: center;
}


/* =========================================
   Footer
   ========================================= */

.footer-note {
  margin: 28px 0 0;
  color: #a0a0a0;
  font-size: 12px;
  text-align: center;
}


/* =========================================
   Tablet / Smaller Screens
   ========================================= */

@media (max-width: 850px) {

  .login-card {
    grid-template-columns: 1fr;
    max-width: 600px;
  }

  .brand-panel {
    padding: 45px 35px;
  }

  .logo-card {
    max-width: 330px;
    margin-bottom: 28px;
  }

  .brand-message h2 {
    font-size: 22px;
  }

  .brand-message p {
    font-size: 14px;
  }

  .form-panel {
    padding: 50px 45px;
  }

}


/* =========================================
   Mobile
   ========================================= */

@media (max-width: 500px) {

  .login-page {
    padding: 15px;
  }

  .login-card {
    border-radius: 14px;
  }

  .brand-panel {
    padding: 35px 25px;
  }

  .logo-card {
    padding: 15px;
    margin-bottom: 25px;
  }

  .brand-message h2 {
    font-size: 20px;
  }

  .brand-message p {
    font-size: 13px;
  }

  .form-panel {
    padding: 40px 25px;
  }

  .heading-section h1 {
    font-size: 30px;
  }

  .password-label-row {
    align-items: flex-start;
    gap: 10px;
  }

  .signup-link {
    flex-direction: column;
    gap: 7px;
  }

}

</style>