<template>
  <aside class="w-64 bg-white shadow-md border-r">
    <header class="p-4 border-b bg-gradient-to-r from-blue-600 to-blue-400 text-white">
      <h2 class="text-lg font-semibold">Chat History</h2>
    </header>
    <ul class="p-4 space-y-2">
      <li
        v-for="(history, index) in chatHistory"
        :key="index"
        @click="loadChat(index)"
        class="p-3 rounded-lg cursor-pointer hover:bg-blue-100"
      >
        <span class="text-sm font-medium text-gray-700">Chat {{ index + 1 }}</span>
      </li>
    </ul>
  </aside>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, type PropType } from 'vue'

const props = defineProps({
  chatHistory: {
    type: Array as PropType<Array<Array<{ role: string; content: string }>>>,
    required: true,
  },
})

const emit = defineEmits(['loadChat'])

function loadChat(index: number) {
  emit('loadChat', index)
}
</script>

<style scoped>
/* Add any specific styles for the sidebar here */
</style>
