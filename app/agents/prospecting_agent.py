# agents/app/agents/prospecting_agent.py
import json
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage

from ..database.prospect_db import ProspectDatabase, Prospect, LeadStatus
from ..nodes.message_parser import MessageParser
from ..nodes.data_extractor import DataExtractor  
from ..nodes.response_generator import ResponseGenerator

class ProspectingState:
    def __init__(self):
        self.prospect_id: Optional[int] = None
        self.current_message: str = ""
        self.conversation_history: List[Dict[str, Any]] = []
        self.intent: str = ""
        self.extracted_data: Dict[str, Any] = {}
        self.response: str = ""
        self.should_end: bool = False
        self.qualification_complete: bool = False

class ProspectingAgent:
    def __init__(self, openai_api_key: str, db_path: str = "prospects.db"):
        self.llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4o", temperature=0.3)
        self.db = ProspectDatabase(db_path)
        self.parser = MessageParser(self.llm)
        self.extractor = DataExtractor(self.db)
        self.response_gen = ResponseGenerator(self.llm)
        self.memory = MemorySaver()
        
        # Crear el grafo de estados
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Crea el grafo de estados de LangGraph"""
        
        def receive_message(state: Dict[str, Any]) -> Dict[str, Any]:
            """Nodo: Recibe y procesa el mensaje inicial"""
            message = state.get("current_message", "")
            prospect_id = state.get("prospect_id")
            
            # Si no hay prospect_id, crear uno nuevo
            if not prospect_id:
                prospect = Prospect()
                prospect_id = self.db.create_prospect(prospect)
                state["prospect_id"] = prospect_id
            
            # Agregar mensaje al historial
            self.db.add_conversation_message(prospect_id, message, "user")
            
            # Obtener historial de conversación
            conversation_history = self.db.get_conversation_history(prospect_id)
            state["conversation_history"] = conversation_history
            
            return state
        
        def classify_intent(state: Dict[str, Any]) -> Dict[str, Any]:
            """Nodo: Clasifica la intención del mensaje"""
            message = state["current_message"]
            history = state["conversation_history"]
            
            intent = self.parser.classify_intent(message, history)
            state["intent"] = intent
            
            return state
        
        def extract_data(state: Dict[str, Any]) -> Dict[str, Any]:
            """Nodo: Extrae datos del mensaje"""
            message = state["current_message"]
            
            extracted_data = self.parser.extract_entities(message)
            state["extracted_data"] = extracted_data
            
            # Actualizar prospecto en base de datos
            if state["prospect_id"]:
                self.extractor.update_prospect_data(state["prospect_id"], extracted_data)
            
            return state
        
        def check_qualification(state: Dict[str, Any]) -> Dict[str, Any]:
            """Nodo: Verifica si el prospecto está calificado"""
            prospect_id = state["prospect_id"]
            prospect = self.db.get_prospect(prospect_id)
            
            if prospect:
                state["qualification_complete"] = self.extractor.is_qualified(prospect)
                
                # Actualizar estado del prospecto
                if state["qualification_complete"]:
                    prospect.status = LeadStatus.QUALIFIED.value
                    self.db.update_prospect(prospect)
            
            return state
        
        def generate_response(state: Dict[str, Any]) -> Dict[str, Any]:
            """Nodo: Genera la respuesta apropiada"""
            intent = state["intent"]
            prospect_id = state["prospect_id"]
            history = state["conversation_history"]
            
            # Obtener datos del prospecto
            prospect = self.db.get_prospect(prospect_id)
            prospect_data = prospect.to_dict() if prospect else {}
            
            # Identificar información faltante
            missing_info = []
            if not prospect_data.get('name'): missing_info.append('nombre')
            if not prospect_data.get('company'): missing_info.append('empresa')
            if not prospect_data.get('budget'): missing_info.append('presupuesto')
            if not prospect_data.get('location'): missing_info.append('ubicación')
            if not prospect_data.get('industry'): missing_info.append('industria')
            
            # Generar respuesta
            response = self.response_gen.generate_response(intent, prospect_data, history, missing_info)
            state["response"] = response
            
            # Agregar respuesta al historial
            self.db.add_conversation_message(prospect_id, response, "assistant")
            
            return state
        
        def decide_next_action(state: Dict[str, Any]) -> str:
            """Nodo de decisión: Determina la siguiente acción"""
            intent = state["intent"]
            qualification_complete = state.get("qualification_complete", False)
            
            if intent == "REJECTION" or intent == "CLOSING":
                return "end_conversation"
            elif qualification_complete:
                return "send_meeting_link"
            else:
                return "continue_conversation"
        
        def send_meeting_link(state: Dict[str, Any]) -> Dict[str, Any]:
            """Nodo: Envía link de reunión para leads calificados"""
            prospect_id = state["prospect_id"]
            
            # Aquí integrarías con Brevo para enviar el link
            meeting_message = """
            ¡Excelente! Basándome en nuestra conversación, creo que podemos ayudarte.
            
            Te voy a enviar un enlace para que puedas agendar una reunión con nuestro equipo:
            [LINK DE BREVO AQUÍ]
            
            ¿Hay algún horario que te convenga más?
            """
            
            state["response"] = meeting_message
            self.db.add_conversation_message(prospect_id, meeting_message, "assistant")
            
            return state
        
        def end_conversation(state: Dict[str, Any]) -> Dict[str, Any]:
            """Nodo: Finaliza la conversación"""
            prospect_id = state["prospect_id"]
            prospect = self.db.get_prospect(prospect_id)
            
            if prospect:
                prospect.status = LeadStatus.CLOSED.value
                self.db.update_prospect(prospect)
            
            state["should_end"] = True
            return state
        
        # Crear el grafo
        workflow = StateGraph(dict)
        
        # Agregar nodos
        workflow.add_node("receive_message", receive_message)
        workflow.add_node("classify_intent", classify_intent)
        workflow.add_node("extract_data", extract_data)
        workflow.add_node("check_qualification", check_qualification)
        workflow.add_node("generate_response", generate_response)
        workflow.add_node("send_meeting_link", send_meeting_link)
        workflow.add_node("end_conversation", end_conversation)
        
        # Definir flujo
        workflow.set_entry_point("receive_message")
        
        workflow.add_edge("receive_message", "classify_intent")
        workflow.add_edge("classify_intent", "extract_data")
        workflow.add_edge("extract_data", "check_qualification")
        workflow.add_edge("check_qualification", "generate_response")
        
        # Nodo condicional
        workflow.add_conditional_edges(
            "generate_response",
            decide_next_action,
            {
                "continue_conversation": END,
                "send_meeting_link": "send_meeting_link",
                "end_conversation": "end_conversation"
            }
        )
        
        workflow.add_edge("send_meeting_link", END)
        workflow.add_edge("end_conversation", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def process_message(self, message: str, prospect_id: Optional[int] = None) -> Dict[str, Any]:
        """Procesa un mensaje y devuelve la respuesta"""
        initial_state = {
            "current_message": message,
            "prospect_id": prospect_id,
            "conversation_history": [],
            "intent": "",
            "extracted_data": {},
            "response": "",
            "should_end": False,
            "qualification_complete": False
        }
        
        # Ejecutar el grafo
        config = {"configurable": {"thread_id": str(prospect_id or "new")}}
        result = self.graph.invoke(initial_state, config)
        
        return result
    
    def get_prospect_summary(self, prospect_id: int) -> Dict[str, Any]:
        """Obtiene un resumen del prospecto"""
        prospect = self.db.get_prospect(prospect_id)
        if not prospect:
            return {}
        
        conversation_history = self.db.get_conversation_history(prospect_id)
        qualification_summary = self.response_gen.generate_qualification_summary(prospect.to_dict())
        
        return {
            "prospect": prospect.to_dict(),
            "conversation_count": len(conversation_history),
            "qualification_summary": qualification_summary,
            "last_interaction": conversation_history[-1] if conversation_history else None
        }