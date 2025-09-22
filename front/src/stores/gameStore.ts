import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { io, Socket } from 'socket.io-client'

interface Player {
  id: string
  name: string
  is_active: boolean
  is_host: boolean
}

interface GameMessage {
  id: number
  sender: string
  content: string
  timestamp: string
}

export const useGameStore = defineStore('game', () => {
  // Estado da conexão
  const socket = ref<Socket | null>(null)
  const connected = ref<boolean>(false)
  const gameId = ref<string>('')
  const playerName = ref<string>('')

  // Estado do jogo
  const players = ref<Player[]>([])
  const currentWord = ref<string>('')
  const nextLetter = ref<string>('')
  const nextLetterIndex = ref<number>(0)
  const difficulty = ref<string>('normal')
  const gameStarted = ref<boolean>(false)
  const currentPlayer = ref<Player | null>(null)
  const myPlayerId = ref<string>('')
  const hostId = ref<string>('')  // ID do host da sala

  // Mensagens e status
  const messages = ref<GameMessage[]>([])
  const lastError = ref<string>('')

  // Computed
  const isConnected = computed(() => connected.value && socket.value?.disconnected === false)
  const isMyTurn = computed(() => {
    if (!currentPlayer.value || !myPlayerId.value) return false
    return currentPlayer.value.id === myPlayerId.value
  })
  const amIHost = computed(() => {
    // Primeira tentativa: usar hostId
    if (hostId.value && myPlayerId.value) {
      return myPlayerId.value === hostId.value
    }
    // Fallback: verificar diretamente no array de players
    const me = players.value.find(p => p.id === myPlayerId.value)
    return me?.is_host || false
  })

  // Conectar ao Socket.IO
  function connect(gameIdParam: string, playerNameParam: string): void {
    if (socket.value) {
      socket.value.disconnect()
    }

    gameId.value = gameIdParam
    playerName.value = playerNameParam

    // Limpar o nome pendente do localStorage
    localStorage.removeItem('pendingPlayerName')

    // Conecta ao Socket.IO - backend em localhost:8000
    socket.value = io('http://localhost:8000', {
      transports: ['websocket', 'polling']
    })

    socket.value.on('connect', () => {
      console.log('🔌 Conectado ao Socket.IO')
      connected.value = true

      // Enviar dados de entrada na sala
      console.log('📤 Enviando join_game:', { game_id: gameIdParam, player_name: playerNameParam })
      socket.value?.emit('join_game', {
        game_id: gameIdParam,
        player_name: playerNameParam
      })

      addMessage('Sistema', 'Conectado ao jogo!')
    })

    // Escutar eventos do jogo
    socket.value.on('game_event', (data) => handleGameEvent(data))

    socket.value.on('disconnect', () => {
      console.log('Desconectado do Socket.IO')
      connected.value = false
      addMessage('Sistema', 'Conexão perdida')
    })

    socket.value.on('connect_error', (error: any) => {
      console.error('Erro no Socket.IO:', error)
      lastError.value = 'Erro de conexão'
      addMessage('Sistema', 'Erro de conexão')
    })
  }

  // Handler principal para eventos do jogo
  function handleGameEvent(data: any): void {
    console.log('🎲 Evento do jogo:', data)

    switch (data.type) {
      case 'player_joined':
        players.value = data.players || []
        currentPlayer.value = data.current_player || null

        // Sempre define o hostId quando há players
        const host = players.value.find(p => p.is_host)
        if (host) {
          hostId.value = host.id
        }

        // Salvar meu ID se for minha entrada
        if (data.player === playerName.value && data.player_id) {
          myPlayerId.value = data.player_id
        }
        addMessage('Sistema', `${data.player} entrou na sala`)
        break

      case 'player_left':
        players.value = data.players || []
        // Atualiza o host se necessário
        if (players.value.length > 0) {
          const host = players.value.find(p => p.is_host)
          if (host) {
            hostId.value = host.id
          }
        }
        currentPlayer.value = data.current_player || null
        addMessage('Sistema', `${data.player} saiu da sala`)
        break

      case 'game_started':
        gameStarted.value = true
        currentWord.value = data.current_word || data.initial_word || data.word || ''
        nextLetter.value = data.next_letter || ''
        nextLetterIndex.value = data.next_letter_index || 0
        players.value = data.players || []
        currentPlayer.value = data.current_player || null

        // Atualiza o host
        if (players.value.length > 0) {
          const host = players.value.find(p => p.is_host)
          if (host) {
            hostId.value = host.id
          }
        }
        addMessage('Sistema', '🎮 Jogo iniciado!')
        break

      case 'next_turn':
        currentPlayer.value = data.current_player || null
        addMessage('Sistema', `Vez de: ${data.current_player?.name || 'Alguém'}`)
        break

      case 'word_submitted':
        currentWord.value = data.current_word || data.word || ''
        nextLetter.value = data.next_letter || ''
        nextLetterIndex.value = data.next_letter_index || 0
        players.value = data.players || []
        currentPlayer.value = data.current_player || null
        // Atualiza o host
        if (players.value.length > 0) {
          const host = players.value.find(p => p.is_host)
          if (host) {
            hostId.value = host.id
          }
        }
        addMessage(data.player || 'Alguém', data.word || '')
        break

      case 'player_eliminated':
        players.value = data.players || []
        currentPlayer.value = data.current_player || null
        // Atualiza o host
        if (players.value.length > 0) {
          const host = players.value.find(p => p.is_host)
          if (host) {
            hostId.value = host.id
          }
        }
        addMessage('Sistema', `${data.player} foi eliminado!`)
        break

      case 'game_over':
        gameStarted.value = false
        addMessage('Sistema', `🏆 Jogo terminou! Vencedor: ${data.winner}`)
        break

      case 'error':
        lastError.value = data.message || 'Erro desconhecido'
        addMessage('Erro', data.message || 'Erro desconhecido')
        break

      case 'difficulty_changed':
        difficulty.value = data.difficulty || 'normal'
        addMessage('Sistema', `Dificuldade alterada para: ${data.difficulty}`)
        break

      case 'difficulty_change_denied':
        lastError.value = data.reason || 'Não foi possível alterar a dificuldade'
        break

      case 'start_game_denied':
        lastError.value = data.reason || 'Não foi possível iniciar o jogo'
        break

      case 'word_rejected':
        lastError.value = data.reason || 'Palavra rejeitada'
        addMessage('Sistema', `❌ Palavra rejeitada: ${data.reason}`)
        break

      default:
        console.log('Evento não tratado:', data.type)
        break
    }
  }

  // Enviar palavra
  function submitWord(word: string): void {
    if (!socket.value || !word.trim()) return

    socket.value.emit('submit_word', {
      word: word.trim()
    })
  }

  // Iniciar novo jogo
  function startNewGame(): void {
    if (!socket.value) return

    socket.value.emit('start_new_game', {})
  }

  // Alterar dificuldade
  function changeDifficulty(newDifficulty: string): void {
    if (!socket.value) return

    socket.value.emit('change_difficulty', {
      difficulty: newDifficulty
    })
  }

  // Sair do jogo
  function leaveGame(): void {
    if (socket.value) {
      socket.value.emit('leave_game', {})
      socket.value.disconnect()
    }
    resetState()
  }

  // Resetar estado
  function resetState(): void {
    connected.value = false
    gameId.value = ''
    players.value = []
    currentWord.value = ''
    nextLetter.value = ''
    nextLetterIndex.value = 0
    difficulty.value = 'normal'
    gameStarted.value = false
    currentPlayer.value = null
    myPlayerId.value = ''
    hostId.value = ''
    messages.value = []
    lastError.value = ''
  }

  // Adicionar mensagem
  function addMessage(sender: string, content: string): void {
    messages.value.push({
      id: Date.now(),
      sender,
      content,
      timestamp: new Date().toLocaleTimeString()
    })
  }

  // Limpar erro
  function clearError(): void {
    lastError.value = ''
  }

  return {
    // Estado
    socket,
    connected,
    gameId,
    playerName,
    players,
    currentWord,
    nextLetter,
    nextLetterIndex,
    difficulty,
    gameStarted,
    currentPlayer,
    myPlayerId,
    hostId,
    messages,
    lastError,

    // Computed
    isConnected,
    isMyTurn,
    amIHost,

    // Métodos
    connect,
    submitWord,
    startNewGame,
    changeDifficulty,
    leaveGame,
    resetState,
    addMessage,
    clearError
  }
})