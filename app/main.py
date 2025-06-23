#!/usr/bin/env python3
"""
Punto de entrada principal para la aplicación de chat
"""

from interface import ChatInterface

def main():
    """Función principal"""
    try:
        # Crear e iniciar la interfaz
        interface = ChatInterface()
        interface.launch(share=True, debug=False)
        
    except Exception as e:
        print(f"❌ Error al iniciar la aplicación: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())