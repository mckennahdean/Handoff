<script setup>
import { useRoute } from 'vue-router'
import NavigationBar from './components/NavigationBar.vue'

// Gets the current page/route so we can control which pages show navigation
const route = useRoute()
</script>

<template>
  <!-- Shared navigation appears on all Handoff pages except the login screen -->
  <NavigationBar v-if="route.name !== 'login'" />

  <!-- Displays the page selected by Vue Router -->
  <RouterView />
</template>
