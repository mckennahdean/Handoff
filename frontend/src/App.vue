<script setup>
import NavigationBar from './components/NavigationBar.vue'
</script>

<template>
  <!-- Shared navigation appears on every Handoff page -->
  <NavigationBar />

  <!-- Displays the page selected by Vue Router -->
  <RouterView />
</template>
