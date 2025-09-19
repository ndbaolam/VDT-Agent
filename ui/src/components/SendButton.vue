<!-- SendButton.vue -->
<template>
  <button
    type="submit"
    :disabled="disabled"
    class="flex-shrink-0 bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-2xl p-3 hover:from-blue-600 hover:to-blue-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 transform hover:scale-105 disabled:hover:scale-100 disabled:hover:shadow-lg"
  >
    <!-- Send Icon -->
    <svg
      v-if="!isLoading"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      stroke-width="2"
      stroke="currentColor"
      class="w-5 h-5"
    >
      <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
    </svg>
    
    <!-- Loading Spinner -->
    <svg
      v-else
      class="w-5 h-5 animate-spin"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        class="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="4"
      ></circle>
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      ></path>
    </svg>
  </button>
</template>

<script setup lang="ts">
import { defineProps } from "vue";

defineProps<{
  isLoading: boolean;
  disabled: boolean;
}>();
</script>