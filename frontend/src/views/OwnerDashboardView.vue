<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Temporary prototype data.
// These numbers will eventually come from the Handoff backend.
const procedureCount = ref(12)
const pendingReviews = ref(3)
const documentationGaps = ref(5)

// Gets the current user's information from the frontend prototype session.
const storedUser = localStorage.getItem('handoffUser')

const user = storedUser
  ? JSON.parse(storedUser)
  : {
      name: 'Owner'
    }

// Navigate to a specific Handoff feature.
const goTo = (path) => {
  router.push(path)
}
</script>

<template>
  <main class="dashboard-page">

    <!-- Dashboard header -->
    <section class="dashboard-header">

      <div>
        <p class="eyebrow">OWNER DASHBOARD</p>

        <h1>
          Welcome back, {{ user.name }}
        </h1>

        <p class="intro">
          Manage your team's knowledge and keep important
          business procedures moving forward.
        </p>
      </div>

    </section>

    <!-- Overview cards -->
    <section class="stats-grid">

      <!-- Procedures -->
      <button
        class="stat-card"
        @click="goTo('/procedures')"
      >
        <span class="stat-label">Procedures</span>
        <strong>{{ procedureCount }}</strong>
        <span class="stat-description">
          Approved procedures in your knowledge base
        </span>
      </button>

      <!-- Reviews -->
      <button
        class="stat-card"
        @click="goTo('/procedure-review')"
      >
        <span class="stat-label">Pending Reviews</span>
        <strong>{{ pendingReviews }}</strong>
        <span class="stat-description">
          Procedures waiting for your approval
        </span>
      </button>

      <!-- Documentation gaps -->
      <button
        class="stat-card"
        @click="goTo('/gaps')"
      >
        <span class="stat-label">Knowledge Gaps</span>
        <strong>{{ documentationGaps }}</strong>
        <span class="stat-description">
          Questions that need documentation
        </span>
      </button>

    </section>

    <!-- Main actions -->
    <section class="section">

      <div class="section-heading">
        <h2>Manage Knowledge</h2>

        <p>
          Capture, review, and maintain the knowledge your
          employees rely on.
        </p>
      </div>

      <div class="action-grid">

        <!-- Record / upload -->
        <button
          class="action-card"
          @click="goTo('/procedures')"
        >
          <div class="action-icon">
            +
          </div>

          <div>
            <h3>Capture a Procedure</h3>

            <p>
              Record or upload an experienced employee's
              knowledge for Handoff to structure.
            </p>
          </div>
        </button>

        <!-- Review -->
        <button
          class="action-card"
          @click="goTo('/procedure-review')"
        >
          <div class="action-icon">
            ✓
          </div>

          <div>
            <h3>Review Procedures</h3>

            <p>
              Review AI-generated procedures and approve
              them before they become available to employees.
            </p>
          </div>
        </button>

        <!-- Gaps -->
        <button
          class="action-card"
          @click="goTo('/gaps')"
        >
          <div class="action-icon">
            !
          </div>

          <div>
            <h3>Documentation Gaps</h3>

            <p>
              See questions Handoff could not answer and
              identify knowledge that still needs to be captured.
            </p>
          </div>
        </button>

        <!-- Query -->
        <button
          class="action-card"
          @click="goTo('/query')"
        >
          <div class="action-icon">
            ?
          </div>

          <div>
            <h3>Ask Handoff</h3>

            <p>
              Test the knowledge base by asking questions
              about documented business procedures.
            </p>
          </div>
        </button>

      </div>

    </section>

    <!-- Prototype notice -->
    <section class="prototype-note">
      <strong>Prototype:</strong>
      Dashboard statistics and account information are
      currently simulated and will be connected to the
      Handoff backend during integration.
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
  max-width: 1150px;
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
   Statistics
   ========================================= */

.stats-grid {
  max-width: 1150px;
  margin: 0 auto 50px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}


.stat-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
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


.stat-card:hover {
  transform: translateY(-2px);
  border-color: #275b4f;
  box-shadow:
    0 8px 25px rgba(39, 91, 79, 0.1);
}


.stat-label {
  color: #666666;
  font-size: 14px;
  font-weight: 600;
}


.stat-card strong {
  margin: 8px 0;
  color: #275b4f;
  font-size: 34px;
}


.stat-description {
  color: #888888;
  font-size: 13px;
  line-height: 1.4;
}


/* =========================================
   Main Section
   ========================================= */

.section {
  max-width: 1150px;
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
   Action Cards
   ========================================= */

.action-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 18px;
}


.action-card {
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


.action-card:hover {
  transform: translateY(-2px);
  border-color: #275b4f;
  box-shadow:
    0 8px 25px rgba(39, 91, 79, 0.1);
}


.action-icon {
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #275b4f;
  color: #ffffff;
  font-size: 21px;
  font-weight: 700;
}


.action-card h3 {
  margin: 2px 0 7px;
  color: #275b4f;
  font-size: 17px;
}


.action-card p {
  margin: 0;
  color: #777777;
  font-size: 14px;
  line-height: 1.55;
}


/* =========================================
   Prototype Notice
   ========================================= */

.prototype-note {
  max-width: 1150px;
  margin: 35px auto 0;
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

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .action-grid {
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

  .stat-card,
  .action-card {
    padding: 20px;
  }

}

</style>
