<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { io, Socket } from 'socket.io-client'

const socket = ref<Socket | null>(null)
const connected = ref(false)
const message = ref('')
const messages = ref<string[]>([])
const inputMessage = ref('')

const connect = () => {
  socket.value = io('http://localhost:8000')

  socket.value.on('connect', () => {
    connected.value = true
    message.value = 'Conectado ao servidor!'
    console.log('Conectado!')
  })

  socket.value.on('disconnect', () => {
    connected.value = false
    message.value = 'Desconectado do servidor'
    console.log('Desconectado!')
  })

  socket.value.on('message', (data) => {
    messages.value.push(data)
  })

  socket.value.on('error', (error) => {
    console.error('Erro no socket:', error)
    message.value = 'Erro na conexão'
  })
}

const sendMessage = () => {
  if (socket.value && inputMessage.value.trim()) {
    socket.value.emit('message', inputMessage.value)
    messages.value.push(`Você: ${inputMessage.value}`)
    inputMessage.value = ''
  }
}

const disconnect = () => {
  socket.value?.disconnect()
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
    <h1>Word Tower - Teste Socket</h1>

    <div class="status">
      <p :class="{ connected: connected, disconnected: !connected }">
        Status: {{ connected ? 'Conectado' : 'Desconectado' }}
      </p>
      <p>{{ message }}</p>
    </div>

    <div class="messages">
      <h3>Mensagens:</h3>
      <div class="message-list">
        <div v-for="(msg, index) in messages" :key="index" class="message">
          {{ msg }}
        </div>
      </div>
    </div>

    <div class="input-area" v-if="connected">
      <input
        v-model="inputMessage"
        @keyup.enter="sendMessage"
        placeholder="Digite uma mensagem..."
        class="message-input"
      />
      <button @click="sendMessage" class="send-btn">Enviar</button>
    </div>

    <div class="controls">
      <button @click="connect" :disabled="connected" class="connect-btn">Conectar</button>
      <button @click="disconnect" :disabled="!connected" class="disconnect-btn">Desconectar</button>
    </div>
  </div>
</template>

<style scoped>
.game-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

.status {
  margin-bottom: 20px;
  padding: 10px;
  border-radius: 5px;
  background-color: #f5f5f5;
}

.connected {
  color: green;
  font-weight: bold;
}

.disconnected {
  color: red;
  font-weight: bold;
}

.messages {
  margin-bottom: 20px;
}

.message-list {
  height: 200px;
  overflow-y: auto;
  border: 1px solid #ccc;
  padding: 10px;
  background-color: #fafafa;
}

.message {
  margin-bottom: 5px;
  padding: 5px;
  background-color: white;
  border-radius: 3px;
}

.input-area {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.message-input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 3px;
}

.send-btn,
.connect-btn,
.disconnect-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}

.send-btn {
  background-color: #007bff;
  color: white;
}

.connect-btn {
  background-color: #28a745;
  color: white;
}

.disconnect-btn {
  background-color: #dc3545;
  color: white;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.controls {
  display: flex;
  gap: 10px;
}
</style>
