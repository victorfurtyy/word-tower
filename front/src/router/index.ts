import { createRouter, createWebHistory } from 'vue-router'
import LobbyGame from '@/pages/LobbyGame.vue'
import Teste from '@/pages/Teste.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'start-screen',
      component: LobbyGame,
    },
    {
      path: '/teste',
      name: 'teste',
      component: Teste,
    }
  ],
})

export default router
