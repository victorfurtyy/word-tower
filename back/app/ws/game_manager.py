import json
import random

import socketio
from app.utils.dictionary import verify_word, get_random_word, get_random_letter_from_word
from app.classes.player import Player

sio = socketio.AsyncServer(
    async_mode='asgi', 
    cors_allowed_origins=['http://localhost:5173']
)
app = socketio.ASGIApp(sio)


class GameManager:
    """Manages game rooms and player interactions for the Word Tower multiplayer game."""
    
    def __init__(self):
        self.rooms: dict[str, dict] = {}

    async def connect(self, game_id: str, sid: str, player_name: str):
        """Connect a player to a game room."""
        if game_id not in self.rooms:
            self.rooms[game_id] = {
                "players": [],
                "current_word": "",
                "game_state": "waiting",
                "round_number": 1,
                "difficulty": "normal",
                "current_player_index": 0,
                "turn_order": [],
                "used_words": []
            }
        
        is_host = len(self.rooms[game_id]["players"]) == 0
        player = Player(player_name, sid, is_host)
        
        if self.rooms[game_id]["game_state"] == "playing":
            player.is_active = False
        
        self.rooms[game_id]["players"].append(player)
        await sio.save_session(sid, {
            "game_id": game_id, 
            "player_name": player_name,
            "player_id": player.id
        })
        await sio.enter_room(sid, game_id)
        
        if self.rooms[game_id]["game_state"] == "waiting":
            self.rooms[game_id]["turn_order"] = [p.id for p in self.rooms[game_id]["players"] if p.is_active]
        
        await self.broadcast_to_room(game_id, {
            "type": "player_joined",
            "player": player_name,
            "player_id": player.id,
            "players": self.get_players_info(game_id),
            "total_players": len(self.rooms[game_id]["players"]),
            "difficulty": self.rooms[game_id]["difficulty"],
            "game_state": self.rooms[game_id]["game_state"],
            "current_player": self.get_current_player_info(game_id),
            "is_active": player.is_active
        })

    async def disconnect(self, game_id: str, sid: str):
        """Disconnect a player from a game room."""
        if game_id not in self.rooms:
            return
        
        room = self.rooms[game_id]
        
        player_name = None
        was_host = False
        for i, player in enumerate(room["players"]):
            if player.websocket == sid:
                player_name = player.name
                was_host = player.is_host
                room["players"].pop(i)
                break
        
        if was_host and room["players"]:
            room["players"][0].is_host = True
        
        remaining_players = len(room["players"])
        
        if room["game_state"] == "playing" and remaining_players < 2:
            room["game_state"] = "waiting"
            room["current_word"] = ""
            room["turn_order"] = []
            room["current_player_index"] = 0
            room["used_words"] = []
            
            await self.broadcast_to_room(game_id, {
                "type": "game_ended",
                "reason": "Insufficient players (minimum 2 required)",
                "players": self.get_players_info(game_id)
            })
        
        if player_name:
            await self.broadcast_to_room(game_id, {
                "type": "player_left",
                "player": player_name,
                "players": self.get_players_info(game_id),
                "total_players": remaining_players,
                "current_player": self.get_current_player_info(game_id)
            })
        
        if not room["players"]:
            del self.rooms[game_id]

    async def eliminate_player(self, game_id: str, player_name: str):
        """Eliminate a player from the current round by name."""
        room = self.rooms.get(game_id)
        if not room:
            return
        
        eliminated_player = None
        for player in room["players"]:
            if player.name == player_name:
                player.is_active = False
                eliminated_player = player
                break
        
        if eliminated_player:
            await self._handle_player_elimination(game_id, eliminated_player)
    
    async def eliminate_player_by_id(self, game_id: str, player_id: str):
        """Eliminate a player from the current round by ID."""
        room = self.rooms.get(game_id)
        if not room:
            return
        
        eliminated_player = None
        for player in room["players"]:
            if player.id == player_id:
                player.is_active = False
                eliminated_player = player
                break
        
        if eliminated_player:
            await self._handle_player_elimination(game_id, eliminated_player)
    
    async def _handle_player_elimination(self, game_id: str, eliminated_player):
        """Handle the elimination logic after a player is marked as inactive."""
        room = self.rooms.get(game_id)
        if not room:
            return
        
        active_players = [p for p in room["players"] if p.is_active]
        
        if len(active_players) <= 1:
            winner = active_players[0] if active_players else None
            await self.end_round(game_id, winner)
        
        await self.broadcast_to_room(game_id, {
            "type": "player_eliminated",
            "player": eliminated_player.name,
            "player_id": eliminated_player.id,
            "players": [p.name for p in room["players"]],
            "active_players": len(active_players),
            "eliminated_player": eliminated_player.name
        })

    async def end_round(self, game_id: str, winner: Player = None):
        """End the current round."""
        room = self.rooms.get(game_id)
        if not room:
            return
        
        for player in room["players"]:
            player.is_active = True 
        
        room["round_number"] += 1
        room["game_state"] = "waiting"
        
        await self.broadcast_to_room(game_id, {
            "type": "round_ended",
            "winner": winner.name if winner else None,
            "round_number": room["round_number"],
            "players": self.get_players_info(game_id)
        })

    async def broadcast_to_room(self, game_id: str, message: dict):
        """Broadcast a message to all players in a room."""
        if game_id not in self.rooms:
            return
        await sio.emit("game_event", message, room=game_id)

    def get_players_info(self, game_id: str) -> list:
        """Get detailed information about all players in a room."""
        room = self.rooms.get(game_id)
        if not room:
            return []
        
        return [{
            "id": player.id,
            "name": player.name,
            "is_active": player.is_active,
            "is_host": player.is_host
        } for player in room["players"]]

    def get_current_player_info(self, game_id: str) -> dict:
        """Get information about the current player's turn."""
        room = self.rooms.get(game_id)
        if not room or room["game_state"] != "playing":
            return None
        
        if not room.get("turn_order"):
            return None
            
        current_index = room.get("current_player_index", 0)
        if current_index >= len(room["turn_order"]):
            return None
            
        current_player_id = room["turn_order"][current_index]
        
        for player in room["players"]:
            if player.id == current_player_id and player.is_active:
                return {
                    "id": player.id,
                    "name": player.name
                }
        return None

    def is_player_host(self, game_id: str, sid: str) -> bool:
        """Check if a player is the host of the room."""
        room = self.rooms.get(game_id)
        if not room:
            return False
        
        for player in room["players"]:
            if player.websocket == sid:
                return player.is_host
        return False

    def get_player_by_sid(self, game_id: str, sid: str) -> Player:
        """Find a player by their socket ID."""
        room = self.rooms.get(game_id)
        if not room:
            return None
        
        for player in room["players"]:
            if player.websocket == sid:
                return player
        return None

    def advance_turn(self, game_id: str):
        """Advance to the next player's turn."""
        room = self.rooms.get(game_id)
        if not room or not room.get("turn_order"):
            return
        
        active_players = [p for p in room["players"] if p.is_active]
        room["turn_order"] = [p.id for p in active_players]
        
        if len(room["turn_order"]) <= 1:
            return
        
        current_index = room.get("current_player_index", 0)
        current_index = (current_index + 1) % len(room["turn_order"])
        room["current_player_index"] = current_index

    async def handle_word_submission(self, game_id: str, sid: str, word: str):
        room = self.rooms.get(game_id)
        if not room:
            return
            
        current_player = self.get_player_by_sid(game_id, sid)
        if not current_player:
            return
            
        current_player_info = self.get_current_player_info(game_id)
        if not current_player_info or current_player_info["id"] != current_player.id:
            await sio.emit("game_event", {
                "type": "word_invalid",
                "word": word,
                "reason": "Não é sua vez de jogar!"
            }, to=sid)
            return
            
        if not current_player.is_active:
            await sio.emit("game_event", {
                "type": "word_invalid", 
                "word": word,
                "reason": "Você foi eliminado desta rodada!"
            }, to=sid)
            return
            
        word = word.lower().strip()
        
        if not verify_word(word, room["difficulty"]):
            await self.eliminate_player(game_id, current_player.name)
            await sio.emit("game_event", {
                "type": "word_invalid",
                "word": word,
                "reason": "Palavra não encontrada no dicionário! Você foi eliminado."
            }, to=sid)
            return
            
        expected_letter = self.get_expected_letter(room)
        if expected_letter and word[0] != expected_letter:
            await self.eliminate_player(game_id, current_player.name)
            await sio.emit("game_event", {
                "type": "word_invalid",
                "word": word,
                "reason": f"A palavra deve começar com '{expected_letter}'! Você foi eliminado."
            }, to=sid)
            return
            
        room["current_word"] = word
        
        next_letter_info = self.get_next_letter_info(room, word)
        
        self.advance_turn(game_id)
        
        await self.broadcast_to_room(game_id, {
            "type": "word_accepted",
            "player": current_player.name,
            "player_id": current_player.id,
            "word": word,
            "current_word": word,
            "next_letter": next_letter_info["letter"],
            "next_letter_index": next_letter_info["index"],
            "current_player": self.get_current_player_info(game_id),
            "players": self.get_players_info(game_id)
        })

    def get_expected_letter(self, room: dict) -> str:
        """Get the expected starting letter for the next word."""
        if not room["current_word"]:
            return ""
        
        current_word = room["current_word"]
        difficulty = room["difficulty"]
        
        if difficulty.lower() == "caotic":
            return room.get("next_letter", current_word[-1])
        else:
            return current_word[-1]
    
    def get_next_letter_info(self, room: dict, word: str) -> dict:
        """Get information about the next letter based on game difficulty."""
        difficulty = room["difficulty"]
        
        if difficulty.lower() == "caotic":
            word_lower = word.lower()
            valid_letters = "abcdefghijklmnopqrstuvwxyz"
            
            valid_positions = [
                i for i, char in enumerate(word_lower) 
                if char in valid_letters
            ]
            
            if not valid_positions:
                return {"letter": "a", "index": -1}
            
            chosen_index = random.choice(valid_positions)
            chosen_letter = word_lower[chosen_index]
            
            room["next_letter"] = chosen_letter
            room["next_letter_index"] = chosen_index
            
            return {"letter": chosen_letter, "index": chosen_index}
        else:
            last_index = len(word) - 1
            last_letter = word[-1].lower()
            
            return {"letter": last_letter, "index": last_index}

    async def start_new_game(self, game_id: str, requesting_player_sid: str = None):
        """Start a new game with a random word."""
        room = self.rooms.get(game_id)
        if not room or len(room["players"]) < 2:
            return False, "Minimum 2 players required"
        
        if requesting_player_sid and not self.is_player_host(game_id, requesting_player_sid):
            return False, "Only the room creator can start the game"
        
        if room["game_state"] == "playing":
            return False, "Game already in progress"
        
        for player in room["players"]:
            player.is_active = True
        
        import random
        active_players = [p for p in room["players"] if p.is_active]
        random.shuffle(active_players)
        room["turn_order"] = [p.id for p in active_players]
        room["current_player_index"] = 0
        
        initial_word = get_random_word(room["difficulty"])
        room["current_word"] = initial_word
        room["game_state"] = "playing"
        
        room["used_words"] = [initial_word.lower()]
        
        next_letter_info = self.get_next_letter_info(room, initial_word)
        
        await self.broadcast_to_room(game_id, {
            "type": "game_started",
            "initial_word": initial_word,
            "current_word": initial_word,
            "next_letter": next_letter_info["letter"],
            "next_letter_index": next_letter_info["index"],
            "round_number": room["round_number"],
            "difficulty": room["difficulty"],
            "current_player": self.get_current_player_info(game_id),
            "players": self.get_players_info(game_id),
            "turn_order": [{"id": p_id, "name": next((p.name for p in room["players"] if p.id == p_id), "Unknown")} for p_id in room["turn_order"]]
        })
        return True, "Game started successfully"

    async def handle_word_submission(self, game_id: str, sid: str, word: str):
        """Process a word submission from a player."""
        room = self.rooms.get(game_id)
        if not room:
            await sio.emit("game_event", {
                "type": "error",
                "message": "Room not found"
            }, to=sid)
            return
        
        if room["game_state"] != "playing":
            await sio.emit("game_event", {
                "type": "error", 
                "message": "Game is not in progress"
            }, to=sid)
            return
        
        player = self.get_player_by_sid(game_id, sid)
        if not player:
            await sio.emit("game_event", {
                "type": "error",
                "message": "Player not found"
            }, to=sid)
            return
        
        current_player_info = self.get_current_player_info(game_id)
        if not current_player_info or current_player_info["id"] != player.id:
            await sio.emit("game_event", {
                "type": "error",
                "message": "Not your turn to play"
            }, to=sid)
            return
        
        if not verify_word(word.lower(), room["difficulty"]):
            await sio.emit("game_event", {
                "type": "word_rejected",
                "reason": "Word not found in dictionary",
                "word": word
            }, to=sid)
            return
        
        if word.lower() in room["used_words"]:
            await sio.emit("game_event", {
                "type": "word_rejected",
                "reason": "Word already used in this game",
                "word": word
            }, to=sid)
            return
        
        next_letter_info = self.get_next_letter_info(room, room["current_word"])
        expected_letter = next_letter_info["letter"].lower()
        
        if word.lower()[0] != expected_letter:
            await sio.emit("game_event", {
                "type": "word_rejected", 
                "reason": f"Word must start with '{expected_letter.upper()}'",
                "word": word
            }, to=sid)
            return
        
        room["current_word"] = word.lower()
        room["used_words"].append(word.lower())
        
        self.advance_turn(game_id)
        
        next_letter_info = self.get_next_letter_info(room, word.lower())
        await self.broadcast_to_room(game_id, {
            "type": "word_submitted",
            "player": player.name,
            "word": word.lower(),
            "current_word": word.lower(),
            "next_letter": next_letter_info["letter"],
            "next_letter_index": next_letter_info["index"],
            "current_player": self.get_current_player_info(game_id),
            "players": self.get_players_info(game_id)
        })

    async def change_room_difficulty(self, game_id: str, difficulty: str, requesting_player_sid: str):
        """Change room difficulty - only when game is not in progress."""
        if difficulty.lower() not in ["normal", "easy", "caotic"]:
            difficulty = "normal"
        
        room = self.rooms.get(game_id)
        if not room:
            return False, "Room not found"
        
        if room["game_state"] == "playing":
            await sio.emit("game_event", {
                "type": "difficulty_change_denied",
                "reason": "Cannot change difficulty during game"
            }, to=requesting_player_sid)
            return False, "Game in progress"
        
        if not self.is_player_host(game_id, requesting_player_sid):
            await sio.emit("game_event", {
                "type": "difficulty_change_denied", 
                "reason": "Only the room creator can change difficulty"
            }, to=requesting_player_sid)
            return False, "Only host can change"
        
        player_in_room = any(player.websocket == requesting_player_sid for player in room["players"])
        if not player_in_room:
            await sio.emit("game_event", {
                "type": "difficulty_change_denied", 
                "reason": "You are not in this room"
            }, to=requesting_player_sid)
            return False, "Player not in room"
        
        room["difficulty"] = difficulty.lower()
        
        await self.broadcast_to_room(game_id, {
            "type": "difficulty_changed",
            "difficulty": room["difficulty"],
            "message": f"Difficulty changed to: {room['difficulty']}"
        })
        return True, "Difficulty changed successfully"


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
    success, message = await manager.start_new_game(game_id, sid)
    
    if not success:
        await sio.emit("game_event", {
            "type": "start_game_denied",
            "reason": message
        }, to=sid)

@sio.event
async def change_difficulty(sid, data):
    session = await sio.get_session(sid)
    game_id = session["game_id"]
    difficulty = data.get("difficulty", "normal")
    success, message = await manager.change_room_difficulty(game_id, difficulty, sid)
    
    if not success:
        await sio.emit("game_event", {
            "type": "error",
            "message": message
        }, to=sid)

@sio.event
async def leave_game(sid, data):
    """Explicitly remove a player from the room."""
    session = await sio.get_session(sid)
    if session and session.get("game_id"):
        await manager.disconnect(session["game_id"], sid)
        await sio.leave_room(sid, session["game_id"])
        await sio.clear_session(sid)
        await sio.emit("game_event", {"type": "left_game"}, to=sid)

@sio.event
async def disconnect(sid):
    """Automatic disconnection - clean session data."""
    session = await sio.get_session(sid)
    if session and session.get("game_id"):
        await manager.disconnect(session["game_id"], sid)
    await sio.clear_session(sid)
    print(f"Client {sid} disconnected and session cleared")

@sio.event
async def connect(sid, environ):
    print(f"Client {sid} connected")
    await sio.emit('message', 'Welcome to the server!', room=sid)
@sio.event
async def player_timeout(sid, data):
    """Eliminate player by timeout via WebSocket."""
    session = await sio.get_session(sid)
    if session and session.get("game_id"):
        player_id = data.get("player_id")
        if player_id:
            await manager.eliminate_player_by_id(session["game_id"], player_id)
            await sio.emit("game_event", {
                "type": "timeout_handled", 
                "player_id": player_id
            }, to=sid)
        else:
            await sio.emit("game_event", {
                "type": "error",
                "message": "Player ID is required for timeout"
            }, to=sid)