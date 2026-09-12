<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Gets the current user's information from the frontend prototype session.
const storedUser = localStorage.getItem('handoffUser')

const user = storedUser
  ? JSON.parse(storedUser)
  : {
      name: 'Employee'
    }

// Navigate to a Handoff feature.
const goTo = (path) => {
  router.push(path)
}
</script>

<template>
  <main class="dashboard-page">

    <!-- Dashboard header -->
    <section class="dashboard-header">

      <div>
        <p class="eyebrow">EMPLOYEE DASHBOARD</p>

        <h1>
          Welcome back, {{ user.name }}
        </h1>

        <p class="intro">
          Find the information you need and get answers
          from your team's approved knowledge.
        </p>
      </div>

    </section>

    <!-- Primary action -->
    <section class="primary-section">

      <button
        class="query-card"
        @click="goTo('/query')"
      >
        <div class="query-icon">
          ?
        </div>

        <div class="query-content">
          <span class="query-label">KNOWLEDGE BASE</span>

          <h2>Ask Handoff</h2>

          <p>
            Ask a question about your company's procedures
            and get an answer grounded in approved knowledge.
          </p>

          <span class="query-action">
            Ask a Question →
          </span>
        </div>
      </button>

    </section>

    <!-- Available resources -->
    <section class="section">

      <div class="section-heading">
        <h2>Your Resources</h2>

        <p>
          Access the knowledge your organization has made available to you.
        </p>
      </div>

      <div class="resource-grid">

        <!-- Approved procedures -->
        <button
          class="resource-card"
          @click="goTo('/procedures')"
        >
          <div class="resource-icon">
            ✓
          </div>

          <div>
            <h3>Approved Procedures</h3>

            <p>
              Browse procedures that have been reviewed and
              approved by your organization.
            </p>
          </div>
        </button>

        <!-- Ask Handoff -->
        <button
          class="resource-card"
          @click="goTo('/query')"
        >
          <div class="resource-icon">
            ?
          </div>

          <div>
            <h3>Ask Handoff</h3>

            <p>
              Search your organization's knowledge by asking
              questions in plain language.
            </p>
          </div>
        </button>

      </div>

    </section>

    <!-- Access information -->
    <section class="access-note">

      <div class="access-icon">
        i
      </div>

      <div>
        <strong>Your access</strong>

        <p>
          Your account provides access to approved business
          knowledge. Procedures and documentation are managed
          by your organization's owner.
        </p>
      </div>

    </section>

    <!-- Prototype notice -->
    <section class="prototype-note">
      <strong>Prototype:</strong>
      Account information and permissions are currently
      simulated and will be connected to the Handoff backend
      during integration.
    </section>

  </main>
</template>

<style scoped>

/* =========================================
   Overall Dashboard
   ========================================= */

.dashboard-page {
  min-height: calc(100vh - 70px);
  padding: 55px 60px;
  box-sizing: border-box;
  background: #f5efe5;
}


/* =========================================
   Header
   ========================================= */

.dashboard-header {
  max-width: 1000px;
  margin: 0 auto 40px;
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
  max-width: 650px;
  margin: 0;
  color: #666666;
  font-size: 16px;
  line-height: 1.6;
}


/* =========================================
   Primary Query Card
   ========================================= */

.primary-section {
  max-width: 1000px;
  margin: 0 auto 45px;
}


.query-card {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 28px;
  padding: 32px;
  box-sizing: border-box;
  border: none;
  border-radius: 16px;
  background: #275b4f;
  color: #ffffff;
  text-align: left;
  cursor: pointer;
  transition:
    transform 0.15s,
    box-shadow 0.15s;
}


.query-card:hover {
  transform: translateY(-2px);
  box-shadow:
    0 10px 30px rgba(39, 91, 79, 0.2);
}


.query-icon {
  flex-shrink: 0;
  width: 65px;
  height: 65px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: #f7f4eb;
  color: #275b4f;
  font-size: 30px;
  font-weight: 700;
}


.query-content {
  flex: 1;
}


.query-label {
  display: block;
  margin-bottom: 5px;
  color: #d9e8e3;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1.5px;
}


.query-content h2 {
  margin: 0 0 7px;
  font-size: 27px;
}


.query-content p {
  max-width: 650px;
  margin: 0 0 12px;
  color: #e6efec;
  font-size: 14px;
  line-height: 1.55;
}


.query-action {
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
}


/* =========================================
   Resources Section
   ========================================= */

.section {
  max-width: 1000px;
  margin: 0 auto;
}


.section-heading {
  margin-bottom: 22px;
}


.section-heading h2 {
  margin: 0 0 7px;
  color: #333333;
  font-size: 24px;
}


.section-heading p {
  margin: 0;
  color: #777777;
  font-size: 14px;
}


/* =========================================
   Resource Cards
   ========================================= */

.resource-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 18px;
}


.resource-card {
  display: flex;
  align-items: flex-start;
  gap: 18px;
  padding: 25px;
  border: 1px solid #ded8ce;
  border-radius: 14px;
  background: #ffffff;
  text-align: left;
  cursor: pointer;
  transition:
    transform 0.15s,
    box-shadow 0.15s,
    border-color 0.15s;
}


.resource-card:hover {
  transform: translateY(-2px);
  border-color: #275b4f;
  box-shadow:
    0 8px 25px rgba(39, 91, 79, 0.1);
}


.resource-icon {
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #275b4f;
  color: #ffffff;
  font-size: 20px;
  font-weight: 700;
}


.resource-card h3 {
  margin: 2px 0 7px;
  color: #275b4f;
  font-size: 17px;
}


.resource-card p {
  margin: 0;
  color: #777777;
  font-size: 14px;
  line-height: 1.55;
}


/* =========================================
   Access Information
   ========================================= */

.access-note {
  max-width: 1000px;
  margin: 35px auto 0;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px;
  box-sizing: border-box;
  border-radius: 10px;
  background: #ffffff;
}


.access-icon {
  flex-shrink: 0;
  width: 25px;
  height: 25px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f5efe5;
  color: #275b4f;
  font-size: 14px;
  font-weight: 700;
}


.access-note strong {
  display: block;
  margin-bottom: 4px;
  color: #275b4f;
  font-size: 13px;
}


.access-note p {
  margin: 0;
  color: #777777;
  font-size: 13px;
  line-height: 1.5;
}


/* =========================================
   Prototype Notice
   ========================================= */

.prototype-note {
  max-width: 1000px;
  margin: 18px auto 0;
  padding: 14px 18px;
  box-sizing: border-box;
  border-radius: 8px;
  background: #ffffff;
  color: #777777;
  font-size: 12px;
  line-height: 1.5;
}


.prototype-note strong {
  color: #275b4f;
}


/* =========================================
   Tablet
   ========================================= */

@media (max-width: 850px) {

  .dashboard-page {
    padding: 40px 30px;
  }

  .resource-grid {
    grid-template-columns: 1fr;
  }

}


/* =========================================
   Mobile
   ========================================= */

@media (max-width: 500px) {

  .dashboard-page {
    padding: 30px 18px;
  }

  .dashboard-header h1 {
    font-size: 30px;
  }

  .intro {
    font-size: 14px;
  }

  .query-card {
    flex-direction: column;
    align-items: flex-start;
    padding: 25px;
  }

  .resource-card {
    padding: 20px;
  }

}

</style>
