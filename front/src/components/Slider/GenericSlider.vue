<script lang="ts" setup>
import { computed } from 'vue'

const props = defineProps<{
  modelValue?: number
  min?: number
  max?: number
  step?: number
  values?: string[]
  backgroundColor?: string
  borderColor?: string
  thumbColor?: string
  trackColor?: string
  trackActiveColor?: string
  fontSize?: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

const currentDisplayValue = computed(() => {
  if (props.values && props.values.length > 0) {
    const index = props.modelValue || 0
    return props.values[index] || props.values[0]
  }
  return props.modelValue || 0
})

const sliderMin = computed(() => {
  if (props.values && props.values.length > 0) {
    return 0
  }
  return props.min || 0
})

const sliderMax = computed(() => {
  if (props.values && props.values.length > 0) {
    return props.values.length - 1
  }
  return props.max || 100
})

const sliderStep = computed(() => {
  if (props.values && props.values.length > 0) {
    return 1
  }
  return props.step || 1
})
</script>

<template>
  <div class="slider-container">
    <input type="range" class="generic-slider" :value="modelValue || 0" :min="sliderMin" :max="sliderMax"
      :step="sliderStep" :disabled="disabled"
      @input="emit('update:modelValue', Number(($event.target as HTMLInputElement).value))" />
    <div class="slider-value">{{ currentDisplayValue }}</div>
  </div>
</template>

<style scoped>
@font-face {
  font-family: 'Tomo Bossa Black';
  src: url('@/assets/fonts/tomo_bossa_black.woff') format('woff');
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 1rem;
  width: 100%;
}

.generic-slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 0.8rem;
  background: v-bind('trackColor || "#E0E0E0"');
  border: 0.2rem solid v-bind('borderColor || "#96550B"');
  border-radius: 0.5rem;
  outline: none;
  transition: all 0.3s ease;
  cursor: pointer;
  font-family: 'Tomo Bossa Black', Arial, sans-serif;

  &:hover {
    transform: scale(1.02);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }

  /* Webkit browsers (Chrome, Safari, Edge) */
  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 1.5rem;
    height: 1.5rem;
    background: v-bind('thumbColor || "#FFB107"');
    border: 0.2rem solid v-bind('borderColor || "#96550B"');
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 0.2rem 0 0 v-bind('borderColor || "#96550B"');

    &:hover {
      transform: scale(1.1);
      box-shadow: 0 0.3rem 0 0 v-bind('borderColor || "#96550B"');
    }

    &:active {
      transform: scale(0.95);
      box-shadow: 0 0.1rem 0 0 v-bind('borderColor || "#96550B"');
    }
  }

  /* Firefox */
  &::-moz-range-thumb {
    width: 1.5rem;
    height: 1.5rem;
    background: v-bind('thumbColor || "#FFB107"');
    border: 0.2rem solid v-bind('borderColor || "#96550B"');
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 0.2rem 0 0 v-bind('borderColor || "#96550B"');

    &:hover {
      transform: scale(1.1);
      box-shadow: 0 0.3rem 0 0 v-bind('borderColor || "#96550B"');
    }

    &:active {
      transform: scale(0.95);
      box-shadow: 0 0.1rem 0 0 v-bind('borderColor || "#96550B"');
    }
  }

  /* Firefox track */
  &::-moz-range-track {
    height: 0.8rem;
    background: v-bind('trackColor || "#E0E0E0"');
    border: 0.2rem solid v-bind('borderColor || "#96550B"');
    border-radius: 0.5rem;
  }

  /* Internet Explorer */
  &::-ms-track {
    width: 100%;
    height: 0.8rem;
    background: transparent;
    border-color: transparent;
    color: transparent;
  }

  &::-ms-fill-lower {
    background: v-bind('trackActiveColor || "#FFD54F"');
    border: 0.2rem solid v-bind('borderColor || "#96550B"');
    border-radius: 0.5rem;
  }

  &::-ms-fill-upper {
    background: v-bind('trackColor || "#E0E0E0"');
    border: 0.2rem solid v-bind('borderColor || "#96550B"');
    border-radius: 0.5rem;
  }

  &::-ms-thumb {
    width: 1.5rem;
    height: 1.5rem;
    background: v-bind('thumbColor || "#FFB107"');
    border: 0.2rem solid v-bind('borderColor || "#96550B"');
    border-radius: 0.5rem;
    cursor: pointer;
    box-shadow: 0 0.2rem 0 0 v-bind('borderColor || "#96550B"');
  }
}

.slider-value {
  min-width: 4rem;
  text-align: center;
  font-family: 'Tomo Bossa Black', Arial, sans-serif;
  font-size: v-bind('fontSize || "1rem"');
  color: v-bind('borderColor || "#96550B"');
  background: v-bind('backgroundColor || "#FED31E"');
  padding: 0.3rem 0.6rem;
  border: 0.2rem solid v-bind('borderColor || "#96550B"');
  border-radius: 0.3rem;
  font-weight: bold;
  white-space: nowrap;
}

/* Responsivo */
@media screen and (max-width: 768px) {
  .slider-container {
    gap: 0.5rem;
  }

  .generic-slider {
    height: 1rem;

    &::-webkit-slider-thumb {
      width: 1.8rem;
      height: 1.8rem;
    }

    &::-moz-range-thumb {
      width: 1.8rem;
      height: 1.8rem;
    }
  }

  .slider-value {
    min-width: 2.5rem;
    font-size: 0.9rem;
  }
}
</style>
