<script lang="ts" setup>

defineProps<{
  backgroundColor?: string
  width?: string
  checkedColor?: string
  borderColor?: string
  modelValue?: boolean
}>()

defineEmits(['update:modelValue'])
</script>

<template>
  <input type="checkbox" class="generic-switch" :checked="modelValue"
    @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)" />
</template>

<style scoped>
.generic-switch {
  position: relative;
  width: v-bind(width);
  aspect-ratio: 16 / 9;
  border-radius: 0.5rem;
  border: 3px solid v-bind('borderColor');
  background-color: v-bind('backgroundColor');
  transition: background-color 0.3s ease;
  outline: none;
  cursor: pointer;
  box-shadow: 0 -5px 0 0 v-bind('borderColor');
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  container-type: inline-size;

  &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 30%;
    transform: translate(-50%, -50%);
    border-radius: 0.5rem;
    height: 40cqw;
    width: 40cqw;
    background-color: white;
    transition: left 0.4s ease;
  }

  &:checked {
    background-color: v-bind('checkedColor');
  }

  &:checked::after {
    left: 70%;
  }

  &:hover {
    opacity: 0.9;
  }
}
</style>