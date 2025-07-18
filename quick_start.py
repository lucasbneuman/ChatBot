# agents/quick_start_improved.py
"""
Script de prueba mejorado para el chatbot de prospección
"""

import os
from dotenv import load_dotenv
from app.agents.prospecting_agent import ProspectingAgent

def test_improved_flow():
    """Prueba del flujo mejorado"""
    load_dotenv()
    
    # Crear agente
    agent = ProspectingAgent(
        openai_api_key=os.getenv("OPENAI_API_KEY", "tu-api-key-aqui"),
        db_path="test_prospects_improved.db"
    )
    
    print("🤖 Chatbot de Prospección - VERSIÓN MEJORADA")
    print("=" * 60)
    print("🎯 Probando: Captura flexible, menos insistencia, campo notas")
    print("=" * 60)
    
    # Simular conversación más realista
    conversation_scenarios = [
        {
            "name": "Escenario 1: Información Implícita",
            "messages": [
                "Hola, me interesa conocer más sobre sus servicios",
                "Trabajo en TechCorp",  # Solo empresa, sin "Mi empresa se llama"
                "Soy María",  # Solo nombre, sin "Me llamo"
                "Estamos en Barcelona desarrollando software fintech",
                "Nuestros principales desafíos son la escalabilidad y reducir costos operativos"
            ]
        },
        {
            "name": "Escenario 2: Lead Calificado + Post-Meeting",
            "messages": [
                "Hola, necesito una solución para mi empresa",
                "Soy Carlos de InnovaCorp, somos una startup fintech en Madrid",
                "Tenemos problemas con nuestros procesos de validación de clientes",
                "Somos decisores en tecnología y tenemos presupuesto asignado para Q2",
                "Me gustaría explorar opciones - continuemos después del link"
            ]
        }
    ]
    
    for scenario in conversation_scenarios:
        print(f"\n{'='*60}")
        print(f"🎭 {scenario['name']}")
        print('='*60)
        
        prospect_id = None
        
        for i, message in enumerate(scenario['messages'], 1):
            print(f"\n👤 Usuario: {message}")
            
            result = agent.process_message(message, prospect_id)
            
            if not prospect_id:
                prospect_id = result["prospect_id"]
            
            print(f"🤖 Bot: {result['response']}")
            print(f"📊 Intención: {result.get('intent', 'N/A')}")
            
            # Mostrar datos extraídos si hay
            if result.get('extracted_data'):
                extracted = result['extracted_data']
                if any(extracted.values()):
                    print(f"📋 Datos extraídos: {extracted}")
        
        # Mostrar resumen final
        print(f"\n{'='*50}")
        print("📋 RESUMEN FINAL")
        print('='*50)
        
        summary = agent.get_prospect_summary(prospect_id)
        prospect = summary["prospect"]
        
        print(f"ID: {prospect.get('id')}")
        print(f"Nombre: {prospect.get('name', 'N/A')}")
        print(f"Empresa: {prospect.get('company', 'N/A')}")
        print(f"Ubicación: {prospect.get('location', 'N/A')}")
        print(f"Industria: {prospect.get('industry', 'N/A')}")
        print(f"Score: {prospect.get('qualification_score', 0)}/100")
        print(f"Estado: {prospect.get('status', 'nuevo')}")
        print(f"Link enviado: {'Sí' if prospect.get('meeting_link_sent') else 'No'}")
        
        if prospect.get('notes'):
            print(f"\n📝 Notas:")
            print(prospect['notes'])
        
        print(f"\n{summary.get('qualification_summary', '')}")
        
        # Probar nota manual
        if i == len(scenario['messages']):
            print(f"\n🔧 Probando nota manual...")
            agent.add_manual_note(prospect_id, "Cliente muy interesado, prioridad alta")
            updated_summary = agent.get_prospect_summary(prospect_id)
            updated_prospect = updated_summary["prospect"]
            print(f"📝 Notas actualizadas:")
            print(updated_prospect.get('notes', 'Sin notas'))
        
        print(f"\n{'='*60}")
    
    print(f"\n✅ PRUEBAS COMPLETADAS")
    print("🔧 Mejoras implementadas:")
    print("  • Captura flexible de información")
    print("  • Comportamiento menos insistente")
    print("  • Campo de notas funcional")
    print("  • Link de Brevo correcto")
    print("  • Sin insistencia en presupuesto")
    print("  • Flujo post-reunión mejorado")

def test_edge_cases():
    """Prueba casos límite"""
    load_dotenv()
    
    agent = ProspectingAgent(
        openai_api_key=os.getenv("OPENAI_API_KEY", "tu-api-key-aqui"),
        db_path="test_edge_cases.db"
    )
    
    print(f"\n🧪 PROBANDO CASOS LÍMITE")
    print("=" * 40)
    
    edge_cases = [
        "TechCorp",  # Solo empresa
        "Soy Ana",   # Solo nombre
        "Trabajo en Barcelona en una fintech",  # Ubicación + industria
        "Tenemos problemas de escalabilidad",   # Pain point sin datos
        "No tengo presupuesto definido",        # Rechazo sutil de presupuesto
    ]
    
    prospect_id = None
    
    for message in edge_cases:
        print(f"\n👤 Test: {message}")
        result = agent.process_message(message, prospect_id)
        
        if not prospect_id:
            prospect_id = result["prospect_id"]
        
        # Solo mostrar datos extraídos
        extracted = result.get('extracted_data', {})
        relevant_data = {k: v for k, v in extracted.items() if v}
        if relevant_data:
            print(f"✅ Capturado: {relevant_data}")
        else:
            print("❌ No se capturó información")
    
    # Resumen final de caso límite
    summary = agent.get_prospect_summary(prospect_id)
    prospect = summary["prospect"]
    print(f"\n📊 RESULTADO FINAL:")
    print(f"Score: {prospect.get('qualification_score', 0)}/100")
    for field in ['name', 'company', 'location', 'industry']:
        value = prospect.get(field, 'N/A')
        status = "✅" if value != 'N/A' else "❌"
        print(f"{status} {field.title()}: {value}")

if __name__ == "__main__":
    test_improved_flow()
    test_edge_cases()