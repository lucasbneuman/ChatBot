# main.py - Versión corregida
import os
import sys
import gradio as gr
from pathlib import Path

# Verificar estructura de directorios
def ensure_directory_structure():
    """Asegura que la estructura de directorios existe"""
    directories = ["app", "app/agents", "app/nodes", "app/database"]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        init_file = Path(directory) / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Módulo auto-generado"""')

# Ejecutar antes de imports
ensure_directory_structure()

try:
    from dotenv import load_dotenv
    from app.agents.prospecting_agent import ProspectingAgent
    from app.database.prospect_db import ProspectDatabase
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("💡 Ejecuta primero: python setup.py")
    sys.exit(1)

# Cargar variables de entorno
load_dotenv()

# Verificar API key
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key or openai_key == "your_openai_api_key_here":
    print("❌ Error: OPENAI_API_KEY no configurada")
    print("📝 Edita el archivo .env con tu API key real")
    sys.exit(1)

try:
    # Inicializar agente
    agent = ProspectingAgent(
        openai_api_key=openai_key,
        db_path="prospects.db"
    )
    db = ProspectDatabase("prospects.db")
    print("✅ Sistema inicializado correctamente")
except Exception as e:
    print(f"❌ Error inicializando sistema: {e}")
    sys.exit(1)

# Estado global para mantener el prospect_id actual
current_prospect_id = None

def chat_interface(message, history):
    """Interfaz de chat para Gradio"""
    global current_prospect_id
    
    if not message or not message.strip():
        return history
    
    try:
        # Procesar mensaje con el agente
        result = agent.process_message(message, current_prospect_id)
        
        # Actualizar prospect_id si es nuevo
        if not current_prospect_id:
            current_prospect_id = result.get("prospect_id")
        
        # Obtener respuesta
        response = result.get("response", "Lo siento, no pude procesar tu mensaje.")
        
        # Actualizar historial en formato messages
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})
        
        return history
        
    except Exception as e:
        print(f"Error procesando mensaje: {e}")
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": "Disculpa, hubo un error técnico. ¿Podrías repetir tu mensaje?"})
        return history

def get_prospect_info():
    """Obtiene información del prospecto actual"""
    global current_prospect_id
    
    if not current_prospect_id:
        return "No hay conversación activa"
    
    try:
        summary = agent.get_prospect_summary(current_prospect_id)
        
        if not summary:
            return "No se encontró información del prospecto"
        
        prospect = summary["prospect"]
        
        info = f"""**Información del Prospecto:**

🆔 **ID:** {prospect.get('id', 'N/A')}
👤 **Nombre:** {prospect.get('name', 'No proporcionado')}
🏢 **Empresa:** {prospect.get('company', 'No proporcionado')}
💰 **Presupuesto:** {prospect.get('budget', 'No proporcionado')}
📍 **Ubicación:** {prospect.get('location', 'No proporcionado')}
🏭 **Industria:** {prospect.get('industry', 'No proporcionado')}
📊 **Score:** {prospect.get('qualification_score', 0)}/100
⚡ **Estado:** {prospect.get('status', 'nuevo')}

**Resumen de Calificación:**
{summary.get('qualification_summary', 'No disponible')}

**Conversaciones:** {summary.get('conversation_count', 0)}
"""
        
        return info
        
    except Exception as e:
        return f"Error obteniendo información: {e}"

def reset_conversation():
    """Reinicia la conversación"""
    global current_prospect_id
    current_prospect_id = None
    return []

def create_gradio_interface():
    """Crea la interfaz de Gradio"""
    
    with gr.Blocks(title="Chatbot de Prospección Inteligente", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🤖 Chatbot de Prospección Inteligente
        
        Sistema automatizado de calificación de leads con IA.
        El bot recopila información clave y califica automáticamente a los prospectos.
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    label="Conversación",
                    height=500,
                    show_label=True,
                    type="messages"
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        label="Mensaje",
                        placeholder="Escribe tu mensaje aquí...",
                        scale=4
                    )
                    send_btn = gr.Button("Enviar", scale=1, variant="primary")
                
                with gr.Row():
                    clear_btn = gr.Button("Nueva Conversación", variant="secondary")
            
            with gr.Column(scale=1):
                gr.Markdown("### 📊 Información del Prospecto")
                
                prospect_info = gr.Textbox(
                    label="Datos del Lead",
                    lines=15,
                    interactive=False,
                    show_label=False
                )
                
                refresh_btn = gr.Button("🔄 Actualizar Info", variant="secondary")
                
                gr.Markdown("""
                ### 🎯 Criterios de Calificación
                
                **Información Básica (30pts):**
                - Nombre (10pts)
                - Empresa (10pts) 
                - Industria (10pts)
                
                **Presupuesto (25pts):**
                - Mención de cifras (25pts)
                - Interés general (15pts)
                
                **Ubicación (15pts):**
                - Datos geográficos (15pts)
                
                **Engagement (30pts):**
                - Pain points identificados (5pts c/u)
                - Tomador de decisiones (15pts)
                
                **Calificado:** ≥60pts
                """)
        
        # Event handlers
        def respond(message, history):
            return chat_interface(message, history)
        
        # Configurar eventos
        msg.submit(respond, [msg, chatbot], [chatbot])
        msg.submit(lambda: "", None, [msg])
        
        send_btn.click(respond, [msg, chatbot], [chatbot])
        send_btn.click(lambda: "", None, [msg])
        
        clear_btn.click(reset_conversation, None, [chatbot])
        
        refresh_btn.click(get_prospect_info, None, [prospect_info])
        
        # Auto-actualizar info del prospecto después de cada mensaje
        chatbot.change(get_prospect_info, None, [prospect_info])
    
    return demo

if __name__ == "__main__":
    print("🚀 Iniciando Chatbot de Prospección...")
    
    try:
        # Crear interfaz
        demo = create_gradio_interface()
        
        # Lanzar aplicación
        print("🌐 Abriendo interfaz web...")
        demo.launch(
            server_name="127.0.0.1",  # Cambio para Windows
            server_port=7860,
            share=False,
            debug=False,  # Desactivar debug para menos warnings
            show_error=True
        )
        
    except Exception as e:
        print(f"❌ Error iniciando aplicación: {e}")
        print("💡 Verifica que todos los módulos estén instalados correctamente")
        sys.exit(1)