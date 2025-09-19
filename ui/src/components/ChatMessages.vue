<!-- ChatMessages.vue -->
<template>
  <div class="flex-1 overflow-y-auto px-6 py-8">
    <!-- Welcome Screen -->
    <WelcomeScreen v-if="messages.length === 0" />
    
    <!-- Messages Container -->
    <div v-else class="flex flex-col gap-6 max-w-4xl mx-auto">
      <!-- Message Bubbles -->
      <MessageBubble
        v-for="(msg, idx) in messages"
        :key="idx"
        :message="msg"
        @render-markdown="(text) => $emit('render-markdown', text)"
      />
      
      <!-- Loading Indicator -->
      <LoadingIndicator v-if="isLoading" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from "vue";
import WelcomeScreen from "./WelcomeScreen.vue";
import MessageBubble from "./MessageBubble.vue";
import LoadingIndicator from "./LoadingIndicator.vue";

interface Message {
  role: string;
  content: string;
}

defineProps<{
  messages: Message[];
  isLoading: boolean;
}>();

defineEmits<{
  'render-markdown': [text: string];
}>();
</script>

<style scoped>
/* Custom scrollbar */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>