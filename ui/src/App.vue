<!-- App.vue -->
<script setup lang="ts">
import ChatBox from './components/ChatBox.vue'
</script>

<template>
  <div id="app" class="w-full h-screen overflow-hidden">
    <ChatBox />
  </div>
</template>

<style scoped>
/* Ensure the app takes full viewport */
#app {
  min-height: 100vh;
  min-width: 100vw;
}

/* Global styles for the chat application */
:global(body) {
  margin: 0;
  padding: 0;
  font-family:
    'Inter',
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    Roboto,
    sans-serif;
}

:global(html) {
  height: 100%;
  margin: 0;
  padding: 0;
}

/* Smooth transitions for all interactive elements */
:global(*) {
  box-sizing: border-box;
}

:global(button) {
  font-family: inherit;
}

/* Custom scrollbar styles */
:global(.custom-scrollbar::-webkit-scrollbar) {
  width: 6px;
}

:global(.custom-scrollbar::-webkit-scrollbar-track) {
  background: transparent;
}

:global(.custom-scrollbar::-webkit-scrollbar-thumb) {
  background-color: #cbd5e0;
  border-radius: 3px;
}

:global(.custom-scrollbar::-webkit-scrollbar-thumb:hover) {
  background-color: #a0aec0;
}
</style>
