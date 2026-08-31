<template>
  <main class="gaps">
    <!-- Page heading -->
    <section class="page-header">
      <div>
        <p class="eyebrow">Owner Workspace</p>
        <h1>Documentation Gaps</h1>
        <p>
          Review questions that could not be answered from approved procedures.
        </p>
      </div>

      <div class="gap-count">
        <span>Open Gaps</span>
        <strong>{{ gaps.length }}</strong>
      </div>
    </section>

    <!-- Documentation gap list -->
    <section v-if="gaps.length > 0" class="gap-list">
      <article
        v-for="gap in gaps"
        :key="gap.id"
        class="gap-card"
      >
        <div class="gap-icon" aria-hidden="true">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
          >
            <path d="M12 17h.01" />
            <path d="M9.5 9a2.5 2.5 0 1 1 4.4 1.6c-.8.8-1.9 1.1-1.9 2.4" />
            <circle cx="12" cy="12" r="9" />
          </svg>
        </div>

        <div class="gap-content">
          <div class="gap-title-row">
            <h2>{{ gap.question }}</h2>

            <span class="frequency">
              {{ gap.frequencyCount }}
              {{ gap.frequencyCount === 1 ? 'time' : 'times' }}
            </span>
          </div>

          <p class="gap-date">
            First reported: {{ gap.timestamp }}
          </p>

          <p class="gap-description">
            This question could not be answered using the currently approved
            procedures and may need to be documented.
          </p>
        </div>

        <!-- Future action for documenting the gap -->
        <button class="review-button" type="button">
          Review Gap
        </button>
      </article>
    </section>

    <!-- Message shown when there are no gaps -->
    <section v-else class="empty-state">
      <div class="empty-icon" aria-hidden="true">✓</div>
      <h2>No Documentation Gaps</h2>
      <p>
        All employee questions are currently covered by approved procedures.
      </p>
    </section>

    <!-- Return to procedures -->
    <div class="bottom-action">
      <RouterLink to="/procedures" class="secondary-link">
        ← Back to Procedures
      </RouterLink>
    </div>
  </main>
</template>

<script setup>
import { ref } from 'vue'

// Temporary data used while the FastAPI endpoint is being developed.
// This will later be replaced with data from GET /api/gaps.
const gaps = ref([
  {
    id: 1,
    question: 'What should be done when a customer does not have a receipt?',
    timestamp: 'August 30, 2026',
    frequencyCount: 5
  },
  {
    id: 2,
    question: 'How should damaged items be handled?',
    timestamp: 'August 29, 2026',
    frequencyCount: 3
  }
])
</script>

<style scoped>
.gaps {
  width: min(1100px, calc(100% - 40px));
  margin: 0 auto;
  padding: 55px 0 70px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 30px;
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
  line-height: 1.5;
}

/* Number of currently open documentation gaps */
.gap-count {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 18px;
  background: #f3e3d8;
  border-radius: 10px;
  color: #914923;
}

.gap-count span {
  font-size: 14px;
  font-weight: 600;
}

.gap-count strong {
  font-size: 22px;
}

/* Documentation gap cards */
.gap-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.gap-card {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 25px;
  background: #ffffff;
  border: 1px solid #e4ddd7;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(60, 45, 35, 0.04);
}

.gap-icon {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: #f3e3d8;
  color: #914923;
}

.gap-icon svg {
  width: 23px;
  height: 23px;
}

.gap-content {
  flex: 1;
  min-width: 0;
}

.gap-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.gap-title-row h2 {
  margin: 0;
  color: #263238;
  font-size: 18px;
  line-height: 1.4;
}

.frequency {
  padding: 4px 9px;
  border-radius: 20px;
  background: #f5f1ed;
  color: #68747a;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.gap-date {
  margin: 7px 0 0;
  color: #68747a;
  font-size: 13px;
}

.gap-description {
  margin: 10px 0 0;
  color: #68747a;
  font-size: 14px;
  line-height: 1.5;
}

/* Future gap review action */
.review-button {
  flex-shrink: 0;
  white-space: nowrap;
}

/* Empty state */
.empty-state {
  padding: 60px 30px;
  background: #ffffff;
  border: 1px solid #e4ddd7;
  border-radius: 12px;
  text-align: center;
}

.empty-icon {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  margin: 0 auto 18px;
  border-radius: 50%;
  background: #e7f1eb;
  color: #35634a;
  font-size: 22px;
  font-weight: 700;
}

.empty-state h2 {
  margin: 0 0 8px;
  color: #263238;
}

.empty-state p {
  margin: 0;
  color: #68747a;
}

/* Return link */
.bottom-action {
  margin-top: 28px;
}

.secondary-link {
  color: #b65f32;
  font-weight: 600;
  text-decoration: none;
}

.secondary-link:hover {
  color: #914923;
}

@media (max-width: 700px) {
  .gaps {
    width: min(100% - 30px, 1100px);
    padding: 40px 0 55px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .gap-card {
    align-items: flex-start;
    flex-direction: column;
  }

  .review-button {
    width: 100%;
  }
}
</style>
