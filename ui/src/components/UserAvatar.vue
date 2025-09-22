<!-- UserAvatar.vue -->
<template>
  <div
    :class="{
      'bg-gradient-to-br from-blue-500 to-purple-600 shadow-blue-500/20': type === 'bot',
      'bg-gradient-to-br from-emerald-400 to-blue-500 shadow-emerald-500/20': type === 'user',
    }"
    class="flex-shrink-0 w-10 h-10 rounded-2xl flex items-center justify-center shadow-lg"
  >
    <!-- Bot Icon -->
    <svg
      v-if="type === 'bot'"
      class="w-5 h-5 text-white"
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

    <!-- User Icon -->
    <svg v-else class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
      />
    </svg>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'

defineProps<{
  type: 'bot' | 'user'
}>()
</script>
