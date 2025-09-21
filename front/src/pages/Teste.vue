<script lang="ts" setup>
import { ref } from 'vue';
import GenericModal from '@/components/Modal/GenericModal.vue';
import GenericSwitch from '@/components/Inputs/GenericSwitch.vue';

const isModalOpen = ref(true);
</script>

<template>
  <GenericModal v-model:open="isModalOpen" title="Configurações">
    <p>Conteúdo do modal aqui</p>
  </GenericModal>

  <GenericSwitch background-color="black" border-color="yellow" width="10rem" />
</template>
<style scoped></style>
