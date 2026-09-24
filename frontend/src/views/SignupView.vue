<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch, saveSession, errorMessage } from '../api.js'

// Allows navigation between the login and sign-up screens.
const router = useRouter()

// Stores the values entered into the sign-up form.
const name = ref('')
const business = ref('')
const inviteCode = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')

// True only when no accounts exist yet. The first account
// becomes the Owner and names the business. Everyone after
// that joins as an Employee using the Owner's invite code.
const needsOwner = ref(false)

// Controls whether the password fields are visible.
const showPassword = ref(false)
const showConfirmPassword = ref(false)

// Displays a message after the user takes an action.
const message = ref('')

// Ask the backend whether this is the first account.
onMounted(async () => {
  try {
    const response = await apiFetch('/api/auth/setup-status')
    const data = await response.json()

    needsOwner.value = data.needs_owner
  } catch {
    message.value = 'Unable to reach the Handoff server.'
  }
})

// Handles account creation through the Handoff backend.
const createAccount = async () => {
  message.value = ''

  if (password.value !== confirmPassword.value) {
    message.value = 'Passwords do not match. Please try again.'
    return
  }

  const body = {
    name: name.value,
    email: email.value,
    password: password.value
  }

  if (needsOwner.value) {
    body.business_name = business.value
  } else {
    body.invite_code = inviteCode.value
  }

  try {
    const response = await apiFetch('/api/auth/signup', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    })

    const data = await response.json()

    if (!response.ok) {
      message.value = errorMessage(
        data,
        'Unable to create account. Please check the form.'
      )
      return
    }

    saveSession(data.access_token, data.user)

    router.push(
      data.user.role === 'owner'
        ? '/owner-dashboard'
        : '/employee-dashboard'
    )
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
  <main class="signup-page">

    <!-- Main sign-up card -->
    <section class="signup-card">

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

      <!-- Right sign-up panel -->
      <div class="form-panel">
        <div class="form-content">

          <!-- Heading -->
          <div class="heading-section">
            <h1>Create Your Account</h1>

            <p>
              Get started with Handoff and keep your business
              knowledge in one place.
            </p>
          </div>

          <!-- Sign-up form -->
          <form @submit.prevent="createAccount">

            <!-- Full name -->
            <div class="form-group">
              <label for="name">Full Name</label>

              <input
                id="name"
                v-model="name"
                type="text"
                placeholder="Your full name"
                required
              />
            </div>

            <!-- Business name: first account only (becomes the Owner) -->
            <div v-if="needsOwner" class="form-group">
              <label for="business">Business Name (you will be the Owner)</label>

              <input
                id="business"
                v-model="business"
                type="text"
                placeholder="Your business or organization"
                required
              />
            </div>

            <!-- Invite code: every account after the Owner -->
            <div v-else class="form-group">
              <label for="invite-code">Invite Code</label>

              <input
                id="invite-code"
                v-model="inviteCode"
                type="text"
                placeholder="8-character code from your manager"
                maxlength="8"
                required
              />
            </div>

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

            <!-- Password -->
            <div class="form-group">
              <label for="password">Password</label>

              <div class="password-input">
                <input
                  id="password"
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="Create a password"
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
            </div>

            <!-- Confirm password -->
            <div class="form-group">
              <label for="confirm-password">Confirm Password</label>

              <div class="password-input">
                <input
                  id="confirm-password"
                  v-model="confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  placeholder="Re-enter your password"
                  required
                />

                <!-- Confirm password visibility toggle -->
                <button
                  type="button"
                  class="password-toggle"
                  :aria-label="
                    showConfirmPassword
                      ? 'Hide password'
                      : 'Show password'
                  "
                  @click="showConfirmPassword = !showConfirmPassword"
                >

                  <!-- Hidden password icon -->
                  <svg
                    v-if="!showConfirmPassword"
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
            </div>

            <!-- Create account button -->
            <button
              type="submit"
              class="create-button"
            >
              Create Account
            </button>

          </form>

          <!-- Return to login -->
          <div class="login-link">
            <span>Already have an account?</span>

            <button
              type="button"
              class="login-link-button"
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
   Overall Sign-Up Page
   ========================================= */

.signup-page {
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
   Main Sign-Up Card
   ========================================= */

.signup-card {
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
  margin-bottom: 28px;
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
  margin-bottom: 18px;
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
   Account Role Selection
   ========================================= */

.role-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}


.role-option {
  display: flex !important;
  align-items: flex-start;
  gap: 10px;
  margin: 0;
  padding: 14px;
  box-sizing: border-box;
  border: 1px solid #d8d2c8;
  border-radius: 8px;
  background: #ffffff;
  cursor: pointer;
  transition:
    border-color 0.2s,
    background 0.2s,
    box-shadow 0.2s;
}


.role-option:hover {
  border-color: #275b4f;
}


.role-option.selected {
  border-color: #275b4f;
  background: #f5f9f7;
  box-shadow:
    0 0 0 2px rgba(39, 91, 79, 0.08);
}


.role-option input[type='radio'] {
  width: auto;
  margin-top: 3px;
  accent-color: #275b4f;
  cursor: pointer;
}


.role-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}


.role-title {
  color: #275b4f;
  font-size: 14px;
  font-weight: 700;
}


.role-description {
  color: #6b6b6b;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.4;
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
   Create Account Button
   ========================================= */

.create-button {
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


.create-button:hover {
  opacity: 0.92;
  transform: translateY(-1px);
  box-shadow:
    0 5px 15px rgba(210, 111, 61, 0.2);
}


.create-button:active {
  transform: translateY(0);
}


/* =========================================
   Login Link
   ========================================= */

.login-link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  margin-top: 24px;
  color: #666666;
  font-size: 14px;
}


.login-link-button {
  padding: 0;
  border: none;
  background: none;
  color: #275b4f;
  font-family: inherit;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}


.login-link-button:hover {
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

  .signup-card {
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

  .signup-page {
    padding: 15px;
  }

  .signup-card {
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

  .role-options {
    grid-template-columns: 1fr;
  }

  .login-link {
    flex-direction: column;
    gap: 7px;
  }
}

</style>
