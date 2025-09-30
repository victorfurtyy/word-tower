import json
import random
import asyncio
import time
import os
from typing import Optional

import socketio
from app.utils.dictionary import verify_word, get_random_word, get_random_letter_from_word
from app.classes.player import Player

TURN_TIME_LIMIT = 30
PENALTY_TIME = 5
MIN_TIME_REMAINING = 3

sockets_cors_env = os.getenv("SOCKET_CORS_ORIGINS", "http://localhost:5173")
if sockets_cors_env.strip() == "*":
    cors_allowed = "*"
else:
    cors_allowed = [o.strip() for o in sockets_cors_env.split(",") if o.strip()]

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=cors_allowed
)
app = socketio.ASGIApp(sio)


class GameManager:
    """Manages game rooms and player interactions for the Word Tower multiplayer game."""
    
    def __init__(self):
        self.rooms: dict[str, dict] = {}
        self.timer_tasks: dict[str, asyncio.Task] = {}

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
                "used_words": [],
                "turn_start_time": None,
                "remaining_time": TURN_TIME_LIMIT,
                "settings": {
                    "default_time": TURN_TIME_LIMIT,
                    "difficulty": "normal"
                }
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
        
        room_settings = self.rooms[game_id]["settings"]
        print(f"⚙️ Enviando configurações da sala {game_id}: {room_settings}")
        
        await self.broadcast_to_room(game_id, {
            "type": "player_joined",
            "player": player_name,
            "player_id": player.id,
            "players": self.get_players_info(game_id),
            "total_players": len(self.rooms[game_id]["players"]),
            "difficulty": self.rooms[game_id]["difficulty"],
            "game_state": self.rooms[game_id]["game_state"],
            "current_player": self.get_current_player_info(game_id),
            "is_active": player.is_active,
            "room_settings": room_settings  # Enviar configurações da sala
        })

    async def disconnect(self, game_id: str, sid: str):
        """Disconnect a player from a game room."""
        if game_id not in self.rooms:
            return
        
        room = self.rooms[game_id]
        
        disconnected_player = None
        player_name = None
        was_host = False
        was_current_player = False
        
        current_player_info = self.get_current_player_info(game_id) if room["game_state"] == "playing" else None
        
        for i, player in enumerate(room["players"]):
            if player.websocket == sid:
                disconnected_player = player
                player_name = player.name
                was_host = player.is_host
                was_current_player = (current_player_info and player.id == current_player_info["id"])
                room["players"].pop(i)
                break
        
        if not disconnected_player:
            return
        
        if was_host and room["players"]:
            room["players"][0].is_host = True
        
        remaining_players = len(room["players"])
        
        if room["game_state"] == "playing":
            await self._stop_turn_timer(game_id)
            
            active_players = [p for p in room["players"] if p.is_active]
            
            if len(active_players) <= 1:
                winner = active_players[0] if active_players else None
                print(f"🏆 Victory condition met after disconnect - Winner: {winner.name if winner else 'None'}")
                await self._declare_victory(game_id, winner)
            elif remaining_players < 2:
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
            else:
                if was_current_player:
                    print(f"🔄 Current player disconnected, advancing turn")
                    self.advance_turn(game_id)
                    next_player = self.get_current_player_info(game_id)
                    if next_player:
                        print(f"⏰ Starting timer for next player: {next_player['name']}")
                        await self._start_turn_timer(game_id)
                    else:
                        print("❌ No next player found after advancing turn")
                else:
                    print(f"🔄 Non-current player disconnected, updating turn order")
                    room["turn_order"] = [p.id for p in active_players]
                    if room.get("current_player_index", 0) >= len(room["turn_order"]):
                        room["current_player_index"] = 0
                        print(f"🔧 Reset player index to 0 due to out of bounds")
                
                await self.broadcast_to_room(game_id, {
                    "type": "player_left",
                    "player": player_name,
                    "players": self.get_players_info(game_id),
                    "total_players": remaining_players,
                    "current_player": self.get_current_player_info(game_id),
                    "was_current_player": was_current_player
                })
        else:
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
        
        current_player = self.get_current_player_info(game_id)
        if current_player and current_player["id"] == eliminated_player.id:
            await self._stop_turn_timer(game_id)
        
        active_players = [p for p in room["players"] if p.is_active]
        
        if len(active_players) <= 1:
            winner = active_players[0] if active_players else None
            await self._declare_victory(game_id, winner)
            return
        
        # If eliminated player was current player, advance turn
        if current_player and current_player["id"] == eliminated_player.id:
            self.advance_turn(game_id)
            
            # Ensure we have a valid next player after advancing
            next_player = self.get_current_player_info(game_id)
            if not next_player and active_players:
                # Fallback: reset to first active player if current player is null
                room["current_player_index"] = 0
                room["turn_order"] = [p.id for p in active_players]
                next_player = self.get_current_player_info(game_id)
            
            if next_player:
                await self._start_turn_timer(game_id)
        
        # Get final state for broadcast - ensure current_player is never None
        final_players_info = self.get_players_info(game_id)
        final_current_player = self.get_current_player_info(game_id)
        
        # Guarantee current_player is never null for active game
        if not final_current_player and active_players and room["game_state"] == "playing":
            # Emergency fallback: set first active player as current
            room["current_player_index"] = 0
            room["turn_order"] = [p.id for p in active_players]
            final_current_player = self.get_current_player_info(game_id)
        
        final_active_count = len(active_players)
        
        await self.broadcast_to_room(game_id, {
            "type": "player_eliminated",
            "player": eliminated_player.name,
            "player_id": eliminated_player.id,
            "players": final_players_info,
            "active_players": final_active_count,
            "eliminated_player": eliminated_player.name,
            "current_player": final_current_player
        })

    async def _start_turn_timer(self, game_id: str):
        """Start the timer for the current player's turn."""
        room = self.rooms.get(game_id)
        if not room or room["game_state"] != "playing":
            return
            
        await self._stop_turn_timer(game_id)
        
        room["turn_start_time"] = time.time()
        # Usar o tempo configurado da sala
        turn_time = room["settings"].get("default_time", TURN_TIME_LIMIT)
        room["remaining_time"] = turn_time
        
        print(f"🕐 Timer iniciado: {turn_time}s para sala {game_id}")
        
        async def countdown():
            try:
                while room.get("remaining_time", 0) > 0 and game_id in self.timer_tasks:
                    await asyncio.sleep(1)
                    
                    if (game_id not in self.rooms or 
                        self.rooms[game_id]["game_state"] != "playing" or
                        game_id not in self.timer_tasks):
                        break
                        
                    room["remaining_time"] -= 1
                    
                    await self.broadcast_to_room(game_id, {
                        "type": "timer_update",
                        "remaining_time": room["remaining_time"],
                        "current_player": self.get_current_player_info(game_id)
                    })
                    
                    if room["remaining_time"] <= 0:
                        if game_id in self.timer_tasks:
                            await self._handle_time_up(game_id)
                        break
            except asyncio.CancelledError:
                pass
        
        timer_task = asyncio.create_task(countdown())
        self.timer_tasks[game_id] = timer_task
        
        await self.broadcast_to_room(game_id, {
            "type": "timer_started",
            "remaining_time": room["remaining_time"],
            "current_player": self.get_current_player_info(game_id)
        })
    
    async def _stop_turn_timer(self, game_id: str):
        """Stop the current timer for a game."""
        if game_id in self.timer_tasks:
            timer_task = self.timer_tasks[game_id]
            timer_task.cancel()
            del self.timer_tasks[game_id]
            
            try:
                await timer_task
            except asyncio.CancelledError:
                pass
        
        room = self.rooms.get(game_id)
        if room:
            room["remaining_time"] = 0
    
    async def _apply_time_penalty(self, game_id: str):
        """Apply time penalty for wrong answer."""
        room = self.rooms.get(game_id)
        if not room:
            return
            
        room["remaining_time"] = max(
            MIN_TIME_REMAINING, 
            room.get("remaining_time", 0) - PENALTY_TIME
        )
        
        await self.broadcast_to_room(game_id, {
            "type": "time_penalty",
            "remaining_time": room["remaining_time"],
            "penalty": PENALTY_TIME,
            "current_player": self.get_current_player_info(game_id)
        })
    
    async def _handle_time_up(self, game_id: str):
        """Handle when a player's time runs out - eliminate player and advance turn."""
        current_player_info = self.get_current_player_info(game_id)
        if not current_player_info:
            return
            
        room = self.rooms.get(game_id)
        if not room:
            return
        
        await self._stop_turn_timer(game_id)
        
        current_player = None
        for player in room["players"]:
            if player.id == current_player_info["id"]:
                current_player = player
                break
        
        if current_player:
            current_player.is_active = False
            
            await self.broadcast_to_room(game_id, {
                "type": "time_up",
                "eliminated_player": current_player_info["name"],
                "player_id": current_player_info["id"],
                "reason": "Tempo esgotado"
            })
            
            await self._handle_player_elimination(game_id, current_player)
    
    async def _declare_victory(self, game_id: str, winner):
        """Declare victory and prepare for game reset."""
        room = self.rooms.get(game_id)
        if not room:
            return
            
        await self._stop_turn_timer(game_id)
        
        room["game_state"] = "victory"
        room["winner"] = winner.name if winner else "Nenhum vencedor"
        
        await self.broadcast_to_room(game_id, {
            "type": "victory",
            "winner": winner.name if winner else "Nenhum vencedor",
            "winner_id": winner.id if winner else None,
            "players": self.get_players_info(game_id)
        })
        
        async def auto_reset():
            await asyncio.sleep(5)
            if game_id in self.rooms and self.rooms[game_id]["game_state"] == "victory":
                await self.reset_game(game_id)
                
        asyncio.create_task(auto_reset())

    async def reset_game(self, game_id: str):
        """Reset the game to waiting state after victory."""
        room = self.rooms.get(game_id)
        if not room:
            return
            
        await self._stop_turn_timer(game_id)
        
        room["game_state"] = "waiting"
        room["current_word"] = ""
        room["used_words"] = []
        room["turn_order"] = []
        room["current_player_index"] = 0
        room["round_number"] = 1
        room["winner"] = None
        # Usar configurações da sala para o tempo
        room["remaining_time"] = room["settings"].get("default_time", TURN_TIME_LIMIT)
        
        for player in room["players"]:
            player.is_active = True
        
        await self.broadcast_to_room(game_id, {
            "type": "game_reset",
            "game_state": "waiting",
            "players": self.get_players_info(game_id),
            "message": "Game has been reset. Host can start a new game."
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
            print(f"❌ No room or game not playing for {game_id}")
            return None
        
        turn_order = room.get("turn_order", [])
        if not turn_order:
            print(f"❌ No turn order for {game_id}")
            return None
            
        current_index = room.get("current_player_index", 0)
        if current_index >= len(turn_order):
            print(f"❌ Index {current_index} out of bounds for turn_order length {len(turn_order)}")
            return None
            
        current_player_id = turn_order[current_index]
        print(f"🔍 Looking for player {current_player_id} at index {current_index}")
        
        for player in room["players"]:
            if player.id == current_player_id and player.is_active:
                print(f"✅ Found current player: {player.name}")
                return {
                    "id": player.id,
                    "name": player.name
                }
        
        print(f"❌ Player {current_player_id} not found or inactive")
        print(f"   Active players: {[p.name for p in room['players'] if p.is_active]}")
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
        if not room:
            return
        
        active_players = [p for p in room["players"] if p.is_active]
        
        if len(active_players) <= 1:
            room["turn_order"] = [p.id for p in active_players] if active_players else []
            room["current_player_index"] = 0
            print(f"⚠️ Not enough active players for turn advancement: {len(active_players)}")
            return
        
        old_turn_order = room.get("turn_order", [])
        old_index = room.get("current_player_index", 0)
        
        print(f"🔄 Advance turn - Active players: {[p.name for p in active_players]}")
        print(f"   Old turn order: {old_turn_order}, old index: {old_index}")
        
        room["turn_order"] = [p.id for p in active_players]
        
        if old_turn_order and old_index < len(old_turn_order):
            current_player_id = old_turn_order[old_index]
            print(f"   Looking for old current player: {current_player_id}")
            
            try:
                new_index = room["turn_order"].index(current_player_id)
                room["current_player_index"] = (new_index + 1) % len(room["turn_order"])
                print(f"   Found at {new_index}, advancing to {room['current_player_index']}")
            except ValueError:
                room["current_player_index"] = 0
                print(f"   Old player not found, resetting to 0")
        else:
            room["current_player_index"] = 0
            print(f"   No valid old state, starting at 0")
        
        print(f"   New turn order: {room['turn_order']}, new index: {room['current_player_index']}")

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
        
        # Reiniciar o timer para o próximo jogador com as configurações corretas
        await self._start_turn_timer(game_id)
        
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
            # In chaotic mode, use the stored next_letter if it exists
            # This ensures the letter stays the same until someone gets it right
            return room.get("next_letter", current_word[-1])
        else:
            return current_word[-1]
    
    def get_next_letter_info(self, room: dict, word: str) -> dict:
        """Get information about the next letter based on game difficulty."""
        difficulty = room["difficulty"]
        
        if difficulty.lower() == "caotic":
            # In chaotic mode, randomly select a letter from the accepted word
            # This only happens when a word is successfully accepted
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
            
            # Store the new letter for future attempts
            room["next_letter"] = chosen_letter
            room["next_letter_index"] = chosen_index
            
            return {"letter": chosen_letter, "index": chosen_index}
        else:
            # Normal and easy modes: always use the last letter
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
            "turn_order": [{"id": p_id, "name": next((p.name for p in room["players"] if p.id == p_id), "Unknown")} for p_id in room["turn_order"]],
            "room_settings": room["settings"]  # Enviar configurações da sala
        })
        
        await self._start_turn_timer(game_id)
        
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
        
        # Buscar o nome do jogador para incluir na mensagem
        player_name = "Alguém"
        for player in room["players"]:
            if player.websocket == sid:
                player_name = player.name
                break

        if not verify_word(word.lower(), room["difficulty"]):
            await self.broadcast_to_room(game_id, {
                "type": "word_rejected",
                "reason": "Word not found in dictionary",
                "word": word,
                "player": player_name
            })
            await self._apply_time_penalty(game_id)
            return
        
        if word.lower() in room["used_words"]:
            await self.broadcast_to_room(game_id, {
                "type": "word_rejected",
                "reason": "Word already used in this game",
                "word": word,
                "player": player_name
            })
            await self._apply_time_penalty(game_id)
            return
        expected_letter = self.get_expected_letter(room).lower()
        
        if word.lower()[0] != expected_letter:
            await self.broadcast_to_room(game_id, {
                "type": "word_rejected", 
                "reason": f"Word must start with '{expected_letter.upper()}'",
                "word": word,
                "player": player_name
            })
            await self._apply_time_penalty(game_id)
            return
        
        room["current_word"] = word.lower()
        room["used_words"].append(word.lower())
        next_letter_info = self.get_next_letter_info(room, word.lower())
        
        await self._stop_turn_timer(game_id)
        self.advance_turn(game_id)
        
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
        
        await self._start_turn_timer(game_id)

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

    async def update_room_settings(self, game_id: str, settings: dict, requesting_player_sid: str):
        """Update room settings (time and difficulty) - can be changed at any time by host."""
        room = self.rooms.get(game_id)
        if not room:
            return False, "Room not found"

        if not self.is_player_host(game_id, requesting_player_sid):
            await sio.emit("game_event", {
                "type": "settings_update_denied", 
                "reason": "Only the room creator can change settings"
            }, to=requesting_player_sid)
            return False, "Only host can change"

        player_in_room = any(player.websocket == requesting_player_sid for player in room["players"])
        if not player_in_room:
            await sio.emit("game_event", {
                "type": "settings_update_denied", 
                "reason": "You are not in this room"
            }, to=requesting_player_sid)
            return False, "Player not in room"

        # Atualizar configurações
        if "default_time" in settings:
            new_time = settings["default_time"]
            old_time = room["settings"].get("default_time", "unknown")
            room["settings"]["default_time"] = new_time
            room["remaining_time"] = new_time
            
            # Se há um timer ativo, atualizá-lo também
            if room["game_state"] == "playing" and self.timer_tasks.get(game_id):
                room["remaining_time"] = new_time
                print(f"[DEBUG BACKEND] Active timer updated to: {new_time}")
                await self.broadcast_to_room(game_id, {
                    "type": "timer_update",
                    "remaining_time": room["remaining_time"],
                    "current_player": self.get_current_player_info(game_id)
                })

        if "difficulty" in settings:
            difficulty = settings["difficulty"].lower()
            # Mapear dificuldades do frontend para backend
            difficulty_map = {
                "fácil": "easy",
                "normal": "normal", 
                "difícil": "caotic"
            }
            backend_difficulty = difficulty_map.get(difficulty, "normal")
            
            room["settings"]["difficulty"] = difficulty
            room["difficulty"] = backend_difficulty

        await self.broadcast_to_room(game_id, {
            "type": "room_settings_updated",
            "settings": room["settings"],
            "message": "Room settings updated successfully"
        })
        return True, "Settings updated successfully"


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
async def update_room_settings(sid, data):
    """Update room settings (time and difficulty)."""
    session = await sio.get_session(sid)
    game_id = session["game_id"]
    settings = data.get("settings", {})
    
    success, message = await manager.update_room_settings(game_id, settings, sid)
    
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