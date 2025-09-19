<!-- MessageBubble.vue -->
<template>
  <div
    :class="{
      'ml-auto': message.role === 'user',
      'mr-auto': message.role === 'bot'
    }"
    class="flex items-start gap-3 max-w-[85%] group"
  >
    <!-- Bot Avatar -->
    <UserAvatar v-if="message.role === 'bot'" type="bot" />
    
    <!-- Message Content -->
    <div
      :class="{
        'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/25': message.role === 'user',
        'bg-white shadow-md shadow-gray-200/60 text-gray-800 border border-gray-100/80': message.role === 'bot'
      }"
      class="rounded-3xl px-5 py-4 transform transition-all duration-200 hover:scale-[1.02] hover:shadow-xl"
    >
      <div 
        v-if="message.role === 'bot'" 
        v-html="renderedContent" 
        class="prose prose-sm max-w-none prose-blue prose-headings:text-gray-800 prose-p:text-gray-700 prose-code:bg-gray-100 prose-code:px-2 prose-code:py-1 prose-code:rounded-lg prose-pre:bg-gray-50 prose-pre:border prose-pre:border-gray-200"
      ></div>
      <div v-else class="text-white font-medium">{{ message.content }}</div>
    </div>
    
    <!-- User Avatar -->
    <UserAvatar v-if="message.role === 'user'" type="user" />
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, computed } from "vue";
import UserAvatar from "@/components/UserAvatar.vue";
import { marked } from 'marked';

interface Message {
  role: string;
  content: string;
}

const props = defineProps<{
  message: Message;
}>();

defineEmits<{
  'render-markdown': [text: string];
}>();

const renderedContent = computed(() => {
  if (props.message.role === 'bot') {
    return marked(props.message.content);
  }
  return props.message.content;
});
</script>

<style scoped>
/* Prose styling for markdown content */
.prose {
  color: inherit;
}

.prose h1, .prose h2, .prose h3, .prose h4, .prose h5, .prose h6 {
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