<!-- LoadingIndicator.vue -->
<template>
  <div class="flex items-start gap-3 max-w-[85%] mr-auto">
    <!-- Bot Avatar with Pulse Animation -->
    <div
      class="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/20"
    >
      <svg
        class="w-5 h-5 text-white animate-pulse"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
        />
      </svg>
    </div>

    <!-- Loading Message Bubble -->
    <div
      class="bg-white shadow-md shadow-gray-200/60 text-gray-800 border border-gray-100/80 rounded-3xl px-5 py-4 flex items-center gap-3"
    >
      <!-- Bouncing Dots -->
      <div class="flex space-x-1">
        <div
          class="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
          style="animation-delay: 0ms"
        ></div>
        <div
          class="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
          style="animation-delay: 150ms"
        ></div>
        <div
          class="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
          style="animation-delay: 300ms"
        ></div>
      </div>

      <!-- Loading Text -->
      <span class="text-gray-500 text-sm font-medium">AI is thinking...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
// No props or logic needed for this component
</script>
