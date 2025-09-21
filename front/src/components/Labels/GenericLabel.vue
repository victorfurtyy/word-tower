<script lang="ts" setup>
defineProps<{
  position?: 'start' | 'center' | 'end'
  fontSize?: string
  color?: string
}>()
</script>

<template>
  <label class="generic-label" :class="`text-${position || 'start'}`" :style="{
    fontSize: fontSize || '1rem',
    color: color || '#333'
  }">
    <slot />
  </label>
</template>

<style scoped>
@font-face {
  font-family: 'TOMO Bossa';
  src: url('@/assets/fonts/tomo_bossa_black.woff') format('woff');
  font-display: swap;
}

.generic-label {
  font-family: 'TOMO Bossa', Arial, sans-serif;
  font-weight: normal;
  line-height: 1.2;
  display: block;
  margin: 0;
  padding: 0;
}

.text-start {
  text-align: left;
}

.text-center {
  text-align: center;
}

.text-end {
  text-align: right;
}
</style>