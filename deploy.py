#!/usr/bin/env python3
"""
Script de despliegue para el Agente Inteligente de Lucas Benites
"""

import os
import subprocess
import sys
from pathlib import Path

def check_requirements():
    """Verifica que los archivos necesarios existan"""
    required_files = [
        'app.py',
        'requirements_production.txt',
        'Dockerfile',
        '.env'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Archivos faltantes:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ Todos los archivos necesarios están presentes")
    return True

def check_env_vars():
    """Verifica que las variables de entorno estén configuradas"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['OPENAI_API_KEY', 'BREVO_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Variables de entorno faltantes:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Configura tu archivo .env basado en .env.production.example")
        return False
    
    print("✅ Variables de entorno configuradas correctamente")
    return True

def test_local():
    """Prueba la aplicación localmente"""
    print("🧪 Probando aplicación localmente...")
    try:
        # Importar y verificar que no hay errores
        from app.agents.unified_agent import UnifiedAgent
        
        agent = UnifiedAgent(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            db_path="prospects_production.db"
        )
        
        print("✅ Aplicación funciona correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en la aplicación: {e}")
        return False

def deploy_options():
    """Muestra opciones de despliegue"""
    print("\n🚀 OPCIONES DE DESPLIEGUE:")
    print("\n1. 🤗 HUGGING FACE SPACES (Gratis, fácil)")
    print("   - Sube tu código a GitHub")
    print("   - Crea un Space en https://huggingface.co/spaces")
    print("   - Conecta con tu repo GitHub")
    print("   - Configura las variables de entorno en Settings")
    
    print("\n2. 🚄 RAILWAY (Recomendado para producción)")
    print("   - Registrate en https://railway.app")
    print("   - railway login")
    print("   - railway link")
    print("   - railway up")
    
    print("\n3. ☁️ GOOGLE CLOUD RUN")
    print("   - gcloud builds submit --tag gcr.io/[PROJECT_ID]/agent")
    print("   - gcloud run deploy --image gcr.io/[PROJECT_ID]/agent")
    
    print("\n4. 🐳 DOCKER LOCAL")
    print("   - docker build -t agent-lucas .")
    print("   - docker run -p 7860:7860 --env-file .env agent-lucas")

def main():
    print("🤖 DESPLIEGUE DEL AGENTE INTELIGENTE DE LUCAS BENITES")
    print("=" * 60)
    
    # Verificaciones previas
    if not check_requirements():
        sys.exit(1)
        
    if not check_env_vars():
        sys.exit(1)
        
    if not test_local():
        sys.exit(1)
    
    # Mostrar opciones
    deploy_options()
    
    print("\n✅ Sistema listo para desplegar!")
    print("📖 Consulta la documentación específica de cada plataforma")

if __name__ == "__main__":
    main()