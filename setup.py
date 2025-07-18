# setup.py
"""
Script de configuración inicial para el chatbot de prospección
"""

import os
import sys
from pathlib import Path

def create_directory_structure():
    """Crea la estructura de directorios necesaria"""
    directories = [
        "app",
        "app/agents", 
        "app/nodes",
        "app/database",
        "test"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        Path(directory + "/__init__.py").touch(exist_ok=True)
    
    print("✅ Estructura de directorios creada")

def create_env_file():
    """Crea archivo .env si no existe"""
    env_content = """# Configuración del Chatbot de Prospección
OPENAI_API_KEY=your_openai_api_key_here
BREVO_API_KEY=your_brevo_api_key_here  
DATABASE_URL=sqlite:///./prospects.db
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Archivo .env creado")
        print("⚠️  IMPORTANTE: Edita el archivo .env con tus API keys reales")
    else:
        print("✅ Archivo .env ya existe")

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    required_packages = [
        "openai",
        "langchain", 
        "langgraph",
        "gradio",
        "pydantic",
        "python-dotenv",
        "requests"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Instala los paquetes faltantes:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def main():
    """Función principal de configuración"""
    print("🤖 Configurando Chatbot de Prospección...")
    print("=" * 50)
    
    # Crear estructura
    create_directory_structure()
    
    # Crear .env
    create_env_file()
    
    # Verificar dependencias
    print("\n📦 Verificando dependencias...")
    if check_dependencies():
        print("\n🎉 ¡Configuración completada!")
        print("\n📋 Próximos pasos:")
        print("1. Edita el archivo .env con tus API keys")
        print("2. Ejecuta: python main.py")
        print("3. Abre http://localhost:7860 en tu navegador")
    else:
        print("\n❌ Instala las dependencias faltantes primero")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())