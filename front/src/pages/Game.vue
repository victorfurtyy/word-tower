<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { io, Socket } from 'socket.io-client'

const socket = ref<Socket | null>(null)
const connected = ref(false)
const responses = ref<string[]>([])

// Campos para enviar dados
const selectedEvent = ref('join_game')
const dataInput = ref('{"game_id": "sala123", "player_name": "João"}')

// Opções de eventos disponíveis (baseado no backend)
const eventOptions = [
  'join_game',
  'submit_word',
  'start_new_game',
  'change_difficulty',
  'leave_game',
  'player_timeout',
]

const connect = () => {
  socket.value = io('http://localhost:8000')

  socket.value.on('connect', () => {
    connected.value = true
    addResponse('✅ Conectado ao servidor!')
    console.log('Você se conectou ao Word Tower!')
  })

  socket.value.on('disconnect', () => {
    connected.value = false
    addResponse('❌ Desconectado do servidor')
    console.log('Desconectado!')
  })

  socket.value.on('error', (error) => {
    addResponse(`🚫 Erro: ${error}`)
    console.error('Erro no socket:', error)
  })

  // Listener genérico para capturar todas as respostas
  socket.value.onAny((eventName, ...args) => {
    addResponse(`📨 Evento: ${eventName} | Dados: ${JSON.stringify(args)}`)
  })
}

const disconnect = () => {
  socket.value?.disconnect()
}

const sendData = () => {
  if (!socket.value || !connected.value) {
    addResponse('⚠️ Não conectado ao servidor!')
    return
  }

  try {
    const data = JSON.parse(dataInput.value)
    socket.value.emit(selectedEvent.value, data)
    addResponse(`📤 Enviado: ${selectedEvent.value} | ${JSON.stringify(data)}`)
  } catch (error) {
    addResponse(`🚫 Erro no JSON: ${error}`)
  }
}

const addResponse = (text: string) => {
  const timestamp = new Date().toLocaleTimeString()
  responses.value.push(`[${timestamp}] ${text}`)
}

const clearResponses = () => {
  responses.value = []
}

onMounted(() => {
  connect()
})

onUnmounted(() => {
  disconnect()
})
</script>

<template>
  <div class="game-container">
    <h1>Word Tower - Socket Tester</h1>

    <!-- Status da Conexão -->
    <div class="status-section">
      <div class="status" :class="{ connected: connected, disconnected: !connected }">
        Status: {{ connected ? '🟢 Conectado' : '🔴 Desconectado' }}
      </div>
      <div class="controls">
        <button @click="connect" :disabled="connected" class="btn connect-btn">Conectar</button>
        <button @click="disconnect" :disabled="!connected" class="btn disconnect-btn">
          Desconectar
        </button>
      </div>
    </div>

    <!-- Seção de Envio -->
    <div class="send-section">
      <h3>Enviar Dados</h3>

      <div class="form-group">
        <label>Evento:</label>
        <select v-model="selectedEvent" class="event-select">
          <option v-for="event in eventOptions" :key="event" :value="event">
            {{ event }}
          </option>
        </select>
      </div>

      <div class="form-group">
        <label>Dados (JSON):</label>
        <input
          v-model="dataInput"
          placeholder='{"player_name": "João", "room_id": "123"}'
          class="data-input"
          @keyup.enter="sendData"
        />
      </div>

      <button @click="sendData" :disabled="!connected" class="btn send-btn">📤 Enviar</button>
    </div>

    <!-- Seção de Respostas -->
    <div class="responses-section">
      <div class="responses-header">
        <h3>Respostas do Servidor</h3>
        <button @click="clearResponses" class="btn clear-btn">🗑️ Limpar</button>
      </div>

      <textarea
        :value="responses.join('\n')"
        readonly
        class="responses-textarea"
        placeholder="As respostas do servidor aparecerão aqui..."
      ></textarea>
    </div>

    <!-- Exemplos de Uso -->
    <div class="examples-section">
      <h3>Exemplos de JSON por Evento:</h3>
      <div class="examples">
        <strong>join_game:</strong> <code>{"game_id": "sala123", "player_name": "João"}</code><br />
        <strong>submit_word:</strong> <code>{"word": "CASA"}</code><br />
        <strong>start_new_game:</strong> <code>{}</code><br />
        <strong>change_difficulty:</strong> <code>{"difficulty": "normal"}</code> |
        <code>{"difficulty": "easy"}</code> | <code>{"difficulty": "caotic"}</code><br />
        <strong>leave_game:</strong> <code>{}</code><br />
        <strong>player_timeout:</strong> <code>{"player_name": "João"}</code>
      </div>
    </div>
  </div>
</template>

<style scoped>
.game-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.status-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.status {
  font-weight: bold;
  font-size: 18px;
}

.connected {
  color: #28a745;
}

.disconnected {
  color: #dc3545;
}

.controls {
  display: flex;
  gap: 10px;
}

.send-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  background-color: #ffffff;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #495057;
}

.event-select,
.data-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.event-select {
  background-color: white;
}

.responses-section {
  margin-bottom: 30px;
}

.responses-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.responses-textarea {
  width: 100%;
  height: 300px;
  padding: 15px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  background-color: #f8f9fa;
  resize: vertical;
}

.examples-section {
  padding: 15px;
  background-color: #e9ecef;
  border-radius: 8px;
}

.examples code {
  display: inline-block;
  background-color: #f1f3f4;
  padding: 4px 8px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  margin: 2px 0;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.2s;
}

.connect-btn {
  background-color: #28a745;
  color: white;
}

.connect-btn:hover:not(:disabled) {
  background-color: #218838;
}

.disconnect-btn {
  background-color: #dc3545;
  color: white;
}

.disconnect-btn:hover:not(:disabled) {
  background-color: #c82333;
}

.send-btn {
  background-color: #007bff;
  color: white;
  width: 100%;
  margin-top: 10px;
}

.send-btn:hover:not(:disabled) {
  background-color: #0056b3;
}

.clear-btn {
  background-color: #6c757d;
  color: white;
  font-size: 12px;
  padding: 5px 10px;
}

.clear-btn:hover {
  background-color: #545b62;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

h1 {
  text-align: center;
  color: #343a40;
  margin-bottom: 30px;
}

h3 {
  color: #495057;
  margin-bottom: 15px;
}
</style>
