<script lang="ts" setup>
import GenericButton from '@/components/Buttons/GenericButton.vue'
import { X } from 'lucide-vue-next'
import { ref, watch } from 'vue'

const props = defineProps<{
  open?: boolean
  title?: string
  backgroundColor?: string
  borderColor?: string
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
}>()

const isClosing = ref(false)
const shouldShow = ref(props.open || false)

// Função para fechar com animação
const closeModal = () => {
  isClosing.value = true

  // Após a animação, esconde o modal
  setTimeout(() => {
    emit('update:open', false)
    isClosing.value = false
    shouldShow.value = false
  }, 400) // Duração da animação de saída
}

// Observa mudanças na prop open
watch(() => props.open, (newValue) => {
  if (newValue) {
    shouldShow.value = true
    isClosing.value = false
  } else if (!isClosing.value) {
    shouldShow.value = false
  }
})
</script>

<template>
  <div v-if="shouldShow" class="modal-backdrop" :class="{ 'closing': isClosing }">
    <div class="modal-container" :class="{ 'closing': isClosing }" @click.stop>
      <div class="modal-header">
        <h2 class="modal-header-title">{{ title || 'Modal' }}</h2>
        <div class="modal-close-button">
          <GenericButton @click="closeModal" aspect-ratio="1" background-color="#ff4d4f" border-color="#b71c1c">
            <X :size="35" />
          </GenericButton>
        </div>
      </div>
      <div class="modal-body">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<style scoped>
@font-face {
  font-family: 'Tomo Bossa Black';
  src: url('@/assets/fonts/tomo_bossa_black.woff') format('woff');
}

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-container {
  background: v-bind('backgroundColor || "white"');
  border: 5px solid v-bind('borderColor || "transparent"');
  border-radius: .5rem;
  width: 50vw;
  height: fit-content;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  @media screen and (max-width: 768px) {
    width: 95vw;
  }
}

.modal-backdrop {
  animation: backdropFadeIn 0.3s ease-out;
}

.modal-backdrop.closing {
  animation: backdropFadeOut 0.4s ease-out;
}

.modal-container {
  animation: modalSlideIn 0.4s ease-out;
}

.modal-container.closing {
  animation: modalSlideOut 0.4s ease-out;
}

.modal-header,
.modal-body,
.modal-footer {
  padding: 1rem;
  font-family: 'Tomo Bossa Black', Arial, sans-serif;
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  justify-content: center;
  align-items: center;
}

.modal-header {
  position: relative;
}

.modal-header-title {
  font-size: 1.5rem;
  margin: 0;
  text-align: center;
}

.modal-close-button {
  width: 3rem;
  translate: 0 -10px;
  position: absolute;
  top: 1rem;
  right: 1rem;
}

@keyframes backdropFadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes backdropFadeOut {
  from {
    opacity: 1;
  }

  to {
    opacity: 0;
  }
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-100px) scale(0.95);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes modalSlideOut {
  from {
    opacity: 1;
    transform: translateY(0) scale(1);
  }

  to {
    opacity: 0;
    transform: translateY(-100px) scale(0.95);
  }
}
</style>