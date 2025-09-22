<!-- ChatInput.vue -->
<template>
  <!-- Floating Input Container -->
  <div class="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50 w-full max-w-4xl px-6">
    <form
      @submit.prevent="$emit('send-message')"
      class="relative flex items-end gap-3 bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl shadow-black/10 p-3 border border-white/20 hover:shadow-2xl hover:shadow-black/15 transition-all duration-300"
    >
      <!-- Textarea -->
      <textarea
        :value="input"
        @input="updateInput"
        @keydown="handleKeyDown"
        placeholder="Type your message..."
        class="flex-1 resize-none bg-transparent focus:outline-none placeholder:text-gray-400 px-4 py-3 text-gray-700 leading-relaxed min-h-[48px] max-h-[160px]"
        rows="1"
        ref="textareaRef"
      ></textarea>
      
      <!-- Action Buttons -->
      <div class="flex items-center gap-2">
        <!-- Upload Button -->
        <label
          class="flex items-center justify-center w-10 h-10 rounded-full bg-gray-100/80 hover:bg-gray-200/80 transition cursor-pointer shadow-sm backdrop-blur-sm"
        >
          <input type="file" accept=".txt" class="hidden" @change="handleFileUpload" />
          📎
        </label>
        
        <!-- Send Button -->
        <SendButton :is-loading="isLoading" :disabled="!input.trim() || isLoading" />
      </div>
    </form>
    
    <!-- Status Indicator (positioned above the input) -->
    <div class="absolute -top-12 left-1/2 transform -translate-x-1/2">
      <StatusIndicator :is-loading="isLoading" />
    </div>
    
    <!-- Custom Alert (positioned above the input) -->
    <div class="absolute -top-20 left-1/2 transform -translate-x-1/2 w-full max-w-sm">
      <AlertBox
        v-if="alertMessage"
        :message="alertMessage"
        :duration="3000"
        @close="alertMessage = ''"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, defineProps, defineEmits } from 'vue'
import SendButton from '@/components/SendButton.vue'
import StatusIndicator from '@/components/StatusIndicator.vue'
import AlertBox from '@/components/AlertBox.vue'

const props = defineProps<{
  input: string
  isLoading: boolean
}>()

const emit = defineEmits<{
  'update:input': [value: string]
  'send-message': []
}>()

const textareaRef = ref<HTMLTextAreaElement | null>(null)
const alertMessage = ref('')

function updateInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:input', target.value)
}

function resizeTextarea() {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = `${Math.min(textareaRef.value.scrollHeight, 160)}px`
  }
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey && !props.isLoading) {
    e.preventDefault()
    emit('send-message')
  }
}

function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return
  
  if (file.type !== 'text/plain') {
    alertMessage.value = '❌ Only .txt files are supported.'
    return
  }
  
  const reader = new FileReader()
  reader.onload = () => {
    emit('update:input', reader.result as string)
  }
  reader.readAsText(file)
}

onMounted(() => {
  resizeTextarea()
})

watch(
  () => props.input,
  () => {
    resizeTextarea()
  },
)
</script>