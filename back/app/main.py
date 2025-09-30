# Word Tower API - Socket.IO Backend
import sys
import os
import uvicorn

# Adiciona o diretório pai ao path para encontrar o módulo 'app'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("UVICORN_RELOAD", "False").lower() in ("1", "true", "yes")

    uvicorn.run("app.ws.game_manager:app", host=host, port=port, reload=reload)