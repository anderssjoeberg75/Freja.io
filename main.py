import socketio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings, get_allowed_origins
from app.core.logging import logger
from app.services.proactive_service import init_proactive_service
from contextlib import asynccontextmanager

# Section: Tool bootstrap imports
# Importing this module at app startup ensures all auto-discovered skill tools,
# including integrations, are registered in the shared ToolRegistry before first chat.
from app.core.legacy_registration import register_all_tools

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Mainframe Services...")

    # Explicitly register tools
    register_all_tools()

    from app.core.database import init_db, get_db_settings_sync
    init_db()

    # --- Kontrollera om känsliga nycklar finns kvar i databasen ---
    try:
        from app.core.settings_schema import SETTINGS_SCHEMA
        secret_keys = {item.key for item in SETTINGS_SCHEMA if item.type == "password"}
        db_settings = get_db_settings_sync()
        secrets_in_db = [k for k in secret_keys if db_settings.get(k)]
        if secrets_in_db:
            logger.warning(f"⚠️ Känsliga nycklar finns kvar i databasen: {secrets_in_db}. Kör scripts/cleanup_db_secrets.py för att rensa!")
    except Exception as e:
        logger.error(f"Fel vid kontroll av känsliga nycklar i DB: {e}")

    proactive = init_proactive_service(sio)
    await proactive.start()

    # Start Document Watcher for RAG
    from app.services.document_watcher import document_watcher
    document_watcher.start()

    # Initialize Telegram with LLM callback
    from app.services.telegram_service import init_telegram_service

    async def telegram_llm_callback(message: str, chat_id: str) -> str:
        """Process Telegram message through Unified Chat Service."""
        try:
            from app.services.chat_service import shared_chat_service

            response = await shared_chat_service.process_message(
                session_id=chat_id,
                user_msg=message
            )
            return response

        except Exception as e:
            logger.error(f"Telegram LLM error for chat_id={chat_id}: {e}", exc_info=True)
            return f"Fel vid AI-svar: {str(e)}"

    telegram = init_telegram_service(telegram_llm_callback)
    await telegram.start()

    yield

    # Shutdown
    logger.info("Shutting down Mainframe Services...")
    document_watcher.stop()
    await telegram.stop()
    await proactive.stop()

# Initialize FastAPI
app = FastAPI(lifespan=lifespan)

# --- Centralized Exception Handler ---
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"[EXCEPTION] {request.method} {request.url}: {exc}", exc_info=True)
    detail = str(exc) if settings.DEBUG else "An internal error occurred."
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": detail}
    )

# Optional: Handle validation errors more gracefully
@app.exception_handler(FastAPIRequestValidationError)
async def validation_exception_handler(request: Request, exc: FastAPIRequestValidationError):
    logger.warning(f"[VALIDATION] {request.method} {request.url}: {exc}")
    detail = exc.errors() if settings.DEBUG else "Validation error."
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "detail": detail}
    )

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IP Access Control Middleware
@app.middleware("http")
async def ip_middleware(request: Request, call_next):
    from app.core.security import check_ip_allowlist
    try:
        check_ip_allowlist(request)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})
    except Exception as e:
        logger.error(f"IP Middleware error: {e}")
        # In case of unexpected error, we default to allow to prevent lockout
        # but log the incident.
    
    response = await call_next(request)
    return response

# Socket.IO Setup
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=get_allowed_origins())
app_socketio = socketio.ASGIApp(sio, app)

# Legacy socket session store (kept for safe disconnect cleanup).
chat_sessions = {}

# Routes
@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}

# Include API Routers
from app.routers import chat, settings as settings_router, system, live, strava, withings, document_analysis

app.include_router(chat.router)
app.include_router(settings_router.router)
app.include_router(system.router)
app.include_router(live.router)
app.include_router(strava.router)
app.include_router(withings.router)
app.include_router(document_analysis.router)

from app.routers import integrations
app.include_router(integrations.router)

# --- SERVE REACT FRONTEND (Production) ---
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Mount static assets (JS/CSS/Images built by Vite)
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

# Voice handlers removed


@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")
    # Clean up chat session if exists
    if sid in chat_sessions:
        await chat_sessions[sid].stop()
        del chat_sessions[sid]

# --- CHAT EVENTS ---
# --- CHAT EVENTS ---
# socket.io chat events removed in cleanup (using REST API or live.py instead)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app_socketio", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
