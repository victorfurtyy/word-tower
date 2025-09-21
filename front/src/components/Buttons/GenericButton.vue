<script lang="ts" setup>

defineProps<{
  backgroundColor?: string
  borderColor?: string
  aspectRatio?: string | number
  fontSize?: string
  handleClick?: (event: MouseEvent) => void
}>()
</script>

<template>
  <button class="generic-button" @click="handleClick">
    <slot></slot>
  </button>
</template>

<style scoped>
@font-face {
  font-family: 'Tomo Bossa Black';
  src: url('@/assets/fonts/tomo_bossa_black.woff') format('woff');
}

.generic-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background-color: v-bind('backgroundColor');
  border: 5px solid v-bind('borderColor');
  border-radius: .5rem;
  aspect-ratio: v-bind('aspectRatio');
  transition: .4s;
  box-shadow: 0 8px 0 0 v-bind('borderColor');
  cursor: pointer;
  font-family: "Tomo Bossa Black";
  font-size: v-bind('fontSize');
  white-space: nowrap;
  color: #502405;
  width: 100%;

  &:hover {
    transform: translateY(8px);
    box-shadow: 0 0 0 0 v-bind('borderColor');
  }
}
</style>