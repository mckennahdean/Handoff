<template>
  <nav class="navigation">
    <!-- Handoff brand and home link -->
    <RouterLink to="/" class="brand">
      <span class="brand-mark">H</span>
      <span>Handoff</span>
    </RouterLink>

    <div class="nav-links">
      <!-- Owner pages -->
      <RouterLink to="/procedures">Procedures</RouterLink>
      <RouterLink to="/gaps">Documentation Gaps</RouterLink>

      <!-- Employee page -->
      <RouterLink to="/query">Ask Handoff</RouterLink>
    </div>
  </nav>
</template>

<style scoped>
.navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 30px;
  background: #ffffff;
  border-bottom: 1px solid #e4ddd7;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #263238;
  text-decoration: none;
  font-size: 21px;
  font-weight: 700;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: #b65f32;
  color: white;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 28px;
}

.nav-links a {
  color: #53646a;
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
}

.nav-links a:hover {
  color: #b65f32;
}

.nav-links a.router-link-active {
  color: #b65f32;
  font-weight: 700;
}

@media (max-width: 700px) {
  .navigation {
    flex-direction: column;
    gap: 15px;
    padding: 15px;
  }

  .nav-links {
    gap: 18px;
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>
