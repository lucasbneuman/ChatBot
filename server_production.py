#!/usr/bin/env python3
"""
Servidor de Producción - Lucas Benites Multi-Channel
Optimizado para deploy en cloud con puertos dinámicos
"""

import os
import asyncio
import threading
from pathlib import Path
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Importar las interfaces
from app.interfaces.widget_api import app as widget_app

# Cargar variables de entorno
load_dotenv()

def create_production_server():
    """Crea servidor optimizado para producción"""
    
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
            "status": "online",
            "endpoints": {
                "widget_api": "/api",
                "widget_files": "/static/widget",
                "health": "/health",
                "embed_code": "/widget/embed"
            }
        }
    
    @main_app.get("/health")
    async def health_check():
        """Health check para monitoreo"""
        return {
            "status": "healthy",
            "version": "2.0.0",
            "timestamp": asyncio.get_event_loop().time()
        }
    
    @main_app.get("/ip")
    async def get_server_ip(request: Request):
        """Obtiene la IP del servidor para configurar en Brevo"""
        import requests
        try:
            # Obtener IP pública
            ip_response = requests.get("https://api.ipify.org", timeout=5)
            public_ip = ip_response.text
            
            return {
                "public_ip": public_ip,
                "client_ip": request.client.host,
                "headers": dict(request.headers),
                "note": "Agrega la public_ip a las IPs permitidas en Brevo"
            }
        except Exception as e:
            return {"error": str(e)}
    
    @main_app.get("/widget/embed")
    async def widget_embed():
        """Código de embed para WordPress con URLs dinámicas"""
        
        # Detectar URL base desde variables de entorno o request
        base_url = os.getenv("WIDGET_BASE_URL", "https://tu-dominio.railway.app")
        
        embed_code = f"""
<!-- Lucas Benites Chat Widget -->
<script>
    window.LUCAS_WIDGET_CONFIG = {{
        apiUrl: '{base_url}/api',
        position: 'bottom-right',
        autoOpen: false,
        theme: 'blue'
    }};
</script>
<script src="{base_url}/static/widget/lucas-chat-widget.js" 
        data-api-url="{base_url}/api"
        data-position="bottom-right"
        data-auto-open="false">
</script>
        """.strip()
        
        return {
            "embed_code": embed_code,
            "instructions": [
                "1. Copia el código de arriba",
                "2. Ve a tu WordPress Admin",
                "3. Instala plugin 'Insert Headers and Footers'",
                "4. Pega el código en 'Scripts in Footer'",
                "5. Guarda y el widget aparecerá en tu sitio"
            ],
            "base_url": base_url
        }
    
    return main_app

def run_gradio_server():
    """Ejecuta el servidor Gradio para dashboard admin"""
    try:
        # Intentar encontrar puerto libre para Gradio
        gradio_port = find_free_port(7863)
        if not gradio_port:
            print("No se pudo encontrar puerto libre para Gradio")
            return
        
        print(f"Iniciando Dashboard Admin (Gradio) en puerto {gradio_port}...")
        
        # Importar y crear interfaz Gradio
        import gradio as gr
        from main import create_gradio_interface
        
        demo = create_gradio_interface()
        demo.launch(
            server_name="0.0.0.0",
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
        print("El servidor continuará funcionando solo con Widget API")

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

# Variable global para puerto de Gradio
gradio_running_port = None

def main():
    """Función principal del servidor de producción"""
    print("INICIANDO SERVIDOR DE PRODUCCION - LUCAS BENITES")
    print("=" * 60)
    
    # Variables de entorno requeridas
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"ERROR Variables de entorno faltantes: {', '.join(missing_vars)}")
        return
    
    # Obtener configuración de puerto (Railway/Render usan PORT)
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Crear app
    app = create_production_server()
    
    # Iniciar Gradio en hilo separado (solo si no es Render o está habilitado)
    enable_gradio = os.getenv("ENABLE_GRADIO", "true").lower() == "true"
    is_render = os.getenv("RENDER", "false").lower() == "true"
    
    if enable_gradio and not is_render:
        gradio_thread = threading.Thread(target=run_gradio_server, daemon=True)
        gradio_thread.start()
        
        # Esperar un poco para que Gradio se inicie
        import time
        time.sleep(3)
    
    print("OK Servicios iniciados:")
    print(f"   Widget API: http://{host}:{port}")
    print(f"   Widget Embed: http://{host}:{port}/widget/embed")
    print(f"   Health Check: http://{host}:{port}/health")
    
    if enable_gradio and not is_render and gradio_running_port:
        print(f"   Admin Dashboard: http://{host}:{gradio_running_port}")
    elif is_render:
        print("   Admin Dashboard: Deshabilitado en Render (memoria limitada)")
    else:
        print("   Admin Dashboard: Deshabilitado")
        
    print(f"   Codigo embed: http://{host}:{port}/widget/embed")
    print()
    
    # Iniciar servidor
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\nCerrando servidor...")
    except Exception as e:
        print(f"ERROR en servidor: {e}")

if __name__ == "__main__":
    main()