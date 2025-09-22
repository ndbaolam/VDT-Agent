<!-- ChatSidebar.vue -->
<template>
  <aside class="w-80 bg-gradient-to-b from-slate-50 to-white shadow-xl flex flex-col">
    <!-- Elegant New Chat Button -->
    <div class="p-6 pb-4">
      <button
        @click="$emit('newChat')"
        class="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-medium py-3 px-6 rounded-2xl transition-all duration-300 flex items-center justify-center gap-3 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="1.5"
            d="M12 6v6m0 0v6m0-6h6m-6 0H6"
          />
        </svg>
        New Conversation
      </button>
    </div>

    <!-- Chat History with modern design -->
    <div class="flex-1 overflow-y-auto px-4">
      <!-- Loading State -->
      <div v-if="isLoading && chatHistory.length === 0" class="space-y-3">
        <div v-for="i in 4" :key="i" class="animate-pulse">
          <div class="bg-gradient-to-r from-gray-200 to-gray-100 h-16 rounded-2xl"></div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="chatHistory.length === 0" class="text-center py-12">
        <div
          class="bg-gradient-to-br from-indigo-100 to-purple-100 w-20 h-20 rounded-full mx-auto mb-6 flex items-center justify-center"
        >
          <svg
            class="w-10 h-10 text-indigo-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
        </div>
        <h3 class="text-gray-800 font-medium mb-2">No conversations yet</h3>
        <p class="text-gray-500 text-sm leading-relaxed">
          Start your first conversation to<br />see your chat history here
        </p>
      </div>

      <!-- Chat List -->
      <div v-else class="space-y-2 pb-4">
        <div v-for="chat in chatHistory" :key="chat.thread_id" class="group relative">
          <div
            @click="loadChat(chat.thread_id)"
            class="p-4 rounded-2xl cursor-pointer transition-all duration-300 border border-transparent hover:border-indigo-200 hover:shadow-md backdrop-blur-sm"
            :class="{
              'bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200 shadow-md':
                currentThreadId === chat.thread_id,
              'hover:bg-gradient-to-r hover:from-gray-50 hover:to-slate-50':
                currentThreadId !== chat.thread_id,
            }"
          >
            <!-- Chat Content -->
            <div class="flex items-start gap-3">
              <!-- Chat Icon -->
              <div
                class="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center shadow-sm"
              >
                <svg
                  class="w-5 h-5 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.5"
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                  />
                </svg>
              </div>

              <!-- Chat Details -->
              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between gap-2">
                  <h3
                    class="text-gray-800 font-medium line-clamp-2 text-sm leading-relaxed"
                    :title="chat.title"
                  >
                    {{ chat.title }}
                  </h3>

                  <!-- Delete Button -->
                  <button
                    @click.stop="deleteChat(chat.thread_id)"
                    class="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-50 rounded-lg text-red-400 hover:text-red-500 transition-all duration-200"
                    title="Delete conversation"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="1.5"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>

                <!-- Metadata with beautiful styling -->
                <div class="flex items-center gap-3 mt-2 text-xs">
                  <span
                    v-if="chat.message_count"
                    class="text-indigo-600 bg-indigo-50 px-2 py-1 rounded-lg font-medium"
                  >
                    {{ chat.message_count }} msg{{ chat.message_count !== 1 ? 's' : '' }}
                  </span>
                  <span v-if="chat.last_updated" class="text-gray-500">
                    {{ formatDate(chat.last_updated) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Elegant Footer -->
    <footer
      v-if="chatHistory.length > 0"
      class="p-4 border-t border-gray-100 bg-gradient-to-r from-gray-50 to-slate-50"
    >
      <div class="text-center">
        <span class="text-xs text-gray-500 font-medium">
          {{ chatHistory.length }} conversation{{ chatHistory.length !== 1 ? 's' : '' }} total
        </span>
      </div>
    </footer>
  </aside>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, type PropType } from 'vue'

interface ChatHistoryItem {
  thread_id: string
  title: string
  last_updated?: string
  message_count?: number
}

const props = defineProps({
  chatHistory: {
    type: Array as PropType<ChatHistoryItem[]>,
    required: true,
  },
  currentThreadId: {
    type: String as PropType<string | null>,
    default: null,
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits<{
  loadChat: [threadId: string]
  newChat: []
  deleteChat: [threadId: string]
  refreshHistory: []
}>()

function loadChat(threadId: string) {
  emit('loadChat', threadId)
}

function deleteChat(threadId: string) {
  if (confirm('Are you sure you want to delete this conversation?')) {
    emit('deleteChat', threadId)
  }
}

function formatDate(dateString: string): string {
  if (!dateString) return ''

  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMinutes = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMinutes < 1) {
    return 'Just now'
  } else if (diffMinutes < 60) {
    return `${diffMinutes}m ago`
  } else if (diffHours < 24) {
    return `${diffHours}h ago`
  } else if (diffDays < 7) {
    return `${diffDays}d ago`
  } else {
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    })
  }
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Beautiful custom scrollbar */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: linear-gradient(to bottom, #cbd5e1, #94a3b8);
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(to bottom, #94a3b8, #64748b);
}

/* Smooth animations */
* {
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}

/* Backdrop blur support */
@supports (backdrop-filter: blur(10px)) {
  .backdrop-blur-sm {
    backdrop-filter: blur(4px);
  }
}
</style>
