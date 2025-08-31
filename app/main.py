from fastapi import FastAPI
from app.ws.game_manager import app as websocket_app

app = FastAPI(title="Word Tower API")

# Inclui as rotas WebSocket
app.mount("/ws", websocket_app)

@app.get("/")
async def root():
    return {"message": "Word Tower API is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)