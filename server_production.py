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
from fastapi import FastAPI
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
    """Ejecuta el servidor Gradio si está habilitado"""
    try:
        # Solo ejecutar Gradio si está habilitado y hay suficiente memoria
        if os.getenv("ENABLE_GRADIO", "false").lower() == "true":
            print("Intentando iniciar Dashboard Admin (Gradio)...")
            
            # Verificar si es Render (limitaciones de memoria)
            if os.getenv("RENDER", "false").lower() == "true":
                print("Render detectado - Gradio deshabilitado por limitaciones de memoria")
                return
            
            import gradio as gr
            from main import create_gradio_interface
            
            gradio_port = int(os.getenv("GRADIO_PORT", "7860"))
            print(f"Iniciando Dashboard Admin (Gradio) en puerto {gradio_port}...")
            
            demo = create_gradio_interface()
            demo.launch(
                server_name="0.0.0.0",
                server_port=gradio_port,
                share=False,
                debug=False,
                show_api=False,
                quiet=True
            )
        else:
            print("Gradio deshabilitado en producción (ENABLE_GRADIO=false)")
            
    except Exception as e:
        print(f"ERROR iniciando Gradio: {e}")
        print("Continuando sin Dashboard Admin...")

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
    
    # Iniciar Gradio si está habilitado
    if os.getenv("ENABLE_GRADIO", "false").lower() == "true":
        gradio_thread = threading.Thread(target=run_gradio_server, daemon=True)
        gradio_thread.start()
    
    print("OK Servicios iniciados:")
    print(f"   Widget API: http://{host}:{port}")
    print(f"   Widget Embed: http://{host}:{port}/widget/embed")
    print(f"   Health Check: http://{host}:{port}/health")
    
    if os.getenv("ENABLE_GRADIO", "false").lower() == "true":
        gradio_port = os.getenv("GRADIO_PORT", "7860")
        print(f"   Admin Dashboard: http://{host}:{gradio_port}")
    
    print("\nPara WordPress:")
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