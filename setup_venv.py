#!/usr/bin/env python3
"""
Script de setup automatizado para el proyecto de Lucas Benites
Migra de conda a venv y configura el entorno de desarrollo
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_step(message):
    """Imprime un paso del proceso"""
    print(f"\n🔧 {message}")
    print("=" * (len(message) + 4))

def run_command(command, description=""):
    """Ejecuta un comando y maneja errores"""
    try:
        if description:
            print(f"   Ejecutando: {description}")
        
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        
        if result.stdout:
            print(f"   ✅ {result.stdout.strip()}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        if e.stderr:
            print(f"   ❌ Error details: {e.stderr}")
        return False

def check_python_version():
    """Verifica que Python sea 3.8+"""
    print_step("Verificando versión de Python")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("   ❌ Se requiere Python 3.8 o superior")
        print(f"   📍 Versión actual: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} detectado")
    return True

def remove_conda_env():
    """Intenta desactivar entorno conda si existe"""
    print_step("Verificando entorno conda")
    
    # Verificar si estamos en un entorno conda
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env and conda_env != 'base':
        print(f"   ⚠️ Entorno conda activo: {conda_env}")
        print("   💡 Por favor ejecuta 'conda deactivate' y vuelve a ejecutar este script")
        return False
    
    print("   ✅ No hay entorno conda activo")
    return True

def setup_venv():
    """Crea y configura el entorno virtual"""
    print_step("Configurando entorno virtual venv")
    
    venv_path = Path("venv")
    
    # Eliminar venv existente si existe
    if venv_path.exists():
        print("   🗑️ Eliminando entorno venv existente...")
        shutil.rmtree(venv_path)
    
    # Crear nuevo venv
    print("   📦 Creando nuevo entorno virtual...")
    if not run_command("python -m venv venv", "Crear venv"):
        return False
    
    # Verificar que se creó correctamente
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    if not python_exe.exists():
        print("   ❌ Error creando el entorno virtual")
        return False
    
    print("   ✅ Entorno virtual creado exitosamente")
    
    # Actualizar pip en el venv
    print("   ⬆️ Actualizando pip...")
    pip_cmd = f'"{pip_exe}" install --upgrade pip'
    if not run_command(pip_cmd, "Actualizar pip"):
        print("   ⚠️ Advertencia: No se pudo actualizar pip, continuando...")
    
    return True

def install_dependencies():
    """Instala las dependencias del proyecto"""
    print_step("Instalando dependencias")
    
    if not Path("requirements.txt").exists():
        print("   ❌ Archivo requirements.txt no encontrado")
        return False
    
    # Comando para instalar dependencias
    if sys.platform == "win32":
        pip_cmd = '"venv/Scripts/pip.exe" install -r requirements.txt'
    else:
        pip_cmd = "venv/bin/pip install -r requirements.txt"
    
    print("   📦 Instalando paquetes Python...")
    print("   ⏳ Esto puede tomar varios minutos...")
    
    if not run_command(pip_cmd, "Instalar dependencias"):
        print("   ❌ Error instalando dependencias")
        return False
    
    print("   ✅ Dependencias instaladas exitosamente")
    return True

def verify_installation():
    """Verifica que la instalación sea correcta"""
    print_step("Verificando instalación")
    
    # Comando para verificar imports
    if sys.platform == "win32":
        python_cmd = '"venv/Scripts/python.exe"'
    else:
        python_cmd = "venv/bin/python"
    
    test_imports = [
        "fastapi",
        "gradio", 
        "openai",
        "langchain"
    ]
    
    for package in test_imports:
        cmd = f'{python_cmd} -c "import {package}; print(f\\"{package} OK\\")"'
        if not run_command(cmd, f"Verificar {package}"):
            print(f"   ❌ Error importando {package}")
            return False
    
    print("   ✅ Todas las librerías principales funcionan correctamente")
    return True

def create_env_template():
    """Crea template de archivo .env si no existe"""
    print_step("Configurando variables de entorno")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("   ✅ Archivo .env ya existe")
        return True
    
    # Crear .env.example como template
    env_template = '''# Configuración de Lucas Benites Agent
# Copia este archivo a .env y completa con tus API keys

# OpenAI API Key (obligatorio)
OPENAI_API_KEY=tu-openai-api-key-aqui

# Brevo API Key (obligatorio para CRM)
BREVO_API_KEY=tu-brevo-api-key-aqui

# Configuración de entorno
ENVIRONMENT=development

# Configuración para deploy (opcional)
RENDER=false
ENABLE_GRADIO=true
'''
    
    try:
        with open(env_example, 'w', encoding='utf-8') as f:
            f.write(env_template)
        print("   ✅ Archivo .env.example creado")
        print("   💡 Copia .env.example a .env y configura tus API keys")
        
    except Exception as e:
        print(f"   ⚠️ Error creando .env.example: {e}")
    
    return True

def print_next_steps():
    """Muestra los próximos pasos al usuario"""
    print_step("¡Setup completado! 🎉")
    
    print("\n📋 PRÓXIMOS PASOS:")
    print("   1. Configura tus API keys:")
    if sys.platform == "win32":
        print("      • Copia .env.example a .env")
        print("      • Edita .env con tus claves de OpenAI y Brevo")
    else:
        print("      • cp .env.example .env")
        print("      • Edita .env con tus claves de OpenAI y Brevo")
    
    print("\n   2. Activa el entorno virtual:")
    if sys.platform == "win32":
        print("      • venv\\Scripts\\activate")
    else:
        print("      • source venv/bin/activate")
    
    print("\n   3. Ejecuta la aplicación:")
    print("      • python main.py                 (Dashboard Gradio)")
    print("      • python server_widget.py        (Widget WordPress)")
    print("      • python server_production.py    (Solo API)")
    
    print("\n   4. Prueba el sistema:")
    print("      • python test/test_supervisor_flow.py")
    print("      • python test_brevo_connection.py")
    
    print("\n🌐 URLs importantes:")
    print("   • Widget demo: http://localhost:8002")
    print("   • Dashboard: http://localhost:7864")
    print("   • API docs: http://localhost:8002/docs")
    
    print("\n📚 Documentación completa en README.md")

def main():
    """Función principal del setup"""
    print("🚀 SETUP AUTOMATIZADO - LUCAS BENITES AGENT")
    print("=" * 50)
    print("🔄 Migrando de conda a venv...")
    
    # Verificar Python
    if not check_python_version():
        sys.exit(1)
    
    # Verificar conda
    if not remove_conda_env():
        sys.exit(1)
    
    # Setup venv
    if not setup_venv():
        print("\n❌ Error configurando entorno virtual")
        sys.exit(1)
    
    # Instalar dependencias
    if not install_dependencies():
        print("\n❌ Error instalando dependencias")
        sys.exit(1)
    
    # Verificar instalación
    if not verify_installation():
        print("\n❌ Error verificando instalación")
        sys.exit(1)
    
    # Configurar .env
    create_env_template()
    
    # Mostrar próximos pasos
    print_next_steps()
    
    print(f"\n🎯 Setup completado exitosamente!")
    print("   El proyecto está listo para usar con venv")

if __name__ == "__main__":
    main()