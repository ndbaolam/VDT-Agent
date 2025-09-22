<!-- WelcomeScreen.vue -->
<template>
  <div class="text-center mt-20">
    <div
      class="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-3xl mb-6 shadow-lg shadow-blue-500/20"
    >
      <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
        />
      </svg>
    </div>
    <h1
      class="text-4xl font-bold bg-gradient-to-r from-gray-800 via-blue-600 to-purple-600 bg-clip-text text-transparent mb-3"
    >
      VTNet Chat Assistant
    </h1>
    <p class="text-gray-500 text-lg max-w-md mx-auto leading-relaxed">
      Your intelligent conversation partner. Ask me anything and let's start chatting!
    </p>
  </div>
</template>

<script setup lang="ts">
// No props or logic needed for this component
</script>
