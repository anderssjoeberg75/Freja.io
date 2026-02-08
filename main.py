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
        "http://192.168.107.17:3000",
        "*"
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

# Include API Routers
from app.routers import chat, settings as settings_router, system

app.include_router(chat.router)
app.include_router(settings_router.router)
app.include_router(system.router)

# --- SERVE REACT FRONTEND (Production) ---
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Mount static assets (JS/CSS/Images build by Vite)
# Mount static assets (JS/CSS/Images build by Vite)
static_dir = os.path.join(os.path.dirname(__file__), "client", "dist")

if os.path.exists(static_dir):
    # Mount /assets to be served as static files
    if os.path.exists(os.path.join(static_dir, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")
    
    # Serve index.html for root
    @app.get("/")
    async def serve_root():
        return FileResponse(os.path.join(static_dir, "index.html"))

    # Serve index.html for any sub-path (SPA fallback)
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Allow API requests to pass through (already handled by routers above)
        if full_path.startswith("api") or full_path.startswith("health"):
            return {"error": "API route not found"}
            
        # Check if file exists in assets (e.g. favicon.ico not in assets folder)
        potential_file = os.path.join(static_dir, full_path)
        if os.path.exists(potential_file) and os.path.isfile(potential_file):
            return FileResponse(potential_file)
            
        # Return index.html for React Router to handle
        return FileResponse(os.path.join(static_dir, "index.html"))
else:
    logger.warning("Frontend build not found. Run 'npm run build' in client directory.")
    @app.get("/")
    async def serve_missing_build():
        return {"error": "Frontend build not found", "msg": "Please run 'npm run build' in client directory and restart backend."}

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
    # Clean up chat session if exists
    if sid in chat_sessions:
        await chat_sessions[sid].stop()
        del chat_sessions[sid]

# --- CHAT EVENTS ---
chat_sessions = {}

@sio.event
async def start_chat(sid, data):
    logger.info(f"Starting chat session for {sid}")
    from app.services.gemini_live_chat import LiveChatSession
    from app.core.config import settings

    async def on_text(text):
        await sio.emit("chat_text", {"text": text}, room=sid)

    async def on_audio(audio_b64):
        await sio.emit("chat_audio", {"audio": audio_b64}, room=sid)

    async def on_done():
        await sio.emit("chat_done", {}, room=sid)

    async def on_error(err):
        await sio.emit("error", {"msg": str(err)}, room=sid)

    msg = data.get("message")
    
    session = LiveChatSession(
        api_key=settings.GOOGLE_API_KEY,
        on_text_chunk=on_text,
        on_audio_chunk=on_audio,
        on_done=on_done,
        on_error=on_error
    )
    
    chat_sessions[sid] = session
    
    # Start the session in a background task
    import asyncio
    asyncio.create_task(session.start(initial_message=msg))

@sio.event
async def chat_message(sid, data):
    if sid in chat_sessions:
        msg = data.get("message")
        if msg:
            await chat_sessions[sid].send_message(msg)

@sio.event
async def stop_chat(sid):
    if sid in chat_sessions:
        await chat_sessions[sid].stop()
        del chat_sessions[sid]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app_socketio", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
