
import json
import random

import socketio
from app.utils.dictionary import verify_word, get_random_word, get_random_letter_from_word
from app.classes.player import Player
from fastapi import FastAPI as FastAPIReal
from starlette.middleware.cors import CORSMiddleware

# Cria o servidor Socket.IO ASGI
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=['http://localhost:5173'])
fastapi_app = FastAPIReal()
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)


class GameManager:
    def __init__(self):
        self.rooms: dict[str, dict] = {}  # {game_id: {players: [], current_word: str, game_state: str}}

    async def connect(self, game_id: str, sid: str, player_name: str):
        if game_id not in self.rooms:
            self.rooms[game_id] = {
                "players": [],
                "current_word": "",
                "game_state": "waiting",  # waiting, playing, ended
                "round_number": 1,
                "difficulty": "normal"  # Dificuldade padrão da sala
            }
        player = Player(player_name, sid)
        self.rooms[game_id]["players"].append(player)
        await sio.save_session(sid, {"game_id": game_id, "player_name": player_name})
        await sio.enter_room(sid, game_id)
        # Notifica todos os jogadores sobre o novo player
        await self.broadcast_to_room(game_id, {
            "type": "player_joined",
            "player": player_name,
            "total_players": len(self.rooms[game_id]["players"]),
            "difficulty": self.rooms[game_id]["difficulty"]
        })

    async def disconnect(self, game_id: str, sid: str):
        if game_id not in self.rooms:
            return
        # Encontra e remove o player
        player_name = None
        for i, player in enumerate(self.rooms[game_id]["players"]):
            if player.websocket == sid:
                player_name = player.name
                self.rooms[game_id]["players"].pop(i)
                break
        # Notifica outros jogadores sobre a saída
        if player_name:
            await self.broadcast_to_room(game_id, {
                "type": "player_left",
                "player": player_name,
                "total_players": len(self.rooms[game_id]["players"])
            })
        # Remove sala se vazia
        if not self.rooms[game_id]["players"]:
            del self.rooms[game_id]

    async def eliminate_player(self, game_id: str, player_name: str):
        """Elimina um player da rodada atual"""
        room = self.rooms.get(game_id)
        if not room:
            return
        
        # Encontra o player e marca como eliminado
        for player in room["players"]:
            if player.name == player_name:
                player.is_active = False
                break
        
        # Verifica quantos players ainda estão ativos
        active_players = [p for p in room["players"] if p.is_active]
        
        if len(active_players) <= 1:
            # Fim da rodada
            winner = active_players[0] if active_players else None
            await self.end_round(game_id, winner)
        
        # Notifica todos sobre a eliminação
        await self.broadcast_to_room(game_id, {
            "type": "player_eliminated",
            "player": player_name,
            "active_players": len(active_players),
            "eliminated_player": player_name
        })

    async def end_round(self, game_id: str, winner: Player = None):
        """Finaliza a rodada atual"""
        room = self.rooms.get(game_id)
        if not room:
            return
        
        # Atualiza pontuação do vencedor
        if winner:
            winner.score += 1
        
        # Prepara para próxima rodada
        for player in room["players"]:
            player.is_active = True  # Reativa todos os players
        
        room["round_number"] += 1
        room["game_state"] = "waiting"
        
        await self.broadcast_to_room(game_id, {
            "type": "round_ended",
            "winner": winner.name if winner else None,
            "round_number": room["round_number"],
            "scores": {player.name: player.score for player in room["players"]}
        })

    async def broadcast_to_room(self, game_id: str, message: dict):
        if game_id not in self.rooms:
            return
        await sio.emit("game_event", message, room=game_id)

    async def handle_word_submission(self, game_id: str, sid: str, word: str):
        room = self.rooms.get(game_id)
        if not room:
            return
        # Encontra o player atual
        current_player = None
        for player in room["players"]:
            if player.websocket == sid:
                current_player = player
                break
        if not current_player:
            return
        # Valida a palavra
        word = word.lower().strip()
        # Verifica se a palavra existe no dicionário
        if not verify_word(word, room["difficulty"]):
            await sio.emit("game_event", {
                "type": "word_invalid",
                "word": word,
                "reason": "Palavra não encontrada no dicionário!"
            }, to=sid)
            return
        # Verifica se começa com a letra correta
        expected_letter = self.get_expected_letter(room)
        if expected_letter and word[0] != expected_letter:
            await sio.emit("game_event", {
                "type": "word_invalid",
                "word": word,
                "reason": f"A palavra deve começar com '{expected_letter}'"
            }, to=sid)
            return
        # Palavra válida! Atualiza o jogo
        room["current_word"] = word
        # Calcula a próxima letra e índice baseado no modo
        next_letter_info = self.get_next_letter_info(room, word)
        # Notifica todos os jogadores
        await self.broadcast_to_room(game_id, {
            "type": "word_accepted",
            "player": current_player.name,
            "word": word,
            "current_word": word,
            "next_letter": next_letter_info["letter"],
            "next_letter_index": next_letter_info["index"]
        })

    def get_expected_letter(self, room: dict) -> str:
        """
        Retorna a letra que a próxima palavra deve começar.
        """
        if not room["current_word"]:
            return ""
        
        current_word = room["current_word"]
        difficulty = room["difficulty"]
        
        if difficulty.lower() == "caotic":
            # Modo caótico: usa a letra armazenada da jogada anterior
            return room.get("next_letter", current_word[-1])
        else:
            # Modos normal e easy: sempre a última letra da palavra atual
            return current_word[-1]
    
    def get_next_letter_info(self, room: dict, word: str) -> dict:
        """
        Calcula qual será a próxima letra e seu índice baseado no modo de jogo.
        Retorna dict com 'letter' e 'index'.
        
        - Normal/Easy: Sempre a última letra (índice = len(word) - 1)
        - Caótico: Letra aleatória de qualquer posição válida
        """
        difficulty = room["difficulty"]
        
        if difficulty.lower() == "caotic":
            # Modo caótico: sorteia uma posição aleatória da palavra
            word_lower = word.lower()
            valid_letters = "abcdefghijklmnopqrstuvwxyz"
            
            # Encontra posições com letras válidas (sem acentos)
            valid_positions = [
                i for i, char in enumerate(word_lower) 
                if char in valid_letters
            ]
            
            if not valid_positions:
                # Fallback se não houver letras válidas
                return {"letter": "a", "index": -1}
            
            # Sorteia uma posição válida aleatória
            chosen_index = random.choice(valid_positions)
            chosen_letter = word_lower[chosen_index]
            
            # Armazena para próxima validação
            room["next_letter"] = chosen_letter
            room["next_letter_index"] = chosen_index
            
            return {"letter": chosen_letter, "index": chosen_index}
        else:
            # Modos normal e easy: SEMPRE a última letra da palavra
            last_index = len(word) - 1
            last_letter = word[-1].lower()
            
            return {"letter": last_letter, "index": last_index}

    async def start_new_game(self, game_id: str):
        """Inicia uma nova partida com uma palavra aleatória"""
        room = self.rooms.get(game_id)
        if not room or len(room["players"]) < 2:
            return
        
        # Reativa todos os players
        for player in room["players"]:
            player.is_active = True
        
        # Sorteia uma nova palavra inicial baseada na dificuldade
        initial_word = get_random_word(room["difficulty"])
        room["current_word"] = initial_word
        room["game_state"] = "playing"
        
        # Calcula a primeira letra e índice para o próximo jogador
        next_letter_info = self.get_next_letter_info(room, initial_word)
        
        await self.broadcast_to_room(game_id, {
            "type": "game_started",
            "initial_word": initial_word,
            "current_word": initial_word,
            "next_letter": next_letter_info["letter"],
            "next_letter_index": next_letter_info["index"],
            "round_number": room["round_number"],
            "difficulty": room["difficulty"]
        })

    async def change_room_difficulty(self, game_id: str, difficulty: str):
        """Altera a dificuldade da sala"""
        if difficulty.lower() not in ["normal", "easy", "caotic"]:
            difficulty = "normal"
        
        room = self.rooms.get(game_id)
        if not room:
            return
        
        room["difficulty"] = difficulty.lower()
        
        await self.broadcast_to_room(game_id, {
            "type": "difficulty_changed",
            "difficulty": room["difficulty"],
            "message": f"Dificuldade alterada para: {room['difficulty']}"
        })


manager = GameManager()

# Eventos Socket.IO
@sio.event
async def join_game(sid, data):
    game_id = data.get("game_id")
    player_name = data.get("player_name", "Anonymous")
    await manager.connect(game_id, sid, player_name)

@sio.event
async def submit_word(sid, data):
    session = await sio.get_session(sid)
    game_id = session["game_id"]
    word = data.get("word", "")
    await manager.handle_word_submission(game_id, sid, word)

@sio.event
async def start_new_game(sid, data):
    session = await sio.get_session(sid)
    game_id = session["game_id"]
    await manager.start_new_game(game_id)

@sio.event
async def change_difficulty(sid, data):
    session = await sio.get_session(sid)
    game_id = session["game_id"]
    difficulty = data.get("difficulty", "normal")
    await manager.change_room_difficulty(game_id, difficulty)

@sio.event
async def leave_game(sid, data):
    session = await sio.get_session(sid)
    game_id = session["game_id"]
    await manager.disconnect(game_id, sid)
    await sio.leave_room(sid, game_id)

@sio.event
async def disconnect(sid):
    session = await sio.get_session(sid)
    if session:
        game_id = session.get("game_id")
        if game_id:
            await manager.disconnect(game_id, sid)

###
@sio.event
async def connect(sid, environ):
    print(f"Cliente {sid} conectado")
    await sio.emit('message', 'Bem-vindo ao servidor!', room=sid)

@sio.event
async def message(sid, data):
    print(f"Mensagem de {sid}: {data}")
    await sio.emit('message', f"Servidor recebeu: {data}", room=sid)


@fastapi_app.post("/game/{game_id}/start")
async def start_game_http(game_id: str):
    await manager.start_new_game(game_id)
    return {"message": "New game started"}

@fastapi_app.post("/game/{game_id}/timeout/{player_name}")
async def player_timeout(game_id: str, player_name: str):
    await manager.eliminate_player(game_id, player_name)
    return {"message": f"Player {player_name} eliminated due to timeout"}