# 🏗️ Word Tower

**Jogo de palavras multijogador em tempo real com sistema de eliminação por timeout**

_Projeto desenvolvido para a disciplina de Programação I (Ciência da Computação - UFCG, Campina Grande)_

---

## 🚀 Como Rodar a Aplicação

### 📋 Pré-requisitos

- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **Node.js 20+** ([Download](https://nodejs.org/))

### 🛠️ Instalação

#### Opção 1: Instalação Simples (pip global)

```bash
# 1. Clone o projeto
git clone https://github.com/KJSS3012/word-tower.git
cd word-tower

# 2. Instalar dependências Python
cd back
pip install -r requirements.txt

# 3. Instalar dependências Node.js (novo terminal)
cd ../front
npm install
```

#### Opção 2: Instalação com Ambiente Virtual (Recomendado)

```bash
# 1. Clone o projeto
git clone https://github.com/KJSS3012/word-tower.git
cd word-tower

# 2. Criar ambiente virtual
cd back
python -m venv venv

# 3. Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 4. Instalar dependências Python
pip install -r requirements.txt

# 5. Instalar dependências Node.js (novo terminal)
cd ../front
npm install
```

### ▶️ Executar

**Terminal 1 - Backend:**

```bash
cd back
python -m app.main
```

> Backend rodará em `http://localhost:8000`

**Terminal 2 - Frontend:**

```bash
cd front
npm run dev
```

> Frontend rodará em `http://localhost:5173`

### 🌐 Acessar

Abra `http://localhost:5173` no navegador e divirta-se!

---

## 🎮 Como Jogar

### 🚪 Entrando no Jogo

1. **Crie uma sala** ou **entre em uma existente** usando o código
2. **Aguarde outros jogadores** (mínimo 2 para iniciar)
3. **Host inicia o jogo** quando todos estiverem prontos

### 🎯 Objetivo

Formar uma "torre de palavras" onde cada palavra deve começar com a **última letra** da palavra anterior.

### ⏰ Sistema de Tempo

- **30 segundos** por turno (configurável)
- **Timer visual** mostra tempo restante
- **Eliminação automática** quando tempo esgota

### 🏆 Vitória

- **Último jogador ativo** vence a rodada
- **Jogo reinicia** automaticamente para nova partida

---

## 📝 Regras do Jogo

### ✅ Palavra Válida

- Deve começar com a **letra correta**
- Deve ser uma **palavra real** (verificada no dicionário)
- **Não pode repetir** palavras já usadas

### ❌ Palavra Inválida

- **Letra errada**: Eliminação imediata
- **Palavra inexistente**: Eliminação imediata
- **Palavra repetida**: Eliminação imediata

### 🎲 Dificuldades

| Dificuldade | Dicionário  | Próxima Letra     | Desafio |
| ----------- | ----------- | ----------------- | ------- |
| **Fácil**   | Sem acentos | Última letra      | ⭐      |
| **Normal**  | Com acentos | Última letra      | ⭐⭐    |
| **Caótico** | Com acentos | Posição aleatória | ⭐⭐⭐  |

---

## 💻 Tecnologias

### Backend

- **Python 3.8+**: Linguagem principal
- **Socket.IO**: Comunicação em tempo real
- **uvicorn**: Servidor ASGI para WebSockets
- **AsyncIO**: Programação assíncrona para timers

### Frontend

- **Vue 3**: Framework reativo moderno
- **TypeScript**: Tipagem estática
- **Pinia**: Gerenciamento de estado
- **Socket.IO Client**: Comunicação real-time

### Comunicação

- **WebSocket**: Tempo real para gameplay
- **JSON**: Formato de troca de dados

---

## 📦 Dependências

### Backend (Python)

```txt
uvicorn[standard]==0.24.0    # Servidor ASGI
python-socketio[asyncio]==5.10.0    # Socket.IO server
```

### Frontend (Node.js)

```json
{
  "vue": "^3.5.18",
  "typescript": "latest",
  "pinia": "^3.0.3",
  "socket.io-client": "^4.8.1",
  "vue-router": "^4.5.1"
}
```

---

## 🎓 Créditos

**Projeto Acadêmico**

- **Disciplina**: Programação I
- **Instituição**: Universidade Federal de Campina Grande (UFCG)
- **Curso**: Ciência da Computação

**Word Tower** © 2025
