# Word Tower

Projeto em desenvolvimento para a disciplina de Programação I (Ciência da Computação - UFCG, Campina Grande).

## 🎮 Sobre o Jogo
Word Tower é um jogo de palavras multijogador em tempo real onde o objetivo é digitar uma palavra válida que comece com a última letra da palavra anterior. A cada rodada, uma palavra é escolhida aleatoriamente para iniciar a sequência.

## 📋 Regras do Jogo

### Regras Básicas
- **Objetivo**: Digite uma palavra que comece com a última letra da palavra anterior
- **Tempo limite**: Cada jogador tem 10-15 segundos para enviar uma palavra
- **Validação**: Todas as palavras são verificadas no dicionário
- **Eliminação**: Jogadores são eliminados se:
  - Enviarem uma palavra inválida (não existe no dicionário), diminuindo seu tempo
  - Enviarem uma palavra que não comece com a letra correta, diminuindo seu tempo
  - O tempo esgotar - Fim definitivo

### Dificuldades
- **Easy**: Usa dicionário sem acentos (`sem_acento.txt`) - letra sempre vem da última posição
- **Normal**: Usa dicionário com acentos (`com_acento.txt`) - letra sempre vem da última posição  
- **Caotic**: Usa dicionário com acentos + letra sorteada de posição aleatória da palavra

### Sistema de Rodadas
- **Início**: Palavra inicial sorteada aleatoriamente
- **Turnos**: Jogadores se alternam para enviar palavras
- **Fim de rodada**: Quando resta apenas 1 jogador ativo
- **Pontuação**: O vencedor da rodada ganha 1 ponto
- **Nova rodada**: Todos os jogadores voltam a estar ativos

## 🚀 Como Jogar

### 1. Conectar ao Jogo
```
WebSocket: /game/{game_id}
```

**Primeira mensagem obrigatória:**
```json
{
  "type": "join_game",
  "player_name": "SeuNome"
}
```

### 2. Fluxo do Jogo
1. **Entrada na sala**: Jogador se conecta e envia dados de entrada
2. **Configuração**: Definir dificuldade da sala (opcional)
3. **Início do jogo**: Enviado `start_new_game` para começar
4. **Palavra inicial**: Sistema sorteia palavra e informa a todos
5. **Jogadas**: Jogadores enviam palavras válidas em sequência
6. **Fim de rodada**: Último jogador ativo vence e ganha ponto

## 🔌 API Endpoints

### WebSocket
```
GET /game/{game_id}
```
**Parâmetros de Query:**
- `player_name`: Nome do jogador
- `difficulty`: "easy", "normal" ou "caotic" (padrão: "normal")

### HTTP Routes
```
POST /game/{game_id}/start
```
Inicia uma nova partida (alternativa ao WebSocket)

```
POST /game/{game_id}/timeout/{player_name}
```
Elimina um jogador por timeout (chamado pelo frontend)

## 📡 Mensagens WebSocket

### Mensagens Enviadas pelo Cliente

#### Entrar no Jogo (primeira mensagem obrigatória)
```json
{
  "type": "join_game",
  "player_name": "SeuNome"
}
```

#### Enviar Palavra
```json
{
  "type": "submit_word",
  "word": "exemplo"
}
```

#### Iniciar Nova Partida
```json
{
  "type": "start_new_game"
}
```

#### Alterar Dificuldade da Sala
```json
{
  "type": "change_difficulty",
  "difficulty": "caotic"
}
```

#### Sair do Jogo
```json
{
  "type": "leave_game"
}
```

### Mensagens Recebidas do Servidor

#### Jogador Entrou
```json
{
  "type": "player_joined",
  "player": "João",
  "total_players": 3,
  "difficulty": "normal"
}
```

#### Jogo Iniciado
```json
{
  "type": "game_started",
  "initial_word": "casa",
  "current_word": "casa",
  "next_letter": "a",
  "next_letter_index": 3,
  "round_number": 1,
  "difficulty": "normal"
}
```

#### Palavra Aceita
```json
{
  "type": "word_accepted",
  "player": "João",
  "word": "abacaxi",
  "current_word": "abacaxi",
  "next_letter": "i",
  "next_letter_index": 6
}
```

#### Palavra Inválida
```json
{
  "type": "word_invalid",
  "word": "xpto",
  "reason": "Palavra não encontrada no dicionário!"
}
```

#### Jogador Eliminado
```json
{
  "type": "player_eliminated",
  "player": "João",
  "active_players": 2,
  "eliminated_player": "João"
}
```

#### Dificuldade Alterada
```json
{
  "type": "difficulty_changed",
  "difficulty": "caotic",
  "message": "Dificuldade alterada para: caotic"
}
```

#### Fim de Rodada
```json
{
  "type": "round_ended",
  "winner": "Maria",
  "round_number": 2,
  "scores": {
    "João": 0,
    "Maria": 1,
    "Pedro": 0
  }
}
```

## 🏗️ Arquitetura

### Tecnologias
- **Backend**: Python + FastAPI + WebSocket
- **Dicionários**: Arquivos de texto com palavras válidas
- **Comunicação**: Tempo real via WebSocket

### Estrutura do Projeto
```
app/
├── main.py                 # Aplicação principal
├── ws/
│   └── game_manager.py     # Gerenciador de jogos WebSocket
├── classes/
│   └── player.py           # Classe Player
├── utils/
│   └── dictionary.py       # Validação de palavras
└── assets/
    └── dicts/
        ├── com_acento.txt  # Dicionário normal
        └── sem_acento.txt  # Dicionário fácil
```

### Responsabilidades

#### Backend
- ✅ Validação de palavras no dicionário
- ✅ Verificação de letra inicial correta
- ✅ Gerenciamento de salas e jogadores
- ✅ Sistema de 3 dificuldades (Easy/Normal/Caotic)
- ✅ Comunicação WebSocket
- ✅ Sistema de índices para destacar letras

#### Frontend (a ser desenvolvido)
- 🎮 Controle de turnos e tempo
- 🎮 Interface do usuário
- 🎮 Gerenciamento de estado do jogo
- 🎮 Cronômetro e timeouts
- 🎮 Destaque visual das letras baseado no índice

### Funcionalidades do Exemplo:

- ✅ **Conexão WebSocket** com configuração limpa via mensagens
- ✅ **Controle de dificuldade** por sala (não por jogador individual)
- ✅ **Destaque visual** da letra baseado no `next_letter_index`
- ✅ **Interface completa** para jogar
- ✅ **Log de mensagens** em tempo real
- ✅ **Placar** com pontuação dos jogadores
- ✅ **Controles** para iniciar/sair do jogo
- ✅ **Diferentes modos** (Easy/Normal/Caotic) com visual único

### Destaque da Letra:

No modo **Caótico**, a letra pode ser destacada em qualquer posição:
```
Normal/Easy: "abacax[i]" (sempre a última)
Caótico: "ab[a]caxi" (posição aleatória sorteada)
```

## 🛠️ Como Executar

### Backend
```bash
# Instalar dependências
pip install fastapi uvicorn

# Executar servidor
python app/main.py
```

O servidor estará disponível em `http://localhost:8000`

## 📖 Exemplo de Uso Rápido

1. **Conectar**: WebSocket em `/game/sala123`
2. **Entrar**: Envie primeira mensagem `{"type": "join_game", "player_name": "João"}`
3. **Configurar**: Envie `{"type": "change_difficulty", "difficulty": "caotic"}` (opcional)
4. **Iniciar**: Envie `{"type": "start_new_game"}`
5. **Jogar**: Envie `{"type": "submit_word", "word": "abacaxi"}`
6. **Visualizar**: Use `next_letter_index` para destacar a letra na interface

## 🤝 Contribuição
Sugestões e contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

---

> **Projeto Acadêmico** - UFCG - Programação I