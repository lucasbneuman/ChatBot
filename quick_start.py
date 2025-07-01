# Ejemplo de script de inicio rápido
# agents/quick_start.py
"""
Script de inicio rápido para probar el chatbot
"""

import os
from dotenv import load_dotenv
from app.agents.prospecting_agent import ProspectingAgent

def quick_test():
    """Prueba rápida del sistema"""
    load_dotenv()
    
    # Crear agente
    agent = ProspectingAgent(
        openai_api_key=os.getenv("OPENAI_API_KEY", "tu-api-key-aqui"),
        db_path="test_prospects.db"
    )
    
    print("🤖 Chatbot de Prospección - Prueba Rápida")
    print("=" * 50)
    
    # Simular conversación
    messages = [
        "Hola, me interesa conocer más sobre sus servicios",
        "Soy María González de TechStartup",
        "Somos una empresa de software con sede en Barcelona", 
        "Nuestro presupuesto anual para este tipo de soluciones es de unos 75,000 euros",
        "Trabajamos en el sector fintech"
    ]
    
    prospect_id = None
    
    for i, message in enumerate(messages, 1):
        print(f"\n👤 Usuario: {message}")
        
        result = agent.process_message(message, prospect_id)
        
        if not prospect_id:
            prospect_id = result["prospect_id"]
        
        print(f"🤖 Bot: {result['response']}")
        print(f"📊 Intención: {result.get('intent', 'N/A')}")
        
        # Mostrar resumen después del último mensaje
        if i == len(messages):
            print("\n" + "="*50)
            print("📋 RESUMEN FINAL")
            print("="*50)
            
            summary = agent.get_prospect_summary(prospect_id)
            prospect = summary["prospect"]
            
            print(f"Nombre: {prospect.get('name', 'N/A')}")
            print(f"Empresa: {prospect.get('company', 'N/A')}")
            print(f"Presupuesto: {prospect.get('budget', 'N/A')}")
            print(f"Ubicación: {prospect.get('location', 'N/A')}")
            print(f"Industria: {prospect.get('industry', 'N/A')}")
            print(f"Score: {prospect.get('qualification_score', 0)}/100")
            print(f"Estado: {prospect.get('status', 'nuevo')}")
            print(f"\n{summary.get('qualification_summary', '')}")

if __name__ == "__main__":
    quick_test()