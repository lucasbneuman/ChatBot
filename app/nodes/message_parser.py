# agents/app/nodes/message_parser.py
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

class MessageParser:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    def classify_intent(self, message: str, conversation_history: List[Dict]) -> str:
        """Clasifica la intención del mensaje"""
        
        system_prompt = """
        Eres un experto en clasificación de intenciones para prospección de ventas.
        Clasifica el mensaje del usuario en una de estas categorías:
        
        - GREETING: Saludos iniciales
        - INFORMATION: Proporciona información sobre su empresa o necesidades
        - INTEREST: Muestra interés en el producto/servicio
        - OBJECTION: Pone objeciones o dudas
        - REJECTION: Rechaza explícitamente
        - SCHEDULING: Quiere agendar una reunión
        - CLOSING: Finaliza la conversación
        
        Responde solo con la categoría en mayúsculas.
        """
        
        context = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in conversation_history[-5:]])
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Contexto:\n{context}\n\nMensaje actual: {message}")
        ]
        
        response = self.llm.invoke(messages)
        return response.content.strip().upper()
    
    def extract_entities(self, message: str) -> Dict[str, Any]:
        """Extrae entidades del mensaje"""
        
        system_prompt = """
        Extrae información de prospección del mensaje del usuario.
        Devuelve un JSON con las siguientes claves (usar null si no hay información):
        
        {
            "name": "nombre de la persona",
            "company": "nombre de la empresa", 
            "budget": "presupuesto mencionado",
            "location": "ubicación geográfica",
            "industry": "sector o industria",
            "timeline": "cronograma mencionado",
            "pain_points": ["problema1", "problema2"],
            "decision_maker": "si es tomador de decisiones (true/false/null)"
        }
        
        Responde solo con el JSON válido.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=message)
        ]
        
        response = self.llm.invoke(messages)
        try:
            import json
            return json.loads(response.content)
        except:
            return {}
