<!-- Main Chatbot Component -->
<template>
  <main class="flex flex-col w-screen h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50/30">
    <!-- Chat Messages Area -->
    <ChatMessages 
      :messages="messages" 
      :is-loading="isLoading" 
      @render-markdown="renderMarkdown" 
    />
    
    <!-- Input Area -->
    <ChatInput 
      v-model:input="input"
      :is-loading="isLoading"
      @send-message="sendMessage"
    />
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import axios from "axios";
import MarkdownIt from "markdown-it";
import hljs from "highlight.js";
import "highlight.js/styles/github.css";

// Import sub-components
import ChatMessages from "./ChatMessages.vue";
import ChatInput from "./ChatInput.vue";

const input = ref("");
const messages = ref<Array<{ role: string; content: string }>>([]);
const isLoading = ref(false);
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

// Initialize markdown-it
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs bg-gray-50 rounded-xl p-4 border border-gray-200 overflow-x-auto"><code>${
          hljs.highlight(str, { language: lang }).value
        }</code></pre>`;
      } catch (__) {}
    }
    return `<pre class="hljs bg-gray-50 rounded-xl p-4 border border-gray-200 overflow-x-auto"><code>${md.utils.escapeHtml(str)}</code></pre>`;
  },
});

// Render Markdown
function renderMarkdown(text: string) {
  return md.render(text);
}

async function sendMessage() {
  if (!input.value.trim() || isLoading.value) return;
  
  messages.value.push({ role: "user", content: input.value });
  const userMsg = input.value;
  input.value = "";
  
  // Set loading state
  isLoading.value = true;
  
  try {
    const res = await axios.post(`${API_BASE_URL}/chat`, { message: userMsg });
    const data = res.data;
    messages.value.push({
      role: "bot",
      content: data.response || "No response received.",
    });
  } catch (e: any) {
    messages.value.push({
      role: "bot",
      content: "Error: " + (e?.response?.data?.detail || e.message),
    });
  } finally {
    // Clear loading state
    isLoading.value = false;
  }
}
</script>