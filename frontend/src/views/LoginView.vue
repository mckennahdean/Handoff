<script setup>
import { ref } from 'vue'

// Stores the values entered into the login form
const email = ref('')
const password = ref('')

// Controls whether the password is visible
const showPassword = ref(false)

// Displays a message after a user takes an action
const message = ref('')

// Handles the Sign In button
// This is currently a mock action until backend authentication is implemented
const signIn = () => {
  message.value = 'Sign-in functionality will be connected to the Handoff backend.'
}

// Handles the Create an Account button
// This is currently a mock action until account creation is implemented
const createAccount = () => {
  message.value = 'Account creation will be connected to the Handoff backend.'
}

// Handles the Forgot Password link
// This is currently a mock action until authentication is implemented
const forgotPassword = () => {
  message.value = 'Password recovery will be available when authentication is implemented.'
}
</script>

<template>
  <main class="login-page">

    <!-- Main login card -->
    <section class="login-card">

      <!-- Left branding panel -->
      <div class="brand-panel">

        <div class="brand-content">

          <!-- Logo container keeps the green logo readable -->
          <div class="logo-card">
            <img
              src="/images/Handoff_Icon.png"
              alt="Handoff logo"
              class="handoff-logo"
            />
          </div>

          <!-- Branding message -->
          <div class="brand-message">
            <h2>Knowledge that stays with your business.</h2>

            <p>
              Capture the experience of your team and make it easier
              for everyone to find, understand, and use.
            </p>
          </div>

        </div>

      </div>

      <!-- Right login panel -->
      <div class="form-panel">

        <div class="form-content">

          <!-- Heading -->
          <div class="heading-section">
            <h1>Welcome Back</h1>

            <p>
              Sign in to access your Handoff knowledge base.
            </p>
          </div>

          <!-- Login form -->
          <form @submit.prevent="signIn">

            <!-- Email field -->
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

            <!-- Password field -->
            <div class="form-group">

              <div class="password-label">
                <label for="password">Password</label>

                <button
                  type="button"
                  class="forgot-password"
                  @click="forgotPassword"
                >
                  Forgot password?
                </button>
              </div>

              <!-- Password input with visibility toggle -->
              <div class="password-input">

                <input
                  id="password"
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="Enter your password"
                  required
                />

                <button
                  type="button"
                  class="password-toggle"
                  :aria-label="showPassword ? 'Hide password' : 'Show password'"
                  @click="showPassword = !showPassword"
                >

                  <!-- Eye icon when password is hidden -->
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

                  <!-- Eye-off icon when password is visible -->
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

            <!-- Sign in button -->
            <button
              type="submit"
              class="sign-in-button"
            >
              Sign In
            </button>

          </form>

          <!-- Create account -->
          <div class="create-account">
            <span>Don't have an account?</span>

            <button
              type="button"
              class="create-account-button"
              @click="createAccount"
            >
              Create an Account
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

  /* Warm cream background */
  background: #f5efe5;
}


/* =========================================
   Main Login Card
   ========================================= */

.login-card {
  width: 100%;
  max-width: 1050px;
  min-height: 620px;

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

  padding: 65px 70px;
  box-sizing: border-box;

  background: #ffffff;
}


.form-content {
  width: 100%;
  max-width: 400px;
}


/* =========================================
   Heading
   ========================================= */

.heading-section {
  margin-bottom: 38px;
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
  margin-bottom: 24px;
}


.form-group label {
  display: block;

  margin-bottom: 8px;

  color: #333333;

  font-size: 14px;
  font-weight: 600;
}


/* =========================================
   Password Label
   ========================================= */

.password-label {
  display: flex;
  align-items: center;
  justify-content: space-between;

  margin-bottom: 8px;
}


.password-label label {
  margin-bottom: 0;
}


/* =========================================
   Input Fields
   ========================================= */

.form-group input {
  width: 100%;

  padding: 14px 15px;

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
   Forgot Password
   ========================================= */

.forgot-password {
  padding: 0;

  border: none;

  background: none;

  color: #275b4f;

  font-family: inherit;
  font-size: 12px;
  font-weight: 600;

  cursor: pointer;
}


.forgot-password:hover {
  text-decoration: underline;
}


/* =========================================
   Sign In Button
   ========================================= */

.sign-in-button {
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


.sign-in-button:hover {
  opacity: 0.92;

  transform: translateY(-1px);

  box-shadow:
    0 5px 15px rgba(210, 111, 61, 0.2);
}


.sign-in-button:active {
  transform: translateY(0);
}


/* =========================================
   Create Account
   ========================================= */

.create-account {
  display: flex;
  align-items: center;
  justify-content: center;

  gap: 5px;

  margin-top: 28px;

  color: #666666;

  font-size: 14px;
}


.create-account-button {
  padding: 0;

  border: none;

  background: none;

  color: #275b4f;

  font-family: inherit;
  font-size: 14px;
  font-weight: 700;

  cursor: pointer;
}


.create-account-button:hover {
  text-decoration: underline;
}


/* =========================================
   Temporary Message
   ========================================= */

.message {
  margin: 22px 0 0;
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
  margin: 38px 0 0;

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


  .create-account {
    flex-direction: column;
    gap: 7px;
  }

}

</style>
