<!-- Main Chatbot Component ChatBox.vue-->
<template>
  <div class="flex h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50/30">
    <!-- Sidebar -->
    <ChatSidebar 
      :chat-history="chatHistory"
      :current-thread-id="currentThreadId"
      :is-loading="sidebarLoading"
      @load-chat="loadChat"
      @new-chat="startNewChat"
      @delete-chat="deleteChat"
      @refresh-history="loadChatHistory"
    />
    
    <!-- Main Chat Area -->
    <main class="flex flex-col flex-1 relative">
      <!-- Chat Messages Area with proper scrolling -->
      <div class="flex-1 overflow-y-auto overflow-x-hidden" style="padding-bottom: 120px;">
        <ChatMessages
          :messages="messages"
          :is-loading="isLoading"
          @render-markdown="renderMarkdown"
          @approve-interrupt="handleInterruptApproval"
          class="min-h-full"
        />
      </div>
      
      <!-- Floating Input Area -->
      <ChatInput 
        v-model:input="input" 
        :is-loading="isLoading" 
        @send-message="sendMessage" 
      />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

// Import sub-components
import ChatMessages from './ChatMessages.vue'
import ChatInput from './ChatInput.vue'
import ChatSidebar from './ChatSidebar.vue'

interface ChatMessage {
  role: string
  content: string
  interrupt_id?: string
  interrupt_description?: string
  interrupt_action?: any
  requires_approval?: boolean
  thread_id?: string
}

interface ChatHistoryItem {
  thread_id: string
  title: string
  last_updated?: string
  message_count?: number
}

const input = ref('')
const messages = ref<ChatMessage[]>([])
const isLoading = ref(false)
const sidebarLoading = ref(false)
const currentThreadId = ref<string | null>(null)
const chatHistory = ref<ChatHistoryItem[]>([])

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

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
        }</code></pre>`
      } catch (__) {}
    }
    return `<pre class="hljs bg-gray-50 rounded-xl p-4 border border-gray-200 overflow-x-auto"><code>${md.utils.escapeHtml(str)}</code></pre>`
  },
})

// Render Markdown
function renderMarkdown(text: string) {
  return md.render(text)
}

// Load chat history from API
async function loadChatHistory() {
  try {
    sidebarLoading.value = true
    const response = await axios.get(`${API_BASE_URL}/chat-history`)
    chatHistory.value = response.data.chat_history || []
  } catch (error) {
    console.error('Error loading chat history:', error)
    chatHistory.value = []
  } finally {
    sidebarLoading.value = false
  }
}

// Load a specific chat thread
async function loadChat(threadId: string) {
  try {
    isLoading.value = true
    
    // Get thread status and messages
    const response = await axios.get(`${API_BASE_URL}/threads/${threadId}`)
    const threadData = response.data
    
    // Set current thread
    currentThreadId.value = threadId
    
    // Convert thread messages to chat messages format
    messages.value = threadData.messages?.map((msg: any) => ({
      role: msg.role || (msg.type === 'human' ? 'user' : 'bot'),
      content: msg.content || msg.text || '',
      ...msg
    })) || []
    
  } catch (error) {
    console.error('Error loading chat:', error)
    messages.value = [{
      role: 'bot',
      content: 'Error loading chat history. Please try again.'
    }]
  } finally {
    isLoading.value = false
  }
}

// Start a new chat
function startNewChat() {
  currentThreadId.value = null
  messages.value = []
  input.value = ''
}

// Delete a chat
async function deleteChat(threadId: string) {
  try {
    await axios.delete(`${API_BASE_URL}/threads/${threadId}`)
    
    // Remove from chat history
    chatHistory.value = chatHistory.value.filter(chat => chat.thread_id !== threadId)
    
    // If it's the current chat, start a new one
    if (currentThreadId.value === threadId) {
      startNewChat()
    }
  } catch (error) {
    console.error('Error deleting chat:', error)
  }
}

// Send message function
async function sendMessage() {
  if (!input.value.trim() || isLoading.value) return

  messages.value.push({ role: 'user', content: input.value })
  const userMsg = input.value
  input.value = ''

  // Set loading state
  isLoading.value = true

  try {
    const res = await axios.post(`${API_BASE_URL}/chat`, {
      message: userMsg,
      thread_id: currentThreadId.value,
    })

    const data = res.data

    // Update current thread ID
    currentThreadId.value = data.thread_id

    if (data.requires_approval) {
      // Handle interrupt - show approval message
      messages.value.push({
        role: 'bot',
        content: data.interrupt_description || 'Action requires approval',
        interrupt_id: data.interrupt_id,
        interrupt_description: data.interrupt_description,
        interrupt_action: data.interrupt_action,
        requires_approval: true,
        thread_id: data.thread_id,
      })
    } else {
      // Normal response
      messages.value.push({
        role: 'bot',
        content: data.response || 'No response received.',
      })
    }

    // Refresh chat history if this is a new thread
    if (data.thread_id && !chatHistory.value.find(chat => chat.thread_id === data.thread_id)) {
      await loadChatHistory()
    }

  } catch (e: any) {
    messages.value.push({
      role: 'bot',
      content: 'Error: ' + (e?.response?.data?.detail || e.message),
    })
  } finally {
    // Clear loading state
    isLoading.value = false
  }
}

// Handle interrupt approval
async function handleInterruptApproval(interruptId: string, threadId: string, approved: boolean) {
  isLoading.value = true

  try {
    const res = await axios.post(`${API_BASE_URL}/interrupt/approve`, {
      interrupt_id: interruptId,
      thread_id: threadId,
      approved: approved,
    })

    const data = res.data

    // Add the resolution response
    messages.value.push({
      role: 'bot',
      content: data.response || (approved ? 'Action approved and completed.' : 'Action denied.'),
    })
  } catch (e: any) {
    messages.value.push({
      role: 'bot',
      content: 'Error resolving interrupt: ' + (e?.response?.data?.detail || e.message),
    })
  } finally {
    isLoading.value = false
  }
}

// Load chat history on component mount
onMounted(() => {
  loadChatHistory()
})
</script>