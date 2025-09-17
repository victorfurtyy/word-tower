# Word Tower API - Socket.IO Backend
import sys
import os
import uvicorn

# Adiciona o diretório pai ao path para encontrar o módulo 'app'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    uvicorn.run("app.ws.game_manager:app", host="0.0.0.0", port=8000, reload=True)