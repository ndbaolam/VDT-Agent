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
        :message="{
          ...msg,
          renderedContent: renderMarkdown(msg.content),
        }"
        @render-markdown="(text) => $emit('render-markdown', text)"
        @approve-interrupt="
          (interruptId, threadId, approved) =>
            $emit('approve-interrupt', interruptId, threadId, approved)
        "
      />

      <!-- Loading Indicator -->
      <LoadingIndicator v-if="isLoading" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import WelcomeScreen from './WelcomeScreen.vue'
import MessageBubble from './MessageBubble.vue'
import LoadingIndicator from './LoadingIndicator.vue'
import { marked } from 'marked'

interface Message {
  role: string
  content: string
  interrupt_id?: string
  interrupt_description?: string
  interrupt_action?: any
  requires_approval?: boolean
  thread_id?: string
}

defineProps<{
  messages: Message[]
  isLoading: boolean
}>()

defineEmits<{
  'render-markdown': [text: string]
  'approve-interrupt': [interruptId: string, threadId: string, approved: boolean]
}>()

function renderMarkdown(text: string) {
  return marked.parse(text)
}
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
