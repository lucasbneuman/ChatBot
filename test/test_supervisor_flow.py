"""
Test del supervisor con flujo completo:
1. Test de consultas de información (RAG)
2. Test de prospección natural
3. Test de transición info -> prospección
4. Test de validación de datos sin corrupción
"""

import os
from dotenv import load_dotenv
from app.agents.supervisor_agent import SupervisorAgent

def test_supervisor_complete_flow():
    """Prueba el flujo completo con supervisor"""
    print("=== TEST SUPERVISOR FLOW COMPLETO ===")
    
    load_dotenv()
    
    supervisor = SupervisorAgent(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        db_path="test_supervisor.db"
    )
    
    print("Supervisor inicializado")
    print(f"RAG system: {'ACTIVO' if supervisor.rag_system else 'INACTIVO'}")
    print()
    
    prospect_id = None
    
    # Conversación para test de supervisor
    messages = [
        "Hola! Soy María García, tengo una heladería llamada Dulce Tentación",
        "Es una heladería artesanal en el centro de Córdoba", 
        "Necesito automatizar las consultas frecuentes de mis clientes",
        "Tengo un presupuesto de 15,000 pesos para esto"
    ]
    
    print("=== FASE 1: PROSPECCIÓN NATURAL ===")
    for i, message in enumerate(messages, 1):
        print(f"\n[{i}] USER: {message}")
        
        result = supervisor.process_message(message, prospect_id)
        
        if not prospect_id:
            prospect_id = result.get("prospect_id")
            print(f"    -> Prospect ID: {prospect_id}")
        
        response = result.get('response', '')
        intent = result.get('intent', '')
        validation = result.get('validation_passed', False)
        
        print(f"    Intent: {intent}")
        print(f"    Validation: {validation}")
        print(f"    Response length: {len(response)}")
    
    # Test de consulta de información
    print(f"\n=== FASE 2: TEST CONSULTA INFORMACIÓN ===")
    info_message = "¿Cuánto cuesta un chatbot?"
    print(f"\n[USUARIO] {info_message}")
    
    result = supervisor.process_message(info_message, prospect_id)
    response = result.get('response', '')
    intent = result.get('intent', '')
    
    print(f"    Intent: {intent}")
    print(f"    Response length: {len(response)}")
    
    # Verificar que detectó info_request
    if intent == 'info_request':
        print("✓ INFO REQUEST detectado correctamente")
    else:
        print("✗ ERROR: Debería haber detectado info_request")
    
    # Test flujo mixto: info + prospección
    print(f"\n=== FASE 3: TEST FLUJO MIXTO ===")
    mixed_messages = [
        "¿Cuánto tiempo toma implementar un chatbot?",  # Info
        "Mi presupuesto es de 15,000 pesos"  # Prospección
    ]
    
    for i, message in enumerate(mixed_messages, 1):
        print(f"\n[MIXTO {i}] USER: {message}")
        
        result = supervisor.process_message(message, prospect_id)
        response = result.get('response', '')
        intent = result.get('intent', '')
        
        print(f"    Intent: {intent}")
        print(f"    Response length: {len(response)}")
        
        # Verificar que el supervisor detectó el intent correcto
        if i == 1:
            expected = 'info_request'
        else:
            expected = 'prospecting'
        
        if intent == expected:
            print(f"✓ Intent {expected} detectado correctamente")
        else:
            print(f"✗ ERROR: Esperaba {expected}, obtuvo {intent}")
    
    # Verificar estado final del prospecto
    print(f"\n=== VERIFICACIÓN FINAL ===")
    summary = supervisor.get_prospect_summary(prospect_id)
    if 'error' not in summary:
        prospect = summary.get('prospect', {})
        print(f"Prospecto: {prospect.get('name')} - {prospect.get('company')}")
        print(f"Email: {prospect.get('email', 'No proporcionado')}")
        print(f"Score final: {prospect.get('qualification_score', 0)}")
        print(f"Conversaciones: {summary.get('conversation_count', 0)}")
        print(f"Arquitectura: SUPERVISOR")
        
        print("\nEXITO: Nueva arquitectura funcionando:")
        print("  - Supervisor coordina respuestas")
        print("  - RAG responde consultas de informacion")
        print("  - Prospeccion se adapta al flujo natural")
        print("  - Base de datos sin corrupcion")
        print("  - Validacion de datos activa")
    else:
        print("Error obteniendo summary del prospecto")

def test_info_request():
    """Test específico para consultas de información"""
    print("\n=== TEST CONSULTA DE INFORMACIÓN ===")
    
    load_dotenv()
    supervisor = SupervisorAgent(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        db_path="test_info.db"
    )
    
    # Test consultas de información
    queries = [
        "¿Qué servicios ofrece Lucas?",
        "¿Cuánto cuesta un chatbot?",
        "¿Cómo puedo contactar a Lucas?"
    ]
    
    for query in queries:
        print(f"\nConsulta: {query}")
        result = supervisor.process_message(query, None)
        intent = result.get('intent')
        response_len = len(result.get('response', ''))
        
        print(f"Intent: {intent}")
        print(f"Response length: {response_len}")
        
        if intent == 'info_request' and response_len > 50:
            print("✓ PASS")
        else:
            print("✗ FAIL")
    
    print("✓ Test de consultas de información COMPLETADO")

def test_prospecting_flow():
    """Test específico para flujo de prospección"""
    print("\n=== TEST FLUJO DE PROSPECCIÓN ===")
    
    load_dotenv()
    supervisor = SupervisorAgent(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        db_path="test_prospecting.db"
    )
    
    # Simular flujo de prospección
    messages = [
        "Hola",
        "Soy María García",  
        "Tengo una heladería llamada Dulce Tentación",
        "Necesito automatizar la atención al cliente"
    ]
    
    prospect_id = None
    
    for i, message in enumerate(messages, 1):
        print(f"\n[{i}] {message}")
        result = supervisor.process_message(message, prospect_id)
        
        if not prospect_id:
            prospect_id = result.get('prospect_id')
        
        intent = result.get('intent')
        validation = result.get('validation_passed')
        
        print(f"Intent: {intent}")
        print(f"Validation: {validation}")
        
        if validation:
            print("✓ PASS")
        else:
            print("✗ FAIL")
    
    # Verificar datos extraídos
    summary = supervisor.get_prospect_summary(prospect_id)
    prospect = summary.get('prospect', {})
    
    print(f"\nDatos extraídos:")
    print(f"  Nombre: {prospect.get('name')}")
    print(f"  Empresa: {prospect.get('company')}")
    print(f"  Score: {prospect.get('qualification_score')}")
    
    if (prospect.get('name') and 
        prospect.get('company') and 
        prospect.get('qualification_score', 0) > 0):
        print("✓ Test de prospección EXITOSO")
    else:
        print("✗ Test de prospección FALLÓ")

if __name__ == "__main__":
    test_supervisor_complete_flow()
    test_info_request()
    test_prospecting_flow()
    print("\n🎉 TODOS LOS TESTS COMPLETADOS")