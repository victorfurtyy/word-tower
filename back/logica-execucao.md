# 📋 Lógica de Execução - Word Tower Game

Este documento descreve o fluxo completo de comunicação entre o frontend e backend via Socket.IO.

## 🔌 Conexão Inicial

### Frontend envia:
```js
const socket = io('http://localhost:8000');
// Conexão automática via Socket.IO
```

### Backend responde:
```js
socket.on('message', (data) => {
    console.log(data); // "Bem-vindo ao servidor!"
});
```

---

## 🚪 1. Entrada na Sala

### Frontend envia:
```js
socket.emit('join_game', {
    game_id: 'sala123',        // ID da sala (obrigatório)
    player_name: 'João'        // Nome do jogador (opcional, default: "Anonymous")
});
```

### Backend responde:
```js
socket.on('game_event', (data) => {
    if (data.type === 'player_joined') {
        // Dados recebidos:
        data.player;           // Nome do jogador que entrou
        data.total_players;    // Total de jogadores na sala
        data.difficulty;       // Dificuldade atual da sala
    }
});
```

**✅ Lógica:** Se a sala não existir, será criada automaticamente. Todos os jogadores da sala são notificados.

---

## ⚙️ 2. Alterar Dificuldade (Opcional)

### Frontend envia:
```js
socket.emit('change_difficulty', {
    difficulty: 'caotic'  // 'normal', 'easy', 'caotic'
});
```

### Backend responde:

**✅ Sucesso:**
```js
socket.on('game_event', (data) => {
    if (data.type === 'difficulty_changed') {
        data.difficulty;  // Nova dificuldade
        data.message;     // "Dificuldade alterada para: caotic"
    }
});
```

**❌ Erro:**
```js
socket.on('game_event', (data) => {
    if (data.type === 'difficulty_change_denied') {
        data.reason;  // "Não é possível alterar dificuldade durante o jogo"
    }
    // OU
    if (data.type === 'error') {
        data.message; // Mensagem de erro específica
    }
});
```

**⚠️ Restrições:** 
- Só funciona quando `game_state = "waiting"`
- Jogador deve estar na sala

---

## 🎮 3. Iniciar o Jogo

### Frontend envia:
```js
socket.emit('start_new_game', {});
```

### Backend responde:

**✅ Sucesso:**
```js
socket.on('game_event', (data) => {
    if (data.type === 'game_started') {
        data.initial_word;        // Palavra inicial sorteada
        data.current_word;        // Palavra atual (igual à inicial)
        data.next_letter;         // Próxima letra que deve começar a palavra
        data.next_letter_index;   // Posição da letra na palavra
        data.round_number;        // Número da rodada
        data.difficulty;          // Dificuldade da partida
    }
});
```

**❌ Erro:**
```js
socket.on('game_event', (data) => {
    if (data.type === 'start_game_denied') {
        data.reason;  // "Mínimo 2 jogadores necessário" ou "Jogo já em andamento"
    }
});
```

**⚠️ Restrições:**
- Mínimo 2 jogadores na sala
- `game_state` deve ser "waiting"

---

## 📝 4. Enviando Palavras

### Frontend envia:
```js
socket.emit('submit_word', {
    word: 'abacaxi'  // Palavra que deve começar com a letra indicada
});
```

### Backend responde:

**✅ Palavra Aceita:**
```js
socket.on('game_event', (data) => {
    if (data.type === 'word_accepted') {
        data.player;              // Nome do jogador que enviou
        data.word;                // Palavra aceita
        data.current_word;        // Nova palavra atual
        data.next_letter;         // Próxima letra obrigatória
        data.next_letter_index;   // Posição da letra
    }
});
```

**❌ Palavra Rejeitada:**
```js
socket.on('game_event', (data) => {
    if (data.type === 'word_invalid') {
        data.word;    // Palavra rejeitada
        data.reason;  // Motivo: "Palavra não encontrada no dicionário!" 
                      // ou "A palavra deve começar com 'a'"
    }
});
```

**📋 Validações do Backend:**
1. Palavra existe no dicionário da dificuldade
2. Começa com a letra correta
3. Jogador está ativo na sala

---

## ⏰ 5. Timeout de Jogador

### Frontend envia:
```js
socket.emit('player_timeout', {
    player_name: 'João'  // Nome do jogador que teve timeout
});
```

### Backend responde:
```js
socket.on('game_event', (data) => {
    if (data.type === 'player_eliminated') {
        data.eliminated_player;  // Nome do jogador eliminado
        data.active_players;     // Quantidade de jogadores ativos
        data.player;            // Mesmo que eliminated_player
    }
});
```

**✅ Confirmação individual:**
```js
socket.on('game_event', (data) => {
    if (data.type === 'timeout_handled') {
        data.player;  // Nome do jogador que teve timeout processado
    }
});
```

**⚠️ Comportamento:** Jogador é desativado mas **não removido** da sala.

---

## 🏆 6. Fim da Rodada

### Backend envia automaticamente:
```js
socket.on('game_event', (data) => {
    if (data.type === 'round_ended') {
        data.winner;        // Nome do vencedor (null se empate)
        data.round_number;  // Número da próxima rodada
        data.scores;        // Objeto: { "João": 2, "Maria": 1 }
    }
});
```

**✅ Estado após fim:** `game_state = "waiting"` (permite alterar dificuldade novamente)

---

## 🚪 7. Sair da Sala

### Frontend envia:
```js
socket.emit('leave_game', {});
```

### Backend responde:

**Para quem saiu:**
```js
socket.on('game_event', (data) => {
    if (data.type === 'left_game') {
        // Confirmação de saída
    }
});
```

**Para outros jogadores:**
```js
socket.on('game_event', (data) => {
    if (data.type === 'player_left') {
        data.player;         // Nome do jogador que saiu
        data.total_players;  // Jogadores restantes
    }
});
```

---

## 🔌 8. Desconexão Automática

### Quando o cliente desconecta:
```js
// Backend automaticamente:
// 1. Remove jogador da sala
// 2. Notifica outros jogadores
// 3. Remove sala se vazia
```

**Outros jogadores recebem:**
```js
socket.on('game_event', (data) => {
    if (data.type === 'player_left') {
        data.player;         // Nome do jogador desconectado
        data.total_players;  // Jogadores restantes
    }
});
```

---

## 📊 Estados do Jogo

| Estado | Ações Permitidas |
|--------|------------------|
| `"waiting"` | ✅ Alterar dificuldade<br>✅ Iniciar jogo<br>✅ Entrar/sair |
| `"playing"` | ❌ Alterar dificuldade<br>❌ Iniciar novo jogo<br>✅ Enviar palavras<br>✅ Timeout jogadores |

---

## 🎯 Fluxo Completo Exemplo

```js
// 1. Conectar e entrar na sala
socket.emit('join_game', { game_id: 'sala123', player_name: 'João' });

// 2. Alterar dificuldade (opcional)
socket.emit('change_difficulty', { difficulty: 'caotic' });

// 3. Iniciar jogo (quando tiver 2+ jogadores)
socket.emit('start_new_game', {});

// 4. Jogar (enviar palavras)
socket.emit('submit_word', { word: 'casa' });     // next_letter: 'a'
socket.emit('submit_word', { word: 'abacaxi' });  // next_letter: 'i'
socket.emit('submit_word', { word: 'igreja' });   // next_letter: 'a'

// 5. Se jogador demorar muito
socket.emit('player_timeout', { player_name: 'Maria' });

// 6. Quando sobrar 1 jogador → rodada acaba automaticamente
// 7. Repetir processo ou sair
socket.emit('leave_game', {});
```

---

## 🚨 Tratamento de Erros

### Sempre escute eventos de erro:
```js
socket.on('game_event', (data) => {
    switch(data.type) {
        case 'error':
        case 'difficulty_change_denied':
        case 'start_game_denied':
        case 'word_invalid':
            console.error('Erro:', data.reason || data.message);
            // Mostrar mensagem para usuário
            break;
    }
});
```

### Reconexão automática:
```js
socket.on('reconnect', () => {
    console.log('Reconectado ao servidor');
    // Reenviar join_game se necessário
});
```

---

## 📋 Checklist de Implementação Frontend

- [ ] Conectar ao Socket.IO
- [ ] Implementar `join_game`
- [ ] Escutar `player_joined` e `player_left`
- [ ] Implementar `change_difficulty` (com tratamento de erro)
- [ ] Implementar `start_new_game` (com validações)
- [ ] Escutar `game_started`
- [ ] Implementar `submit_word`
- [ ] Escutar `word_accepted` e `word_invalid`
- [ ] Implementar timer e `player_timeout`
- [ ] Escutar `player_eliminated` e `round_ended`
- [ ] Implementar `leave_game`
- [ ] Tratar reconexões e desconexões
- [ ] Interface para mostrar erros ao usuário
