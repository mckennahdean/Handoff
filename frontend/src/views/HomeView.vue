<template>
  <main class="home">
    <!-- Main introduction to the Handoff platform -->
    <section class="hero">
      <p class="eyebrow">Business Knowledge Platform</p>

      <h1>Handoff</h1>

      <p class="tagline">
        Turn business procedures into reliable, searchable knowledge.
      </p>

      <p class="description">
        Capture procedures, review AI-generated documentation, and give
        employees grounded answers based on approved procedures.
      </p>
    </section>

    <!-- Main areas of the application -->
    <section class="options">
      <!-- Owner tools -->
      <div class="option-card">
        <!-- Document/checkmark icon represents procedure management -->
        <div class="card-icon" aria-hidden="true">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
          >
            <path d="M6 3h8l4 4v14H6V3z" />
            <path d="M14 3v5h5" />
            <path d="m9 14 2 2 4-4" />
          </svg>
        </div>

        <h2>Owner</h2>

        <p>
          Manage procedures, review documentation, and identify knowledge gaps.
        </p>

        <!-- Main owner actions -->
        <div class="actions">
          <RouterLink to="/procedures" class="button">
            View Procedures
          </RouterLink>

          <RouterLink to="/gaps" class="button secondary">
            Knowledge Gaps
          </RouterLink>
        </div>
      </div>

      <!-- Employee tools -->
      <div class="option-card">
        <!-- Chat/question icon represents employee questions -->
        <div class="card-icon" aria-hidden="true">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
          >
            <path
              d="M20 11.5a7.5 7.5 0 0 1-8 7.5 8.5 8.5 0 0 1-3.5-.8L4 20l1.3-3.5A7.4 7.4 0 0 1 4 12c0-4.1 3.6-7.5 8-7.5s8 3.1 8 7z"
            />
            <path d="M9.8 10a2.2 2.2 0 1 1 3.9 1.4c-.8.8-1.7 1.1-1.7 2.1" />
            <path d="M12 16h.01" />
          </svg>
        </div>

        <h2>Employee</h2>

        <p>
          Ask questions and receive answers based on approved business
          procedures.
        </p>

        <!-- Main employee action -->
        <RouterLink to="/query" class="button">
          Ask a Question
        </RouterLink>
      </div>
    </section>
  </main>
</template>

<style scoped>
.home {
  max-width: 1100px;
  margin: 0 auto;
  padding: 70px 30px 80px;
}

/* Introductory section */
.hero {
  max-width: 800px;
  margin: 0 auto 60px;
  text-align: center;
}

.eyebrow {
  margin: 0 0 12px;
  color: #b65f32;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}

.hero h1 {
  margin: 0 0 18px;
  color: #263238;
  font-size: 56px;
  line-height: 1.1;
}

.tagline {
  margin: 0 auto 18px;
  color: #39484e;
  font-size: 25px;
  line-height: 1.4;
}

.description {
  max-width: 700px;
  margin: 0 auto;
  color: #68747a;
  font-size: 17px;
  line-height: 1.7;
}

/* Owner and employee cards */
.options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 28px;
}

.option-card {
  padding: 35px;
  background: #ffffff;
  border: 1px solid #e4ddd7;
  border-radius: 14px;
  box-shadow: 0 4px 14px rgba(60, 45, 35, 0.06);
}

.card-icon {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  margin-bottom: 22px;
  border-radius: 10px;
  background: #f3e3d8;
  color: #914923;
}

.card-icon svg {
  width: 24px;
  height: 24px;
}

.option-card h2 {
  margin: 0 0 12px;
  color: #263238;
  font-size: 26px;
}

.option-card p {
  margin: 0 0 25px;
  color: #68747a;
  font-size: 16px;
  line-height: 1.6;
}

/* Primary and secondary actions */
.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.button {
  display: inline-block;
  padding: 11px 20px;
  border-radius: 8px;
  background: #b65f32;
  color: #ffffff;
  text-decoration: none;
  font-weight: 600;
  transition:
    background-color 0.2s ease,
    transform 0.15s ease,
    box-shadow 0.2s ease;
}

.button:hover {
  background: #914923;
  color: #ffffff;
  box-shadow: 0 3px 8px rgba(80, 45, 30, 0.18);
  transform: translateY(-1px);
}

.button.secondary {
  background: #f3e3d8;
  color: #914923;
}

.button.secondary:hover {
  background: #ead4c6;
  color: #914923;
}

/* Responsive layout for smaller screens */
@media (max-width: 700px) {
  .home {
    padding: 45px 20px 60px;
  }

  .hero {
    margin-bottom: 40px;
  }

  .hero h1 {
    font-size: 44px;
  }

  .tagline {
    font-size: 21px;
  }

  .options {
    grid-template-columns: 1fr;
  }

  .option-card {
    padding: 28px;
  }

  .actions {
    flex-direction: column;
  }

  .button {
    text-align: center;
  }
}
</style>
