# agents/app/nodes/response_generator.py
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

class ResponseGenerator:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    def generate_response(self, intent: str, prospect_data: Dict[str, Any], 
                         conversation_history: List[Dict], missing_info: List[str]) -> str:
        """Genera una respuesta basada en el contexto"""
        
        system_prompt = f"""
        Eres un asistente de ventas experto en prospección B2B. Tu objetivo es:
        1. Calificar leads de manera natural y conversacional
        2. Obtener información clave: nombre, empresa, presupuesto, ubicación, industria
        3. Identificar necesidades y puntos de dolor
        4. Mantener un tono profesional pero amigable
        
        Información del prospecto actual:
        - Nombre: {prospect_data.get('name', 'No proporcionado')}
        - Empresa: {prospect_data.get('company', 'No proporcionado')}
        - Presupuesto: {prospect_data.get('budget', 'No proporcionado')}
        - Ubicación: {prospect_data.get('location', 'No proporcionado')}
        - Industria: {prospect_data.get('industry', 'No proporcionado')}
        - Score de calificación: {prospect_data.get('qualification_score', 0)}/100
        
        Información faltante: {', '.join(missing_info) if missing_info else 'Ninguna'}
        
        Intención detectada: {intent}
        
        Genera una respuesta apropiada que:
        - Responda a la intención del usuario
        - Haga una pregunta relevante para obtener información faltante
        - Mantenga la conversación fluida y natural
        - No sea demasiado agresiva en las ventas
        """
        
        context = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in conversation_history[-5:]])
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Conversación reciente:\n{context}\n\nGenera la respuesta apropiada.")
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def generate_qualification_summary(self, prospect_data: Dict[str, Any]) -> str:
        """Genera un resumen de calificación"""
        score = prospect_data.get('qualification_score', 0)
        
        if score >= 80:
            return "🟢 Lead altamente calificado - Programar reunión inmediatamente"
        elif score >= 60:
            return "🟡 Lead calificado - Continuar nutrición y programar reunión"
        elif score >= 40:
            return "🟠 Lead parcialmente calificado - Requiere más información"
        else:
            return "🔴 Lead no calificado - Considerar descarte o nurturing a largo plazo"