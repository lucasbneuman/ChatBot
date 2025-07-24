#!/usr/bin/env python3
"""
Servidor Multi-Canal para Lucas Benites
Combina Gradio (admin) + FastAPI (widget) en un solo proceso
"""

import os
import asyncio
import threading
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Importar las interfaces
from app.interfaces.widget_api import app as widget_app

# Cargar variables de entorno
load_dotenv()

def create_unified_server():
    """Crea servidor unificado FastAPI + Gradio"""
    
    # App principal FastAPI
    main_app = FastAPI(
        title="Lucas Benites - Multi-Channel Server",
        description="Servidor unificado para widget web y dashboard admin",
        version="2.0.0"
    )
    
    # Montar widget API
    main_app.mount("/api", widget_app)
    
    # Servir archivos estáticos del widget
    static_path = Path(__file__).parent / "static"
    if static_path.exists():
        main_app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    @main_app.get("/")
    async def root():
        return {
            "service": "Lucas Benites Multi-Channel Server",
            "version": "2.0.0",
            "endpoints": {
                "widget_api": "/api",
                "widget_files": "/static/widget",
                "admin_dashboard": "/admin (Gradio - puerto 7863)"
            },
            "status": "online"
        }
    
    @main_app.get("/widget/embed")
    async def widget_embed():
        """Código de embed para WordPress"""
        embed_code = f"""
<!-- Lucas Benites Chat Widget -->
<script>
    window.LUCAS_WIDGET_CONFIG = {{
        apiUrl: '{os.getenv("WIDGET_API_URL", "http://localhost:8002")}/api',
        position: 'bottom-right',
        autoOpen: false
    }};
</script>
<script src="{os.getenv("WIDGET_STATIC_URL", "http://localhost:8002")}/static/widget/lucas-chat-widget.js" 
        data-api-url="{os.getenv("WIDGET_API_URL", "http://localhost:8002")}/api"
        data-position="bottom-right"
        data-auto-open="false">
</script>
        """.strip()
        
        return {
            "embed_code": embed_code,
            "instructions": [
                "1. Copia el código de arriba",
                "2. Pégalo en tu WordPress antes del </body>",
                "3. El widget aparecerá automáticamente",
                "4. Personaliza la configuración si es necesario"
            ]
        }
    
    return main_app

def find_free_port(start_port=7863):
    """Encuentra un puerto libre empezando desde start_port"""
    import socket
    for port in range(start_port, start_port + 10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

def run_gradio_server():
    """Ejecuta el servidor Gradio en un hilo separado"""
    try:
        import gradio as gr
        from main import create_gradio_interface
        
        # Encontrar puerto libre
        gradio_port = find_free_port(7863)
        if not gradio_port:
            print("ERROR No se pudo encontrar puerto libre para Gradio")
            return
        
        print(f"Iniciando Dashboard Admin (Gradio) en puerto {gradio_port}...")
        
        demo = create_gradio_interface()
        demo.launch(
            server_name="127.0.0.1",
            server_port=gradio_port,
            share=False,
            debug=False,
            show_api=False,
            quiet=True
        )
        
        # Guardar puerto para referencia
        global gradio_running_port
        gradio_running_port = gradio_port
        
    except Exception as e:
        print(f"ERROR iniciando Gradio: {e}")

# Variable global para puerto de Gradio
gradio_running_port = None

def main():
    """Función principal del servidor"""
    print("INICIANDO SERVIDOR MULTI-CANAL")
    print("=" * 50)
    
    # Verificar variables de entorno
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"ERROR Variables de entorno faltantes: {', '.join(missing_vars)}")
        print("NOTA Configura tu archivo .env")
        return
    
    # Crear app unificada
    app = create_unified_server()
    
    # Iniciar Gradio en hilo separado
    gradio_thread = threading.Thread(target=run_gradio_server, daemon=True)
    gradio_thread.start()
    
    # Esperar un poco para que Gradio se inicie
    import time
    time.sleep(3)
    
    print("OK Servicios iniciados:")
    print(f"   Widget API: http://localhost:8002")
    
    if gradio_running_port:
        print(f"   Admin Dashboard: http://localhost:{gradio_running_port}") 
    else:
        print("   Admin Dashboard: ERROR No se pudo iniciar")
        
    print(f"   Widget Embed: http://localhost:8002/widget/embed")
    print(f"   Static Files: http://localhost:8002/static/widget/")
    print()
    print("Para WordPress:")
    print("   Ve a http://localhost:8002/widget/embed para obtener el código")
    print()
    
    # Iniciar servidor FastAPI
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8002,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\nCerrando servidor...")
    except Exception as e:
        print(f"ERROR en servidor: {e}")

if __name__ == "__main__":
    main()