<script lang="ts" setup>
import { ref, onMounted } from 'vue'

const props = defineProps<{
  duration?: number
  delay?: number
}>()

const showContent = ref(false)

onMounted(() => {
  setTimeout(() => {
    showContent.value = true
  }, props.delay || 100)
})
</script>

<template>
  <div class="generic-overlay" :class="{ 'fade-out': showContent }" :style="{
    transitionDuration: `${props.duration || 2}s`
  }"></div>
</template>

<style scoped>
.generic-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: black;
  z-index: 10;
  opacity: 1;
  transition-property: opacity;
  transition-timing-function: ease-out;
  pointer-events: none;

  &.fade-out {
    opacity: 0;
  }
}
</style>