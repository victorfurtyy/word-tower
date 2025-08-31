from fastapi import WebSocket

class Player:
    def __init__(self, name: str, websocket: WebSocket):
        self.name = name
        self.websocket = websocket
        self.score = 0
        self.is_active = True  # Se o player está ativo na rodada atual
    
    def __str__(self):
        return f"Player({self.name}, score: {self.score}, active: {self.is_active})"
    
    def __repr__(self):
        return self.__str__()