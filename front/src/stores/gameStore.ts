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

  // Configurações da sala
  const roomSettings = ref({
    defaultTime: 30, // tempo padrão em segundos
    difficulty: 'normal' // fácil, normal, difícil
  })

  // Timer state
  const remainingTime = ref<number>(0)
  const timerActive = ref<boolean>(false)
  const isVictoryState = ref<boolean>(false)
  const winner = ref<string>('')

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

    // Conecta ao Socket.IO usando variável de ambiente VITE_SOCKET_URL (configurável no Vercel)
    // Fallback para localhost:8000 para desenvolvimento local
    const SOCKET_URL = (import.meta.env.VITE_SOCKET_URL as string) || 'http://localhost:8000'

    socket.value = io(SOCKET_URL, {
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

  // Função auxiliar para atualizar host
  function updateHostInfo(playersData: Player[]): void {
    if (playersData && playersData.length > 0) {
      const host = playersData.find(p => p.is_host)
      if (host) {
        hostId.value = host.id
      }
    }
  }

  // Função auxiliar para resetar timer
  function resetTimer(): void {
    timerActive.value = false
    remainingTime.value = 0
  }

  // Handler principal para eventos do jogo
  function handleGameEvent(data: any): void {
    console.log('🎲 Evento do jogo:', data)

    switch (data.type) {
      case 'player_joined':
        players.value = data.players || []
        currentPlayer.value = data.current_player || null
        updateHostInfo(players.value)

        // Salvar meu ID se for minha entrada
        if (data.player === playerName.value && data.player_id) {
          myPlayerId.value = data.player_id
        }

        // Atualizar configurações da sala se fornecidas
        if (data.room_settings) {
          roomSettings.value.defaultTime = data.room_settings.default_time || 30
          roomSettings.value.difficulty = data.room_settings.difficulty || 'normal'
          difficulty.value = data.room_settings.difficulty || 'normal'
          console.log('⚙️ Configurações da sala atualizadas (player_joined):', roomSettings.value)
        }

        addMessage('Sistema', `${data.player} entrou na sala`)
        break

      case 'player_left':
        players.value = data.players || []
        updateHostInfo(players.value)
        currentPlayer.value = data.current_player || null

        if (data.was_current_player) {
          addMessage('Sistema', `${data.player} saiu durante sua vez - vez passou para o próximo jogador`)
        } else {
          addMessage('Sistema', `${data.player} saiu da sala`)
        }
        break

      case 'game_started':
        gameStarted.value = true
        currentWord.value = data.current_word || data.initial_word || data.word || ''
        nextLetter.value = data.next_letter || ''
        nextLetterIndex.value = data.next_letter_index || 0
        players.value = data.players || []
        currentPlayer.value = data.current_player || null
        updateHostInfo(players.value)

        // Atualizar configurações da sala se fornecidas
        if (data.room_settings) {
          roomSettings.value.defaultTime = data.room_settings.default_time || 30
          roomSettings.value.difficulty = data.room_settings.difficulty || 'normal'
          difficulty.value = data.room_settings.difficulty || 'normal'
          console.log('⚙️ Configurações da sala atualizadas (game_started):', roomSettings.value)
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
        updateHostInfo(players.value)
        addMessage(data.player || 'Alguém', data.word || '')
        break

      case 'player_eliminated':
        players.value = data.players || []
        currentPlayer.value = data.current_player || null
        updateHostInfo(players.value)
        addMessage('Sistema', `${data.player} foi eliminado!`)
        break

      case 'game_over':
        gameStarted.value = false
        addMessage('Sistema', `🏆 Jogo terminou! Vencedor: ${data.winner}`)
        break

      case 'game_ended':
        gameStarted.value = false
        currentWord.value = ''
        nextLetter.value = ''
        nextLetterIndex.value = 0
        currentPlayer.value = null
        players.value = data.players || []
        // Atualiza o host
        if (players.value.length > 0) {
          const host = players.value.find(p => p.is_host)
          if (host) {
            hostId.value = host.id
          }
        }
        addMessage('Sistema', `⏸️ ${data.reason || 'Jogo encerrado'}`)
        break

      case 'error':
        lastError.value = data.message || 'Erro desconhecido'
        addMessage('Erro', data.message || 'Erro desconhecido')
        break

      case 'difficulty_changed':
        difficulty.value = data.difficulty || 'normal'
        addMessage('Sistema', `Dificuldade alterada para: ${data.difficulty}`)
        break

      case 'room_settings_updated':
        if (data.settings) {
          roomSettings.value.defaultTime = data.settings.default_time || 30
          roomSettings.value.difficulty = data.settings.difficulty || 'normal'

          // Mapear dificuldade do backend para exibição
          const difficultyDisplay: Record<string, string> = {
            'easy': 'Fácil',
            'normal': 'Normal',
            'caotic': 'Difícil'
          }

          // Atualizar a dificuldade do jogo (para compatibilidade com sistema existente)
          const backendDifficulty: Record<string, string> = {
            'fácil': 'easy',
            'normal': 'normal',
            'difícil': 'caotic'
          }

          const settingsDifficulty = data.settings.difficulty || 'normal'
          difficulty.value = backendDifficulty[settingsDifficulty] || settingsDifficulty

          const displayDiff = difficultyDisplay[difficulty.value] || settingsDifficulty
          addMessage('Sistema', `⚙️ Configurações atualizadas: ${data.settings.default_time}s, ${displayDiff}`)
        }
        break

      case 'settings_update_denied':
        lastError.value = data.reason || 'Não foi possível alterar as configurações'
        break

      case 'difficulty_change_denied':
        lastError.value = data.reason || 'Não foi possível alterar a dificuldade'
        break

      case 'start_game_denied':
        lastError.value = data.reason || 'Não foi possível iniciar o jogo'
        break

      case 'word_rejected':
        lastError.value = data.reason || 'Palavra rejeitada'
        // Mostrar a tentativa no chat para todos verem
        const rejectedWord = data.word || 'palavra'
        const rejectedByPlayer = data.player || 'Alguém'
        addMessage(rejectedByPlayer, `${rejectedWord} ❌`)
        addMessage('Sistema', `❌ "${rejectedWord}" foi rejeitada: ${data.reason}`)
        break

      case 'timer_started':
        timerActive.value = true
        // Usar o tempo das configurações da sala se remaining_time não estiver disponível
        const startTime = data.remaining_time || roomSettings.value.defaultTime || 30
        remainingTime.value = startTime
        currentPlayer.value = data.current_player || null
        console.log('🕐 Timer iniciado:', {
          received_time: data.remaining_time,
          room_default: roomSettings.value.defaultTime,
          final_time: startTime
        })
        break

      case 'timer_update':
        remainingTime.value = data.remaining_time || 0
        currentPlayer.value = data.current_player || null
        break

      case 'time_penalty':
        remainingTime.value = data.remaining_time || 0
        currentPlayer.value = data.current_player || null
        addMessage('Sistema', `⏰ Penalização de tempo: -${data.penalty}s`)
        break

      case 'time_up':
        timerActive.value = false
        remainingTime.value = 0
        players.value = data.players || []
        currentPlayer.value = data.current_player || null
        // Atualiza o host
        if (players.value.length > 0) {
          const host = players.value.find(p => p.is_host)
          if (host) {
            hostId.value = host.id
          }
        }
        addMessage('Sistema', `⏰ Tempo esgotado! ${data.eliminated_player} foi eliminado`)
        break

      case 'victory':
        isVictoryState.value = true
        winner.value = data.winner || 'Nenhum vencedor'
        gameStarted.value = false
        resetTimer()
        players.value = data.players || []
        addMessage('Sistema', `🏆 Vitória! Vencedor: ${data.winner}`)
        break

      case 'game_reset':
        gameStarted.value = false
        isVictoryState.value = false
        winner.value = ''
        resetTimer()
        currentWord.value = ''
        nextLetter.value = ''
        nextLetterIndex.value = 0
        currentPlayer.value = null
        players.value = data.players || []
        updateHostInfo(players.value)
        addMessage('Sistema', '🔄 Jogo reiniciado')
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

  // Funções de configuração
  function updateRoomSettings(settings: { defaultTime?: number; difficulty?: string }): void {
    console.log('📤 updateRoomSettings chamado com:', settings)
    console.log('📊 Estado atual roomSettings:', roomSettings.value)

    if (settings.defaultTime !== undefined) {
      roomSettings.value.defaultTime = settings.defaultTime
      console.log('🕐 defaultTime atualizado para:', settings.defaultTime)
    }
    if (settings.difficulty !== undefined) {
      roomSettings.value.difficulty = settings.difficulty
      console.log('⚙️ difficulty atualizada para:', settings.difficulty)
    }

    console.log('📊 Novo estado roomSettings:', roomSettings.value)

    // Enviar configurações para o servidor
    if (socket.value && amIHost.value) {
      // Converter camelCase para snake_case para o backend
      const payload = {
        game_id: gameId.value,
        settings: {
          default_time: roomSettings.value.defaultTime,
          difficulty: roomSettings.value.difficulty
        }
      }
      console.log('🚀 Enviando configurações para servidor:', payload)
      socket.value.emit('update_room_settings', payload)
    } else {
      console.log('❌ Não foi possível enviar para servidor:', {
        hasSocket: !!socket.value,
        isHost: amIHost.value,
        gameId: gameId.value
      })
    }
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
    roomSettings,

    // Timer state
    remainingTime,
    timerActive,
    isVictoryState,
    winner,

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
    clearError,
    updateRoomSettings
  }
})