<!-- MessageBubble.vue -->
<template>
  <div
    :class="{
      'ml-auto': message.role === 'user',
      'mr-auto': message.role === 'bot',
    }"
    class="flex items-start gap-3 max-w-[85%] group"
  >
    <!-- Bot Avatar -->
    <UserAvatar v-if="message.role === 'bot'" type="bot" />

    <!-- Message Content -->
    <div
      :class="{
        'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/25':
          message.role === 'user',
        'bg-white shadow-md shadow-gray-200/60 text-gray-800 border border-gray-100/80':
          message.role === 'bot',
      }"
      class="rounded-3xl px-5 py-4 transform transition-all duration-200 hover:scale-[1.02] hover:shadow-xl"
    >
      <div
        v-if="message.role === 'bot'"
        v-html="message.renderedContent || message.content"
        class="prose prose-sm max-w-none prose-blue prose-headings:text-gray-800 prose-p:text-gray-700 prose-code:bg-gray-100 prose-code:px-2 prose-code:py-1 prose-code:rounded-lg prose-pre:bg-gray-50 prose-pre:border prose-pre:border-gray-200"
      ></div>
      <div v-else class="text-white font-medium">{{ message.content }}</div>

      <!-- Approval Buttons for Interrupts -->
      <div
        v-if="message.requires_approval && message.interrupt_id && message.thread_id"
        class="mt-4 pt-3 border-t border-gray-200"
      >
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm text-gray-600 font-medium">Action requires approval:</span>
          <div class="flex gap-2">
            <button
              @click="$emit('approve-interrupt', message.interrupt_id!, message.thread_id!, true)"
              class="px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white text-sm font-medium rounded-xl hover:from-green-600 hover:to-green-700 transition-all duration-200 shadow-md shadow-green-500/25 hover:shadow-lg hover:shadow-green-500/30 transform hover:scale-105"
            >
              ✓ Approve
            </button>
            <button
              @click="$emit('approve-interrupt', message.interrupt_id!, message.thread_id!, false)"
              class="px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 text-white text-sm font-medium rounded-xl hover:from-red-600 hover:to-red-700 transition-all duration-200 shadow-md shadow-red-500/25 hover:shadow-lg hover:shadow-red-500/30 transform hover:scale-105"
            >
              ✗ Deny
            </button>
          </div>
        </div>

        <!-- Show action details if available -->
        <div v-if="message.interrupt_action" class="mt-3 p-3 bg-gray-50 rounded-xl">
          <div class="text-xs text-gray-500 uppercase tracking-wide font-semibold mb-1">
            Action Details:
          </div>
          <pre class="text-sm text-gray-700 whitespace-pre-wrap">{{
            JSON.stringify(message.interrupt_action, null, 2)
          }}</pre>
        </div>
      </div>
    </div>

    <!-- User Avatar -->
    <UserAvatar v-if="message.role === 'user'" type="user" />
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import UserAvatar from '@/components/UserAvatar.vue'

interface Message {
  role: string
  content: string
  interrupt_id?: string
  interrupt_description?: string
  interrupt_action?: any
  requires_approval?: boolean
  thread_id?: string
  renderedContent?: string
}

defineProps<{
  message: Message
}>()

defineEmits<{
  'render-markdown': [text: string]
  'approve-interrupt': [interruptId: string, threadId: string, approved: boolean]
}>()
</script>

<style scoped>
/* Prose styling for markdown content */
.prose {
  color: inherit;
}

.prose h1,
.prose h2,
.prose h3,
.prose h4,
.prose h5,
.prose h6 {
  color: #1f2937;
  font-weight: 600;
}

.prose p {
  color: #374151;
  line-height: 1.6;
}

.prose code {
  background-color: #f3f4f6;
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 0.875em;
  font-weight: 500;
}

.prose pre {
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem;
  overflow-x: auto;
  margin: 1rem 0;
}

.prose pre code {
  background: transparent;
  padding: 0;
  border-radius: 0;
}
</style>
