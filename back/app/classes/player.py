import uuid

class Player:
    def __init__(self, name: str, websocket: str, is_host: bool = False):
        self.id = str(uuid.uuid4())  # ID único para cada player
        self.name = name
        self.websocket = websocket  # Armazena o SID do Socket.IO
        self.is_active = True  # Se o player está ativo na rodada atual
        self.is_host = is_host  # Se o player é o criador/host da sala
    
    def __str__(self):
        return f"Player({self.name}, id: {self.id[:8]}, active: {self.is_active}, host: {self.is_host})"
    
    def __repr__(self):
        return self.__str__()