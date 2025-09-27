<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGameStore } from '@/stores/gameStore'

const route = useRoute()
const router = useRouter()
const gameStore = useGameStore()

// Pegar parâmetros da rota
const gameId = route.params.gameId as string
const playerName = ref(localStorage.getItem('pendingPlayerName') || '')

// Estado local da interface
const inputWord = ref('')
const selectedDifficulty = ref('normal')
const showNameInput = ref(!playerName.value) // Só mostra se não tem nome salvo
const messagesContainer = ref<HTMLElement | null>(null)
const wordInput = ref<HTMLInputElement | null>(null)

// Computed properties
const canSubmitWord = computed(() => 
  gameStore.isConnected && 
  gameStore.gameStarted && 
  inputWord.value.trim()
)

// Função para conectar após inserir o nome
function connectToGame() {
  if (!playerName.value.trim()) return
  
  gameStore.connect(gameId, playerName.value.trim())
  showNameInput.value = false
}

// Função para enviar palavra
function submitWord() {
  if (!canSubmitWord.value) return
  
  gameStore.submitWord(inputWord.value)
  inputWord.value = ''
}

// Função para iniciar jogo
function startGame() {
  gameStore.startNewGame()
}

// Função para alterar dificuldade
function changeDifficulty() {
  gameStore.changeDifficulty(selectedDifficulty.value)
}

// Função para voltar ao lobby
function backToLobby() {
  gameStore.leaveGame()
  router.push('/')
}

// Limpar erro
function clearError() {
  gameStore.clearError()
}

// Auto-dismiss do erro após 5 segundos
watch(() => gameStore.lastError, (newError) => {
  if (newError) {
    setTimeout(() => {
      gameStore.clearError()
    }, 5000) // 5 segundos
  }
})

// Lifecycle
onMounted(() => {
  // Limpar estado ao montar
  gameStore.resetState()
  
  // Se não tem gameId, volta para o lobby
  if (!gameId) {
    router.push('/')
    return
  }
  
  // Se já tem nome do jogador, conecta automaticamente
  if (playerName.value.trim()) {
    connectToGame()
  }
})

onUnmounted(() => {
  // Desconectar ao desmontar
  if (gameStore.isConnected) {
    gameStore.leaveGame()
  }
})

// Função para destacar a próxima letra
function highlightNextLetter(word: string, index: number): string {
  if (!word || index < 0 || index >= word.length) return word
  
  return word.split('').map((char, i) => 
    i === index ? `<mark style="background: #FFB107; color: #8A480F; padding: 2px 4px; border-radius: 3px; font-weight: bold;">${char}</mark>` : char
  ).join('')
}

// Função para fazer scroll para o final das mensagens
function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// Watch para fazer scroll quando as mensagens mudarem
watch(() => gameStore.messages, () => {
  nextTick(() => {
    scrollToBottom()
  })
}, { deep: true })

// Watch para dar foco no input quando for minha vez
watch(() => gameStore.isMyTurn, (isMyTurn) => {
  if (isMyTurn && gameStore.gameStarted && wordInput.value) {
    nextTick(() => {
      wordInput.value?.focus()
    })
  }
})

// Watch para dar foco quando o jogo começar se já for minha vez
watch(() => gameStore.gameStarted, (gameStarted) => {
  if (gameStarted && gameStore.isMyTurn && wordInput.value) {
    nextTick(() => {
      wordInput.value?.focus()
    })
  }
})
</script>

<template>
  <div class="game-container">
    <!-- Formulário de Nome (estilo similar ao LobbyGame) -->
    <div v-if="showNameInput" class="name-input-screen">
      <div class="logo-container">
        <img src="@/assets/images/logo/logo.png" class="game-logo" alt="Word Tower" draggable="false" />
      </div>
      
      <div class="name-form">
        <h2>Sala: {{ gameId }}</h2>
        <div class="form-group">
          <label>Digite seu nome:</label>
          <input 
            v-model="playerName" 
            type="text" 
            placeholder="Ex: João" 
            @keyup.enter="connectToGame"
            class="name-input"
          />
        </div>
        <button @click="connectToGame" :disabled="!playerName.trim()" class="btn-connect">
          Entrar no Jogo
        </button>
      </div>
    </div>

    <!-- Interface do Jogo -->
    <div v-else class="game-interface">
      <!-- Header com logo pequena e controles -->
      <div class="game-header">
        <img src="@/assets/images/logo/logo.png" class="small-logo" alt="Word Tower" draggable="false" />
        <div class="header-info">
          <span class="room-name">🏠 {{ gameId }}</span>
          <span :class="['connection-status', gameStore.isConnected ? 'connected' : 'disconnected']">
            {{ gameStore.isConnected ? '🟢 Conectado' : '🔴 Desconectado' }}
          </span>
        </div>
        <button @click="backToLobby" class="btn-back">Voltar</button>
      </div>

      <!-- Erro -->
      <div v-if="gameStore.lastError" class="error-message">
        ❌ {{ gameStore.lastError }}
        <button @click="clearError" class="btn-clear">✕</button>
      </div>

      <!-- Jogadores -->
      <div class="players-section">
        <h3>👥 Jogadores na Sala ({{ gameStore.players.length }})</h3>
        <div class="players-grid">
          <div v-for="player in gameStore.players" :key="player.id" class="player-card">
            <span class="player-name">{{ player.name }}</span>
            <span v-if="player.id === gameStore.myPlayerId" class="you-badge">Você</span>
            <span v-if="player.is_host" class="host-badge">👑 Host</span>
            <span v-if="gameStore.currentPlayer && player.id === gameStore.currentPlayer.id" class="turn-badge">Sua vez!</span>
            <span v-if="!player.is_active" class="eliminated-badge">Eliminado</span>
          </div>
        </div>
        
        <!-- Indicador de turno -->
        <div v-if="gameStore.gameStarted && gameStore.currentPlayer" class="turn-indicator">
          <span v-if="gameStore.isMyTurn" class="my-turn">🎯 É sua vez de jogar!</span>
          <span v-else class="other-turn">⏳ Vez de: {{ gameStore.currentPlayer.name }}</span>
        </div>
      </div>

      <!-- Controles do Jogo (apenas para o host) -->
      <div v-if="gameStore.amIHost" class="game-controls">
        <div class="controls-header">
          <h3>⚙️ Configurações (Host)</h3>
        </div>
        
        <div class="control-row">
          <label>Dificuldade:</label>
          <select v-model="selectedDifficulty" @change="changeDifficulty" class="difficulty-select">
            <option value="easy">🟢 Fácil (sem acentos)</option>
            <option value="normal">🟡 Normal (com acentos)</option>
            <option value="caotic">🔴 Caótico (letra aleatória)</option>
          </select>
        </div>
        
        <button 
          v-if="!gameStore.gameStarted"
          @click="startGame" 
          :disabled="!gameStore.isConnected || gameStore.players.length < 1"
          class="btn-start"
        >
          🚀 Iniciar Jogo
        </button>
      </div>

      <!-- Mensagem para não-hosts -->
      <div v-else-if="!gameStore.gameStarted" class="host-only-message">
        <p>🔒 Apenas o host (criador da sala) pode configurar e iniciar o jogo.</p>
        <p v-if="gameStore.players.find((p: any) => p.is_host)">
          Host atual: <strong>{{ gameStore.players.find((p: any) => p.is_host)?.name }}</strong>
        </p>
      </div>

      <!-- Estado do Jogo Ativo -->
      <div v-if="gameStore.gameStarted" class="game-active">
        <div class="game-status">
          <h3>🎮 Jogo em Andamento</h3>
          <div class="difficulty-badge" :class="gameStore.difficulty">
            Modo: {{ 
              gameStore.difficulty === 'easy' ? '🟢 Fácil' : 
              gameStore.difficulty === 'normal' ? '🟡 Normal' : 
              '🔴 Caótico' 
            }}
          </div>
        </div>

        <div class="word-display-container">
          <h4>📝 Palavra Atual:</h4>
          <div 
            class="current-word-display" 
            v-html="highlightNextLetter(gameStore.currentWord, gameStore.nextLetterIndex)"
          ></div>
        </div>

        <div class="next-letter-container">
          <h4>🎯 Próxima palavra deve começar com:</h4>
          <div class="next-letter-badge">{{ gameStore.nextLetter.toUpperCase() }}</div>
        </div>

        <!-- Input para nova palavra -->
        <div class="word-input-container">
          <input 
            ref="wordInput"
            v-model="inputWord" 
            type="text" 
            placeholder="Digite sua palavra aqui..."
            @keyup.enter="submitWord"
            :disabled="!gameStore.isConnected || !gameStore.isMyTurn"
            class="word-input"
          />
          <button @click="submitWord" :disabled="!canSubmitWord || !gameStore.isMyTurn" class="btn-submit">
            Enviar 📤
          </button>
        </div>
        
        <!-- Aviso quando não é sua vez -->
        <div v-if="gameStore.gameStarted && !gameStore.isMyTurn" class="not-your-turn">
          ⏳ Aguarde sua vez para jogar...
        </div>
      </div>

      <!-- Chat de Mensagens -->
      <div class="messages-section">
        <h3>💬 Mensagens do Jogo</h3>
        <div ref="messagesContainer" class="messages-container">
          <div 
            v-for="message in gameStore.messages" 
            :key="message.id" 
            class="message"
            :class="{ 
              'system-message': message.sender === 'Sistema',
              'my-message': message.sender === gameStore.playerName 
            }"
          >
            <div class="message-header">
              <span class="message-sender">{{ message.sender }}</span>
              <span class="message-time">{{ message.timestamp }}</span>
            </div>
            <div class="message-content">{{ message.content }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Background -->
    <div class="page-background"></div>
  </div>
</template>

<style scoped>
@font-face {
  font-family: 'Tomo Bossa Black';
  src: url('@/assets/fonts/tomo_bossa_black.woff') format('woff');
}

.game-container {
  position: relative;
  min-height: 100vh;
  font-family: 'Tomo Bossa Black', Arial, sans-serif;
  overflow-x: auto;
}

/* Background igual ao LobbyGame */
.page-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-image: url('@/assets/images/backgrounds/start_screen_bg.png');
  background-repeat: no-repeat;
  background-size: cover;
  background-position: 45% 100%;
  z-index: 0;
}

/* Tela de input do nome (similar ao lobby) */
.name-input-screen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
  gap: 2rem;
}

.logo-container {
  text-align: center;
}

.game-logo {
  width: 20rem;
  height: auto;
}

.name-form {
  background-color: #C7721E;
  border: 0.3rem solid #8A480F;
  border-radius: 0.5rem;
  box-shadow: 0 0.6rem 0 0 #8A480F;
  padding: 2rem;
  text-align: center;
  color: #502405;
}

.name-form h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.5rem;
}

.form-group {
  margin: 1rem 0;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
  font-weight: bold;
}

.name-input {
  width: 15rem;
  padding: 0.8rem;
  border: 0.2rem solid #96550B;
  border-radius: 0.3rem;
  background-color: #FEE793;
  font-size: 1rem;
  text-align: center;
  font-family: 'Tomo Bossa Black', Arial, sans-serif;
}

.btn-connect {
  background-color: #FFB107;
  border: 0.2rem solid #96550B;
  color: #502405;
  padding: 0.8rem 2rem;
  border-radius: 0.3rem;
  font-size: 1.2rem;
  font-weight: bold;
  cursor: pointer;
  font-family: 'Tomo Bossa Black', Arial, sans-serif;
  box-shadow: 0 0.3rem 0 0 #96550B;
  transition: all 0.1s;

  &:hover:not(:disabled) {
    background-color: color-mix(in srgb, #FFB107, white 20%);
    transform: translateY(-2px);
    box-shadow: 0 10px 0 0 #96550B;
  }

  &:active:not(:disabled) {
    background-color: color-mix(in srgb, #FFB107, black 10%);
    transform: translateY(8px);
    box-shadow: 0 0 0 0 #96550B;
  }
}

.btn-connect:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Interface principal do jogo */
.game-interface {
  position: relative;
  z-index: 5;
  min-height: 100vh;
  padding: 1rem;
  max-width: 1200px;
  margin: 0 auto;
}

.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #C7721E;
  border: 0.2rem solid #8A480F;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
  box-shadow: 0 0.3rem 0 0 #8A480F;
}

.small-logo {
  height: 3rem;
}

.header-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: #502405;
}

.room-name {
  font-size: 1.2rem;
  font-weight: bold;
}

.connection-status.connected {
  color: #2E7D32;
}

.connection-status.disconnected {
  color: #D32F2F;
}

.btn-back {
  background-color: #D32F2F;
  color: white;
  border: 0.2rem solid #B71C1C;
  padding: 0.6rem 1.2rem;
  border-radius: 0.3rem;
  cursor: pointer;
  font-family: 'Tomo Bossa Black', Arial, sans-serif;
  box-shadow: 0 0.2rem 0 0 #B71C1C;
  transition: all 0.1s;

  &:hover {
    background-color: color-mix(in srgb, #D32F2F, white 20%);
    transform: translateY(-2px);
    box-shadow: 0 10px 0 0 #B71C1C;
  }

  &:active {
    background-color: color-mix(in srgb, #D32F2F, black 10%);
    transform: translateY(8px);
    box-shadow: 0 0 0 0 #B71C1C;
  }
}

/* Seções do jogo */
.players-section,
.game-controls,
.game-active,
.messages-section {
  background-color: #C7721E;
  border: 0.2rem solid #8A480F;
  border-radius: 0.5rem;
  padding: 1.5rem;
  margin-bottom: 1rem;
  box-shadow: 0 0.3rem 0 0 #8A480F;
  color: #502405;
}

.players-section h3,
.game-controls h3,
.game-active h3,
.messages-section h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.3rem;
}

.players-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.8rem;
}

.player-card {
  background-color: #FAD280;
  border: 0.15rem solid #96550B;
  border-radius: 0.3rem;
  padding: 0.8rem;
  text-align: center;
  position: relative;
}

.player-name {
  display: block;
  font-weight: bold;
  margin-bottom: 0.3rem;
}

.you-badge {
  position: absolute;
  top: -0.3rem;
  right: -0.3rem;
  background-color: #4CAF50;
  color: white;
  font-size: 0.7rem;
  padding: 0.2rem 0.4rem;
  border-radius: 0.2rem;
}

.host-badge {
  position: absolute;
  top: -0.3rem;
  left: -0.3rem;
  background-color: #FFD700;
  color: #333;
  font-size: 0.6rem;
  padding: 0.2rem 0.4rem;
  border-radius: 0.2rem;
  font-weight: bold;
}

.turn-badge {
  position: absolute;
  top: -0.5rem;
  left: -0.5rem;
  background-color: #FF9800;
  color: white;
  font-size: 0.6rem;
  padding: 0.2rem 0.4rem;
  border-radius: 0.2rem;
  animation: pulse 1s infinite;
}

.eliminated-badge {
  position: absolute;
  top: -0.3rem;
  left: -0.3rem;
  background-color: #F44336;
  color: white;
  font-size: 0.7rem;
  padding: 0.2rem 0.4rem;
  border-radius: 0.2rem;
}

.turn-indicator {
  margin-top: 1rem;
  text-align: center;
  padding: 1rem;
  border-radius: 0.3rem;
  font-weight: bold;
}

.my-turn {
  color: #4CAF50;
  background-color: #E8F5E8;
  padding: 0.8rem;
  border-radius: 0.3rem;
  display: inline-block;
  animation: pulse 2s infinite;
}

.other-turn {
  color: #FF9800;
  background-color: #FFF3E0;
  padding: 0.8rem;
  border-radius: 0.3rem;
  display: inline-block;
}

.not-your-turn {
  text-align: center;
  color: #666;
  font-style: italic;
  margin-top: 1rem;
  padding: 0.5rem;
  background-color: #F5F5F5;
  border-radius: 0.3rem;
}

.host-only-message {
  text-align: center;
  background-color: #FFF3E0;
  border: 1px solid #FF9800;
  border-radius: 0.3rem;
  padding: 1rem;
  margin: 1rem 0;
  color: #E65100;
}

.host-only-message p {
  margin: 0.5rem 0;
}

.host-only-message strong {
  color: #FF6F00;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}

.control-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1rem 0;
}

.control-row label {
  font-weight: bold;
  min-width: 100px;
}

.difficulty-select {
  flex: 1;
  padding: 0.5rem;
  border: 0.15rem solid #96550B;
  border-radius: 0.3rem;
  background-color: #FEE793;
  font-family: 'Tomo Bossa Black', Arial, sans-serif;
}

.btn-start {
  width: 100%;
  background-color: #4CAF50;
  color: white;
  border: 0.2rem solid #2E7D32;
  padding: 1rem;
  border-radius: 0.3rem;
  font-size: 1.2rem;
  font-weight: bold;
  cursor: pointer;
  font-family: 'Tomo Bossa Black', Arial, sans-serif;
  box-shadow: 0 0.3rem 0 0 #2E7D32;
  margin-top: 1rem;
  transition: all 0.1s;

  &:hover:not(:disabled) {
    background-color: color-mix(in srgb, #4CAF50, white 20%);
    transform: translateY(-2px);
    box-shadow: 0 10px 0 0 #2E7D32;
  }

  &:active:not(:disabled) {
    background-color: color-mix(in srgb, #4CAF50, black 10%);
    transform: translateY(8px);
    box-shadow: 0 0 0 0 #2E7D32;
  }
}

.btn-start:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.game-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.difficulty-badge {
  padding: 0.5rem 1rem;
  border-radius: 0.3rem;
  font-weight: bold;
}

.difficulty-badge.easy {
  background-color: #C8E6C9;
  color: #2E7D32;
}

.difficulty-badge.normal {
  background-color: #FFF3C4;
  color: #F57F17;
}

.difficulty-badge.caotic {
  background-color: #FFCDD2;
  color: #D32F2F;
}

.word-display-container,
.next-letter-container {
  text-align: center;
  margin: 1.5rem 0;
}

.current-word-display {
  font-size: 2rem;
  font-weight: bold;
  margin: 1rem 0;
  background-color: #FAD280;
  padding: 1rem;
  border-radius: 0.3rem;
  border: 0.15rem solid #96550B;
}

.next-letter-badge {
  display: inline-block;
  font-size: 1.8rem;
  font-weight: bold;
  background-color: #FFCDD2;
  color: #D32F2F;
  padding: 0.8rem 1.5rem;
  border-radius: 50%;
  border: 0.2rem solid #D32F2F;
  box-shadow: 0 0.2rem 0 0 #D32F2F;
}

.word-input-container {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.word-input {
  flex: 1;
  padding: 1rem;
  border: 0.2rem solid #96550B;
  border-radius: 0.3rem;
  background-color: #FEE793;
  font-size: 1.1rem;
  font-family: 'Tomo Bossa Black', Arial, sans-serif;
}

.btn-submit {
  background-color: #2196F3;
  color: white;
  border: 0.2rem solid #1976D2;
  padding: 1rem 2rem;
  border-radius: 0.3rem;
  font-weight: bold;
  cursor: pointer;
  font-family: 'Tomo Bossa Black', Arial, sans-serif;
  box-shadow: 0 0.2rem 0 0 #1976D2;
  transition: all 0.1s;

  &:hover:not(:disabled) {
    background-color: color-mix(in srgb, #2196F3, white 20%);
    transform: translateY(-2px);
    box-shadow: 0 10px 0 0 #1976D2;
  }

  &:active:not(:disabled) {
    background-color: color-mix(in srgb, #2196F3, black 10%);
    transform: translateY(8px);
    box-shadow: 0 0 0 0 #1976D2;
  }
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.messages-container {
  max-height: 200px;
  overflow-y: auto;
  background-color: #FAD280;
  border: 0.15rem solid #96550B;
  border-radius: 0.3rem;
  padding: 1rem;
  
  /* Custom scrollbar */
  scrollbar-width: thin;
  scrollbar-color: #96550B #FAD280;

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: #FAD280;
    border-radius: 0.2rem;
  }

  &::-webkit-scrollbar-thumb {
    background: #96550B;
    border-radius: 0.2rem;
    border: 1px solid #FAD280;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: #8A480F;
  }

  &::-webkit-scrollbar-thumb:active {
    background: #502405;
  }
}

.message {
  margin-bottom: 0.8rem;
  padding: 0.5rem;
  border-radius: 0.3rem;
  max-width: 80%;
}

.message.system-message {
  background-color: #E0E0E0;
  font-style: italic;
  margin: 0 auto 0.8rem auto;
  text-align: center;
  max-width: 90%;
}

.message.my-message {
  background-color: #E3F2FD;
  border-left: none;
  border-right: 0.3rem solid #2196F3;
  margin-left: auto;
  margin-right: 0;
  text-align: right;
}

.message-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  margin-bottom: 0.3rem;
  opacity: 0.8;
}

.message.my-message .message-header {
  flex-direction: row-reverse;
  gap: 0.5rem;
}

.message-sender {
  font-weight: bold;
}

.message-content {
  font-size: 0.9rem;
}

.error-message {
  position: fixed;
  top: 20px;
  right: 20px;
  background-color: #FFEBEE;
  color: #D32F2F;
  border: 0.15rem solid #D32F2F;
  padding: 1rem 1.5rem;
  border-radius: 0.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(211, 47, 47, 0.3);
  max-width: 400px;
  min-width: 300px;
  font-family: 'Tomo Bossa Black', Arial, sans-serif;
  font-weight: bold;
  
  /* Animação de entrada */
  animation: slideInFromRight 0.3s ease-out;
}

@keyframes slideInFromRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Animação de saída */
.error-message.fade-out {
  animation: slideOutToRight 0.3s ease-in forwards;
}

@keyframes slideOutToRight {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}

.btn-clear {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0.3rem 0.6rem;
  color: #D32F2F;
  font-weight: bold;
  border-radius: 50%;
  transition: all 0.1s;
  font-size: 1.2rem;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  margin-left: 1rem;

  &:hover {
    background-color: color-mix(in srgb, #D32F2F, white 85%);
    transform: scale(1.1);
    box-shadow: 0 2px 8px rgba(211, 47, 47, 0.3);
  }

  &:active {
    background-color: color-mix(in srgb, #D32F2F, white 75%);
    transform: scale(0.95);
    box-shadow: 0 1px 4px rgba(211, 47, 47, 0.3);
  }
}

/* Custom scrollbar global para elementos que podem ter overflow */
.game-interface {
  scrollbar-width: thin;
  scrollbar-color: #8A480F #C7721E;
}

.game-interface::-webkit-scrollbar {
  width: 10px;
}

.game-interface::-webkit-scrollbar-track {
  background: #C7721E;
  border-radius: 0.3rem;
}

.game-interface::-webkit-scrollbar-thumb {
  background: #8A480F;
  border-radius: 0.3rem;
  border: 1px solid #C7721E;
}

.game-interface::-webkit-scrollbar-thumb:hover {
  background: #502405;
}

/* Responsividade */
@media (max-width: 768px) {
  .game-interface {
    padding: 0.5rem;
  }
  
  .game-header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .players-grid {
    grid-template-columns: 1fr;
  }
  
  .word-input-container {
    flex-direction: column;
  }
  
  .game-logo {
    width: 15rem;
  }

  .error-message {
    top: 10px;
    right: 10px;
    left: 10px;
    max-width: none;
    min-width: auto;
    margin: 0;
  }

  @keyframes slideInFromRight {
    from {
      transform: translateY(-100%);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  @keyframes slideOutToRight {
    from {
      transform: translateY(0);
      opacity: 1;
    }
    to {
      transform: translateY(-100%);
      opacity: 0;
    }
  }
}
</style>
