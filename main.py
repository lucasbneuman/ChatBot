# agents/main.py - UI SIMPLIFICADA
import os
import gradio as gr
import uuid
from dotenv import load_dotenv
from app.agents.prospecting_agent import ProspectingAgent
from app.database.prospect_db import ProspectDatabase

# Cargar variables de entorno
load_dotenv()

# Inicializar agente
agent = ProspectingAgent(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    db_path="prospects.db"
)

db = ProspectDatabase("prospects.db")

# Diccionario para mantener prospect_ids por sesión
session_prospects = {}

def get_session_id(request: gr.Request = None) -> str:
    """Genera o recupera un ID único por sesión"""
    if request and hasattr(request, 'session_hash'):
        return str(request.session_hash)
    else:
        return str(uuid.uuid4())

def chat_interface(message, history, request: gr.Request = None):
    """Interfaz de chat para Gradio - MULTI-USUARIO"""
    session_id = get_session_id(request)
    
    print(f"🎯 DEBUG chat_interface - session_id: {session_id}")
    
    # Obtener prospect_id para esta sesión específica
    current_prospect_id = session_prospects.get(session_id)
    print(f"🎯 DEBUG - current_prospect_id para sesión {session_id}: {current_prospect_id}")
    
    if not message.strip():
        return history
    
    # Procesar mensaje con el agente
    result = agent.process_message(message, current_prospect_id)
    
    # Actualizar prospect_id para esta sesión si es nuevo
    if not current_prospect_id:
        current_prospect_id = result.get("prospect_id")
        session_prospects[session_id] = current_prospect_id
        print(f"🆕 DEBUG - Nuevo prospect_id {current_prospect_id} asignado a sesión {session_id}")
    
    # Obtener respuesta
    response = result.get("response", "Lo siento, no pude procesar tu mensaje.")
    
    # Actualizar historial en formato messages
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": response})
    
    return history

def get_prospect_info(request: gr.Request = None):
    """Obtiene información del prospecto actual - MULTI-USUARIO"""
    session_id = get_session_id(request)
    current_prospect_id = session_prospects.get(session_id)
    
    print(f"🔍 DEBUG get_prospect_info - session_id: {session_id}, prospect_id: {current_prospect_id}")
    
    if not current_prospect_id:
        return "No hay conversación activa para esta sesión"
    
    try:
        summary = agent.get_prospect_summary(current_prospect_id)
        print(f"📊 DEBUG - Summary recibido: {summary}")
        
        if not summary or "error" in summary:
            error_msg = summary.get("error", "Unknown error") if summary else "No summary returned"
            return f"❌ Error: {error_msg}"
        
        prospect = summary["prospect"]
        
        # MANEJO ROBUSTO DE VALORES
        def safe_get(key, default="No proporcionado"):
            value = prospect.get(key)
            return value if value else default
        
        # Manejo especial del score
        score_raw = prospect.get('qualification_score')
        if score_raw is None:
            score = 0
        elif isinstance(score_raw, str):
            try:
                score = int(float(score_raw))
            except:
                score = 0
        else:
            score = int(score_raw)
        
        name = safe_get('name')
        company = safe_get('company')
        budget = safe_get('budget')
        location = safe_get('location')
        industry = safe_get('industry')
        status = safe_get('status', 'nuevo')
        notes = safe_get('notes', 'Sin notas')
        
        meeting_sent = prospect.get('meeting_link_sent')
        meeting_status = "✅ Enviado" if meeting_sent else "❌ Pendiente"
        
        # MEJORAR NOTAS CON IA SI HAY SUFICIENTE INFORMACIÓN
        if len(str(notes)) > 100 and notes != 'Sin notas':
            try:
                improved_notes = agent.response_gen.improve_notes_with_ai(notes)
                if improved_notes and improved_notes != notes:
                    notes = improved_notes
                    # Actualizar las notas mejoradas en la base de datos
                    prospect_obj = agent.db.get_prospect(current_prospect_id)
                    if prospect_obj:
                        prospect_obj.notes = improved_notes
                        agent.db.update_prospect(prospect_obj)
                        print(f"📝 Notas mejoradas y guardadas para prospect {current_prospect_id}")
            except Exception as e:
                print(f"❌ Error mejorando notas: {e}")
        
        info = f"""**Información del Prospecto:**

🆔 **ID:** {prospect.get('id', 'N/A')} | 🔑 **Sesión:** {session_id[:8]}...
👤 **Nombre:** {name}
🏢 **Empresa:** {company}
💰 **Presupuesto:** {budget}
📍 **Ubicación:** {location}
🏭 **Industria:** {industry}
📊 **Score:** {score}/100
⚡ **Estado:** {status}
🔗 **Link Reunión:** {meeting_status}

**Notas:**
{notes}

---

**Resumen de Calificación:**
{summary.get('qualification_summary', 'No disponible')}

**Total Conversaciones:** {summary.get('conversation_count', 0)}
"""
        
        return info
        
    except Exception as e:
        print(f"❌ ERROR en get_prospect_info: {e}")
        return f"❌ Error al obtener información: {str(e)}"

def reset_conversation(request: gr.Request = None):
    """Reinicia la conversación - MULTI-USUARIO"""
    session_id = get_session_id(request)
    
    # Limpiar el prospect_id para esta sesión
    if session_id in session_prospects:
        del session_prospects[session_id]
    
    return [], "No hay conversación activa para esta sesión"

def create_gradio_interface():
    """Crea la interfaz de Gradio simplificada"""
    
    with gr.Blocks(title="Chatbot de Prospección - Lucas Benites", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🤖 Asistente de Prospección - Lucas Benites
        
        **Ayudo a dueños de PyMEs a automatizar sus negocios con IA**
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    label="Conversación",
                    height=500,
                    show_label=True,
                    type="messages",
                    placeholder="¡Hola! Soy el asistente de Lucas. ¿En qué puedo ayudarte con tu negocio hoy?"
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        label="Tu mensaje",
                        placeholder="Escribe aquí cómo puedo ayudarte...",
                        scale=4
                    )
                    send_btn = gr.Button("Enviar", scale=1, variant="primary")
                
                with gr.Row():
                    clear_btn = gr.Button("🔄 Nueva Conversación", variant="secondary")
            
            with gr.Column(scale=1):
                gr.Markdown("### 📊 Información del Prospecto")
                
                prospect_info = gr.Textbox(
                    label="Datos del Lead",
                    lines=20,
                    interactive=False,
                    show_label=False
                )
                
                refresh_btn = gr.Button("🔄 Actualizar Info", variant="secondary")
                
                gr.Markdown("""
                ### 🎯 Sobre Lucas Benites
                
                **Especialista en IA para PyMEs:**
                - 🤖 Chatbots que atienden clientes 24/7
                - ⚡ Automatización de procesos repetitivos  
                - 🧠 IA personalizada para cada negocio
                - 📊 Herramientas que ahorran tiempo y dinero
                
                **🔗 Agenda tu charla:** https://meet.brevo.com/lucas-benites
                
                ### 📈 Cómo funciona el scoring:
                - **65+ puntos:** Listo para charla con Lucas
                - **50-64 puntos:** Interés moderado
                - **30-49 puntos:** Poco interés
                - **<30 puntos:** Sin interés
                """)
        
        # Event handlers simplificados
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
    
    return demo

if __name__ == "__main__":
    # Crear interfaz
    demo = create_gradio_interface()
    
    # Lanzar aplicación
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=True,
        debug=True
    )