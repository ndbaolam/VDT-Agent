<!-- ChatInput.vue -->
<template>
  <div class="relative px-6 py-6 bg-white/80 backdrop-blur-xl border-t border-gray-200/50">
    <div class="max-w-4xl mx-auto">
      <form
        @submit.prevent="$emit('send-message')"
        class="relative flex items-end gap-4 bg-white rounded-3xl shadow-lg shadow-gray-200/60 p-2 border border-gray-200/80 hover:shadow-xl transition-all duration-300"
      >
        <textarea
          :value="input"
          @input="updateInput"
          @keydown="handleKeyDown"
          placeholder="Type your message..."
          class="flex-1 resize-none bg-transparent focus:outline-none placeholder:text-gray-400 px-4 py-3 text-gray-700 leading-relaxed"
          rows="1"
          ref="textareaRef"
        ></textarea>
        
        <!-- Send Button -->
        <SendButton :is-loading="isLoading" :disabled="!input.trim() || isLoading" />
      </form>
      
      <!-- Status Indicator -->
      <StatusIndicator :is-loading="isLoading" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, defineProps, defineEmits } from "vue";
import SendButton from "@/components/SendButton.vue";
import StatusIndicator from "@/components/StatusIndicator.vue";

const props = defineProps<{
  input: string;
  isLoading: boolean;
}>();

const emit = defineEmits<{
  'update:input': [value: string];
  'send-message': [];
}>();

const textareaRef = ref<HTMLTextAreaElement | null>(null);

function updateInput(event: Event) {
  const target = event.target as HTMLTextAreaElement;
  emit('update:input', target.value);
}

function resizeTextarea() {
  if (textareaRef.value) {
    textareaRef.value.style.height = "auto";
    textareaRef.value.style.height = `${Math.min(textareaRef.value.scrollHeight, 160)}px`;
  }
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === "Enter" && !e.shiftKey && !props.isLoading) {
    e.preventDefault();
    emit('send-message');
  }
}

onMounted(() => {
  resizeTextarea();
});

watch(() => props.input, () => {
  resizeTextarea();
});
</script>

<style scoped>
textarea {
  min-height: 1.5rem;
  max-height: 10rem;
}
</style>