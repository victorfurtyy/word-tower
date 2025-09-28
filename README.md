# 🏗️ Word Tower

**Jogo de palavras multijogador em tempo real com sistema de eliminação por timeout**

_Projeto desenvolvido para a disciplina de Programação I (Ciência da Computação - UFCG, Campina Grande)_

---

## 📖 Sumário

1. [Como Rodar a Aplicação](#-como-rodar-a-aplicação)
2. [Como Jogar](#-como-jogar)
3. [Regras do Jogo](#-regras-do-jogo)
4. [Tecnologias](#-tecnologias)

---

## 🚀 Como Rodar a Aplicação

### Windows

#### Pré-requisitos

- Python 3.8+ ([Download](https://www.python.org/downloads/))
- Node.js 16+ ([Download](https://nodejs.org/))
- Git ([Download](https://git-scm.com/download/win))

#### Passo a Passo

**1. Clone o repositório**

```cmd
git clone https://github.com/KJSS3012/word-tower.git
cd word-tower
```

**2. Configure o Backend**

```cmd
cd back
pip install fastapi uvicorn python-socketio
python -m app.main
```

_Backend rodará em `http://localhost:8000`_

**3. Configure o Frontend (nova janela do terminal)**

```cmd
cd front
npm install
npm run dev
```

_Frontend rodará em `http://localhost:5173`_

**4. Acesse o jogo**

- Abra `http://localhost:5173` no navegador
- Crie ou entre em uma sala
- Convide amigos compartilhando o link da sala!

### Linux

#### Pré-requisitos

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip nodejs npm git

# Arch Linux
sudo pacman -S python python-pip nodejs npm git

# CentOS/RHEL
sudo yum install python3 python3-pip nodejs npm git
```

#### Passo a Passo

**1. Clone o repositório**

```bash
git clone https://github.com/KJSS3012/word-tower.git
cd word-tower
```

**2. Configure o Backend**

```bash
cd back
pip3 install fastapi uvicorn python-socketio
python3 -m app.main
```

_Backend rodará em `http://localhost:8000`_

**3. Configure o Frontend (novo terminal)**

```bash
cd front
npm install
npm run dev
```

_Frontend rodará em `http://localhost:5173`_

**4. Acesse o jogo**

- Abra `http://localhost:5173` no navegador
- Crie ou entre em uma sala
- Convide amigos compartilhando o link da sala!

---

## 🎮 Como Jogar

### Objetivo

Ser o último jogador sobrevivente! Digite palavras válidas que comecem com a letra indicada antes que o tempo acabe.

### Fluxo do Jogo

**1. Entrando na Sala**

- Acesse o jogo pelo navegador
- Digite seu nome de jogador
- Crie uma nova sala ou entre em uma existente

**2. Configuração (apenas o host)**

- **Fácil**: Palavras sem acentos, próxima letra sempre vem do final
- **Normal**: Palavras com acentos, próxima letra sempre vem do final
- **Caótico**: Palavras com acentos, próxima letra vem de posição aleatória

**3. Durante o Jogo**

- Uma palavra inicial é sorteada automaticamente
- Cada jogador tem **30 segundos** para digitar uma palavra válida
- A palavra deve começar com a letra destacada
- Timer reinicia a cada palavra aceita
- **Palavra errada = -5 segundos de penalidade**
- **Tempo zerado = eliminação definitiva**

**4. Condições de Vitória**

- Último jogador ativo vence a partida
- Jogo reinicia automaticamente após vitória
- Jogadores desconectados são automaticamente eliminados

### Exemplos de Gameplay

**Modo Normal:**

```
Palavra atual: "CASA"
Próxima letra: "A" (sempre a última)
Você digita: "ABACAXI"
Nova palavra: "ABACAXI"
Próxima letra: "I"
```

**Modo Caótico:**

```
Palavra atual: "BRASIL"
Próxima letra: "A" (sorteada aleatoriamente)
Você digita: "AVIÃO"
Nova palavra: "AVIÃO"
Próxima letra: "I" (nova posição sorteada)
```

### Dicas de Estratégia

- 🧠 **Pense rápido**: 30 segundos passam voando!
- 📚 **Vocabulário amplo**: Quanto mais palavras você souber, melhor
- ⚡ **Mode Caótico**: Mais desafiador, qualquer letra pode sair
- 🎯 **Evite erros**: Penalidades de tempo são fatais
- 🤝 **Jogue em grupo**: Mais divertido com 3-6 jogadores

---

## 📋 Regras do Jogo

### Regras Básicas

- ✅ **Objetivo**: Sobreviver sendo o último jogador ativo
- ⏱️ **Tempo**: 30 segundos por turno + reinicia a cada palavra aceita
- 🔤 **Validação**: Palavras verificadas em dicionário português
- ❌ **Penalização**: -5 segundos por palavra incorreta
- 💀 **Eliminação**: Tempo zerado = fora do jogo
- 🔄 **Desconexão**: Jogador sai = eliminação automática

### Modos de Dificuldade

| Modo               | Dicionário | Próxima Letra       | Dificuldade |
| ------------------ | ----------- | -------------------- | ----------- |
| **Fácil**   | Sem acentos | Última posição    | ⭐          |
| **Normal**   | Com acentos | Última posição    | ⭐⭐        |
| **Caótico** | Com acentos | Posição aleatória | ⭐⭐⭐      |

### Sistema de Turnos

- 🎲 **Início**: Palavra inicial sorteada automaticamente
- 🔄 **Alternância**: Jogadores se revezam em ordem
- ⏰ **Timer**: 30s por jogador, reinicia após palavra aceita
- 🎯 **Continuidade**: Jogo continua mesmo se jogadores saírem
- 🏆 **Vitória**: Último ativo vence, jogo reinicia em 5s

---

## 💻 Tecnologias

### Backend

- **Python 3.8+**: Linguagem principal
- **FastAPI**: Framework web moderno e rápido
- **Socket.IO**: Comunicação em tempo real
- **AsyncIO**: Programação assíncrona para timers

### Frontend

- **Vue 3**: Framework reativo moderno
- **TypeScript**: Tipagem estática
- **Pinia**: Gerenciamento de estado
- **Vite**: Build tool rápido

### Comunicação

- **WebSocket**: Tempo real para gameplay
- **JSON**: Formato de troca de dados

---

## 🎓 Créditos

**Projeto Acadêmico**

- **Disciplina**: Programação I
- **Instituição**: Universidade Federal de Campina Grande (UFCG)
- **Curso**: Ciência da Computação

**Word Tower** © 2025
