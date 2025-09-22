<!-- components/AlertBox.vue -->
<template>
  <transition name="fade">
    <div
      v-if="visible"
      class="fixed bottom-6 right-6 z-50 max-w-sm rounded-xl border border-red-200 bg-red-50 p-4 shadow-lg flex items-start gap-3"
    >
      <!-- Message -->
      <div class="flex-1 text-sm text-red-700 leading-relaxed">
        {{ message }}
      </div>

      <!-- Close -->
      <button class="text-red-400 hover:text-red-600 transition" @click="close">✖</button>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, watchEffect } from 'vue'

const props = defineProps<{
  message: string
  duration?: number // ms, auto close
}>()

const visible = ref(true)

function close() {
  visible.value = false
}

watchEffect(() => {
  if (props.duration && visible.value) {
    const timer = setTimeout(() => (visible.value = false), props.duration)
    return () => clearTimeout(timer)
  }
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
