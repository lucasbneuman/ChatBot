# app.py - Archivo principal para Hugging Face Spaces
import os
import gradio as gr
import uuid
from dotenv import load_dotenv
from app.agents.unified_agent import UnifiedAgent
from app.database.prospect_db_fixed import ProspectDatabaseFixed

# Cargar variables de entorno
load_dotenv()

# Verificar que las variables de entorno estén configuradas
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY no encontrada. Configura las variables de entorno.")

if not os.getenv("BREVO_API_KEY"):
    print("ADVERTENCIA: BREVO_API_KEY no encontrada. La integración con Brevo no funcionará.")

# Inicializar agente único
print("Inicializando AGENTE UNICO INTELIGENTE...")
agent = UnifiedAgent(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    db_path="prospects_production.db"
)

print("Agente unico inicializado correctamente")
print(f"RAG system: {'ACTIVO' if agent.rag_system else 'INACTIVO'}")
print(f"Brevo integration: {'ACTIVO' if agent.brevo_sync else 'INACTIVO'}")

db = ProspectDatabaseFixed("prospects_production.db")

# Diccionario para mantener prospect_ids por sesión
session_prospects = {}

def get_session_id(request: gr.Request = None) -> str:
    """Genera o recupera un ID único por sesión"""
    if request and hasattr(request, 'session_hash'):
        return str(request.session_hash)
    else:
        return str(uuid.uuid4())

def chat_interface(message, history, request: gr.Request = None):
    """Interfaz de chat simplificada con agente único"""
    session_id = get_session_id(request)
    
    # Obtener prospect_id para esta sesión
    current_prospect_id = session_prospects.get(session_id)
    
    if not message.strip():
        return history
    
    try:
        # Procesar mensaje con el AGENTE ÚNICO
        result = agent.process_message(message, current_prospect_id)
        
        # Actualizar prospect_id para esta sesión si es nuevo
        if not current_prospect_id:
            current_prospect_id = result.get("prospect_id")
            session_prospects[session_id] = current_prospect_id
        
        # Obtener respuesta
        response = result.get("response", "Lo siento, no pude procesar tu mensaje.")
        
        # Actualizar historial en formato messages
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})
        
        return history
        
    except Exception as e:
        print(f"Error en chat_interface: {e}")
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": "Disculpa, tuve un problema técnico. ¿Podrías repetir tu mensaje?"})
        return history

def get_prospect_info(request: gr.Request = None):
    """Obtiene información del prospecto actual"""
    session_id = get_session_id(request)
    current_prospect_id = session_prospects.get(session_id)
    
    if not current_prospect_id:
        return "No hay conversacion activa para esta sesion"
    
    try:
        summary = agent.get_prospect_summary(current_prospect_id)
        
        if not summary or "error" in summary:
            error_msg = summary.get("error", "Unknown error") if summary else "No summary returned"
            return f"Error: {error_msg}"
        
        prospect = summary["prospect"]
        
        # Función helper para valores seguros
        def safe_get(key, default="No proporcionado"):
            value = prospect.get(key)
            return value if value else default
        
        # Manejo del score
        score_raw = prospect.get('qualification_score', 0)
        score = int(score_raw) if score_raw else 0
        
        # Datos básicos
        name = safe_get('name')
        company = safe_get('company')
        email = safe_get('email')
        budget = safe_get('budget')
        location = safe_get('location')
        industry = safe_get('industry')
        status = safe_get('status', 'nuevo')
        notes = safe_get('notes', 'Sin notas')
        
        meeting_sent = prospect.get('meeting_link_sent', False)
        meeting_status = "Enviado" if meeting_sent else "Pendiente"
        
        # Calificación basada en score
        if score >= 65:
            qualification = "CALIFICADO - Listo para charla con Lucas"
        elif score >= 50:
            qualification = "INTERES MODERADO - Necesita mas informacion" 
        elif score >= 30:
            qualification = "POCO INTERES - Seguir nutriendo"
        else:
            qualification = "NO CALIFICADO - Considerar descarte"
        
        info = f"""INFORMACION DEL PROSPECTO

ID: {prospect.get('id', 'N/A')} | Sesion: {session_id[:8]}...
Nombre: {name}
Empresa: {company}
Email: {email}
Presupuesto: {budget}
Ubicacion: {location}
Industria: {industry}
Score: {score}/100
Estado: {status}
Link Reunion: {meeting_status}

Calificacion:
{qualification}

Notas:
{notes}

---

Estadisticas:
- Conversaciones: {summary.get('conversation_count', 0)}
- RAG System: {'ACTIVO' if agent.rag_system else 'INACTIVO'}
- Brevo Integration: {'ACTIVO' if agent.brevo_sync else 'INACTIVO'}
"""
        
        return info
        
    except Exception as e:
        print(f"Error en get_prospect_info: {e}")
        return f"Error al obtener informacion: {str(e)}"

def reset_conversation(request: gr.Request = None):
    """Reinicia la conversación"""
    session_id = get_session_id(request)
    
    if session_id in session_prospects:
        del session_prospects[session_id]
    
    return [], "No hay conversacion activa para esta sesion"

# Crear la interfaz de Gradio
with gr.Blocks(title="Agente Inteligente de Lucas Benites", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🤖 Agente Inteligente de Lucas Benites
    **Especialista en Tecnología para PyMEs - Versión Unificada**
    
    ¡Hola! Soy el asistente inteligente de Lucas. Puedo ayudarte con información sobre nuestros servicios 
    y entender las necesidades específicas de tu negocio para conectarte con Lucas cuando sea apropiado.
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                label="Conversacion con el Asistente de Lucas",
                height=500,
                show_label=True,
                type="messages",
                placeholder="Hola! Preguntame sobre los servicios de Lucas o cuentame sobre tu negocio. ¿En que puedo ayudarte?"
            )
            
            with gr.Row():
                msg = gr.Textbox(
                    label="Tu mensaje",
                    placeholder="Escribe tu mensaje aqui...",
                    scale=4
                )
                send_btn = gr.Button("Enviar", scale=1, variant="primary")
            
            with gr.Row():
                clear_btn = gr.Button("Nueva Conversacion", variant="secondary")
        
        with gr.Column(scale=1):
            gr.Markdown("**📊 Informacion del Prospecto**")
            
            prospect_info = gr.Textbox(
                label="Dashboard",
                lines=20,
                interactive=False,
                show_label=False
            )
            
            refresh_btn = gr.Button("🔄 Actualizar Info", variant="secondary")
            
            gr.Markdown("""
            **✨ Características:**
            
            • **Deteccion Inteligente**: Identifica automáticamente el contexto de tu consulta
            • **RAG Integrado**: Información actualizada sobre Lucas y sus servicios  
            • **Calificacion Automatica**: Evalúa el fit entre tu negocio y nuestros servicios
            • **Brevo CRM**: Sincronización automática para seguimiento profesional
            
            ---
            
            **📞 Contacto Directo:**
            - Email: lucas@lucasbenites.com
            - WhatsApp: +54 3517554495
            - Calendario: https://meet.brevo.com/lucas-benites
            """)
    
    # Event handlers
    def respond(message, history, request: gr.Request = None):
        return chat_interface(message, history, request)
    
    def handle_reset(request: gr.Request = None):
        messages, info = reset_conversation(request)
        return messages, info
    
    def handle_refresh(request: gr.Request = None):
        return get_prospect_info(request)
    
    # Configurar eventos
    msg.submit(respond, [msg, chatbot], [chatbot])
    msg.submit(lambda: "", None, [msg])
    
    send_btn.click(respond, [msg, chatbot], [chatbot])
    send_btn.click(lambda: "", None, [msg])
    
    clear_btn.click(handle_reset, None, [chatbot, prospect_info])
    
    refresh_btn.click(handle_refresh, None, [prospect_info])
    
    # Auto-actualizar info del prospecto después de cada mensaje
    chatbot.change(handle_refresh, None, [prospect_info])

# Para Hugging Face Spaces
if __name__ == "__main__":
    demo.launch()