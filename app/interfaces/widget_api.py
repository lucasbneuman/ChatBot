"""
API Backend para Widget Flotante de WordPress
Proporciona endpoints REST para comunicación con el widget JavaScript
"""

import os
import uuid
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from ..agents.unified_agent import UnifiedAgent
from ..database.prospect_db_fixed import ProspectDatabaseFixed

# Cargar variables de entorno
load_dotenv()

# Modelos Pydantic para requests
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_info: Optional[Dict[str, Any]] = None

class SessionInfo(BaseModel):
    session_id: str

# Inicializar FastAPI app
app = FastAPI(
    title="Lucas Benites - Widget API",
    description="API para widget flotante de chat inteligente",
    version="2.0.0"
)

# Configurar CORS para WordPress
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "https://lucasbenites.com",  # Tu dominio WordPress
        "https://www.lucasbenites.com",
        "http://localhost:8000",  # Para testing local
        "*"  # Temporal - cambiar en producción
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Inicializar agente y base de datos
agent = None
db = None
sessions = {}  # Almacén de sesiones en memoria (usar Redis en producción)

def initialize_agent():
    """Inicializa el agente único"""
    global agent, db
    
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY no encontrada")
    
    agent = UnifiedAgent(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        db_path="prospects_production.db"
    )
    
    db = ProspectDatabaseFixed("prospects_production.db")
    print("OK Widget API inicializada correctamente")

# Inicializar al arrancar
try:
    initialize_agent()
except Exception as e:
    print(f"ERROR inicializando: {e}")

# === ENDPOINTS ===

@app.get("/")
async def root():
    """Endpoint de health check"""
    return {
        "status": "online",
        "service": "Lucas Benites Widget API",
        "version": "2.0.0",
        "agent_active": agent is not None
    }

@app.post("/chat")
async def chat_endpoint(chat_data: ChatMessage, request: Request):
    """
    Endpoint principal para mensajes del widget
    """
    try:
        if not agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        # Generar session_id si no existe
        session_id = chat_data.session_id or str(uuid.uuid4())
        
        # Obtener prospect_id asociado a la sesión
        prospect_id = sessions.get(session_id, {}).get("prospect_id")
        
        # Procesar mensaje con el agente único
        result = agent.process_message(chat_data.message, prospect_id)
        
        # Actualizar session con prospect_id si es nuevo
        if not prospect_id and result.get("prospect_id"):
            prospect_id = result["prospect_id"]
            sessions[session_id] = {
                "prospect_id": prospect_id,
                "channel": "web_widget",
                "created_at": uuid.uuid4().hex,
                "user_info": chat_data.user_info or {}
            }
        
        # Preparar respuesta
        response_data = {
            "success": True,
            "response": result.get("response", "Lo siento, no pude procesar tu mensaje."),
            "session_id": session_id,
            "prospect_id": prospect_id,
            "metadata": {
                "intent": result.get("intent"),
                "meeting_link_sent": result.get("meeting_link_sent", False),
                "rag_used": result.get("rag_used", False)
            }
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        print(f"ERROR en chat endpoint: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Error interno del servidor",
                "response": "Disculpa, tuve un problema técnico. ¿Podrías repetir tu mensaje?"
            }
        )

@app.post("/session/info")
async def get_session_info(session_data: SessionInfo):
    """
    Obtiene información de la sesión actual
    """
    try:
        session_id = session_data.session_id
        session_info = sessions.get(session_id)
        
        if not session_info:
            return JSONResponse(content={
                "success": False,
                "message": "Sesión no encontrada"
            })
        
        prospect_id = session_info.get("prospect_id")
        if not prospect_id:
            return JSONResponse(content={
                "success": True,
                "session_active": True,
                "prospect_info": None
            })
        
        # Obtener resumen del prospecto
        summary = agent.get_prospect_summary(prospect_id)
        
        return JSONResponse(content={
            "success": True,
            "session_active": True,
            "session_info": session_info,
            "prospect_info": summary.get("prospect") if summary else None
        })
        
    except Exception as e:
        print(f"ERROR obteniendo info de sesión: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/widget/config")
async def get_widget_config():
    """
    Configuración del widget para WordPress
    """
    return JSONResponse(content={
        "success": True,
        "config": {
            "title": "¡Hola! Soy el asistente de Lucas",
            "subtitle": "¿En qué puedo ayudarte hoy?",
            "placeholder": "Escribe tu mensaje aquí...",
            "theme": {
                "primary_color": "#2563EB",
                "secondary_color": "#F3F4F6", 
                "text_color": "#1F2937",
                "border_radius": "12px"
            },
            "features": {
                "typing_indicator": True,
                "message_timestamps": False,
                "minimize_button": True,
                "close_button": True
            },
            "contact_info": {
                "name": "Lucas Benites",
                "title": "Especialista en IA para PyMEs",
                "avatar": "/static/lucas-avatar.png",
                "website": "https://lucasbenites.com",
                "calendar": "https://meet.brevo.com/lucas-benites"
            }
        }
    })

@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    """Handle preflight OPTIONS requests"""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

# === FUNCIONES DE UTILIDAD ===

def get_session_stats():
    """Estadísticas de sesiones activas"""
    return {
        "active_sessions": len(sessions),
        "sessions_with_prospects": len([s for s in sessions.values() if s.get("prospect_id")])
    }

# === SERVIDOR DE DESARROLLO ===

if __name__ == "__main__":
    print("Iniciando Widget API Server...")
    print(f"Agent status: {'Ready' if agent else 'Not initialized'}")
    
    uvicorn.run(
        "widget_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )