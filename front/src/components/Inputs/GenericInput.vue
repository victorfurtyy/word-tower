<script lang="ts" setup>
defineProps<{
  type?: string
  placeholder?: string
  backgroundColor?: string
  borderColor?: string
  fontSize?: string
  modelValue?: string
}>()

defineEmits(['update:modelValue'])
</script>

<template>
  <input :type="type" :value="modelValue" :placeholder="placeholder"
    @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)" class="generic-input" />

</template>

<style scoped>
@font-face {
  font-family: 'Tomo Bossa Black';
  src: url('@/assets/fonts/tomo_bossa_black.woff') format('woff');
}

.generic-input {
  background-color: v-bind('backgroundColor');
  border: 3px solid v-bind('borderColor');
  padding: .5rem;
  transition: .4s;
  border-radius: .5rem;
  font-family: "Tomo Bossa Black";
  font-size: v-bind('fontSize');

  &:focus {
    outline: none;
  }
}
</style>