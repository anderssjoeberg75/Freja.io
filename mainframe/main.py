import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.services.voice_service import init_voice_service
from app.services.proactive_service import init_proactive_service
from app.services.tool_registry import registry
from contextlib import asynccontextmanager

# Import tools to register them
import app.tools.basic_tools

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Mainframe Services...")
    from app.core.database import init_db
    init_db()
    
    proactive = init_proactive_service(sio)
    voice = init_voice_service(sio)
    
    await proactive.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Mainframe Services...")
    await proactive.stop()

# Initialize FastAPI
app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://192.168.107.17:8000",
        "http://192.168.107.17:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO Setup
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app_socketio = socketio.ASGIApp(sio, app)

# Routes
@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}

# Socket.IO Events
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    await sio.emit("status", {"msg": "Mainframe Online"}, room=sid)

@sio.event
async def start_voice(sid, data):
    from app.services.voice_service import voice_service
    if voice_service:
        await voice_service.start_session(sid)

@sio.event
async def stop_voice(sid):
    from app.services.voice_service import voice_service
    if voice_service:
        await voice_service.stop_session(sid)

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app_socketio", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
