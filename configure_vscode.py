#!/usr/bin/env python3
"""
Script para configurar VSCode automáticamente para usar venv
"""

import json
import os
import subprocess
import sys
from pathlib import Path

def print_step(message):
    """Imprime un paso del proceso"""
    print(f"\n🔧 {message}")
    print("=" * (len(message) + 4))

def check_vscode_installed():
    """Verifica si VSCode está instalado"""
    print_step("Verificando VSCode")
    
    try:
        result = subprocess.run("code --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"   ✅ VSCode {version} detectado")
            return True
        else:
            print("   ❌ VSCode no encontrado en PATH")
            return False
    except Exception as e:
        print(f"   ❌ Error verificando VSCode: {e}")
        return False

def get_python_path():
    """Obtiene la ruta del intérprete de Python en venv"""
    print_step("Detectando intérprete de Python")
    
    if sys.platform == "win32":
        python_path = Path("venv/Scripts/python.exe")
    else:
        python_path = Path("venv/bin/python")
    
    if python_path.exists():
        abs_path = python_path.resolve()
        print(f"   ✅ Python encontrado: {abs_path}")
        return str(abs_path)
    else:
        print(f"   ❌ Python no encontrado en: {python_path}")
        return None

def create_vscode_workspace():
    """Crea un archivo de workspace para VSCode"""
    print_step("Creando workspace de VSCode")
    
    python_path = get_python_path()
    if not python_path:
        return False
    
    workspace_config = {
        "folders": [
            {
                "path": "."
            }
        ],
        "settings": {
            "python.defaultInterpreterPath": python_path,
            "python.terminal.activateEnvironment": True,
            "python.terminal.activateEnvInCurrentTerminal": True,
            "files.exclude": {
                "**/__pycache__": True,
                "**/*.pyc": True,
                "**/venv": False
            },
            "python.analysis.typeCheckingMode": "basic",
            "python.analysis.autoImportCompletions": True
        },
        "extensions": {
            "recommendations": [
                "ms-python.python",
                "ms-python.black-formatter",
                "ms-python.pylint"
            ]
        }
    }
    
    try:
        with open("agents.code-workspace", "w", encoding="utf-8") as f:
            json.dump(workspace_config, f, indent=4)
        print("   ✅ Workspace 'agents.code-workspace' creado")
        return True
    except Exception as e:
        print(f"   ❌ Error creando workspace: {e}")
        return False

def open_vscode_workspace():
    """Abre VSCode con el workspace configurado"""
    print_step("Abriendo VSCode")
    
    try:
        subprocess.run("code agents.code-workspace", shell=True, check=True)
        print("   ✅ VSCode abierto con configuración correcta")
        return True
    except subprocess.CalledProcessError:
        print("   ❌ Error abriendo VSCode")
        print("   💡 Abre manualmente: code agents.code-workspace")
        return False

def create_activation_script():
    """Crea script para activar venv fácilmente"""
    print_step("Creando script de activación")
    
    if sys.platform == "win32":
        script_content = """@echo off
echo 🚀 Activando entorno virtual venv...
call venv\\Scripts\\activate.bat
echo ✅ Entorno virtual activado!
echo 💡 Para ejecutar la aplicación:
echo    python main.py                 (Dashboard Gradio)
echo    python server_widget.py        (Widget WordPress)
echo    python server_production.py    (Solo API)
cmd /k
"""
        script_name = "activate_venv.bat"
    else:
        script_content = """#!/bin/bash
echo "🚀 Activando entorno virtual venv..."
source venv/bin/activate
echo "✅ Entorno virtual activado!"
echo "💡 Para ejecutar la aplicación:"
echo "   python main.py                 (Dashboard Gradio)"
echo "   python server_widget.py        (Widget WordPress)"
echo "   python server_production.py    (Solo API)"
bash
"""
        script_name = "activate_venv.sh"
    
    try:
        with open(script_name, "w", encoding="utf-8") as f:
            f.write(script_content)
        
        if not sys.platform == "win32":
            os.chmod(script_name, 0o755)
        
        print(f"   ✅ Script '{script_name}' creado")
        print(f"   💡 Ejecuta: {script_name}")
        return True
    except Exception as e:
        print(f"   ❌ Error creando script: {e}")
        return False

def print_manual_steps():
    """Imprime pasos manuales si algo falla"""
    print_step("Pasos Manuales para VSCode")
    
    python_path = get_python_path()
    
    print("\n📋 Si VSCode no se configuró automáticamente:")
    print("   1. Abrir VSCode en el proyecto")
    print("   2. Presionar Ctrl + Shift + P")
    print("   3. Buscar: 'Python: Select Interpreter'")
    print(f"   4. Seleccionar: {python_path}")
    print("\n   O alternativamente:")
    print("   1. Abrir: agents.code-workspace")
    print("   2. VSCode debería detectar la configuración automáticamente")

def main():
    """Función principal"""
    print("🎯 CONFIGURADOR AUTOMÁTICO DE VSCODE")
    print("=" * 50)
    print("🔄 Configurando VSCode para usar venv...")
    
    # Verificar VSCode
    vscode_available = check_vscode_installed()
    
    # Crear workspace
    workspace_created = create_vscode_workspace()
    
    # Crear script de activación
    script_created = create_activation_script()
    
    if vscode_available and workspace_created:
        print_step("¡Configuración Completada! 🎉")
        print("\n✅ Todo configurado correctamente")
        print("\n🚀 OPCIONES PARA CONTINUAR:")
        print("   1. Ejecutar: code agents.code-workspace")
        print("   2. O abrir VSCode y cargar el workspace manualmente")
        print("   3. Para activar venv: activate_venv.bat (Windows)")
        
        # Intentar abrir VSCode
        print("\n🔄 Intentando abrir VSCode...")
        if open_vscode_workspace():
            print("\n🎯 VSCode abierto con configuración correcta!")
        else:
            print("\n💡 Abre manualmente VSCode con: code agents.code-workspace")
    else:
        print_step("Configuración Manual Requerida")
        print_manual_steps()
    
    print("\n📚 Documentación completa en README.md")
    print("🆘 Si tienes problemas, revisa la sección Troubleshooting")

if __name__ == "__main__":
    main()