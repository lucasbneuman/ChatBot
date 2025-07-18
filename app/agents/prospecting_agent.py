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
        self.meeting_link_sent: bool = False

class ProspectingAgent:
    def __init__(self, openai_api_key: str, db_path: str = "prospects.db"):
        self.llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4o-mini", temperature=0.3,max_tokens=150)
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
            try:
                message = state.get("current_message", "")
                prospect_id = state.get("prospect_id")
                
                # Si no hay prospect_id, crear uno nuevo
                if not prospect_id:
                    prospect = Prospect()
                    prospect_id = self.db.create_prospect(prospect)
                    state["prospect_id"] = prospect_id
                
                # Verificar que las funciones de DB existen antes de usarlas
                if hasattr(self.db, 'add_conversation_message'):
                    self.db.add_conversation_message(prospect_id, message, "user")
                
                # Obtener historial de conversación
                if hasattr(self.db, 'get_conversation_history'):
                    conversation_history = self.db.get_conversation_history(prospect_id)
                else:
                    conversation_history = []
                
                state["conversation_history"] = conversation_history
                
                # Verificar si ya se envió el link
                prospect = self.db.get_prospect(prospect_id)
                if prospect and hasattr(prospect, 'meeting_link_sent'):
                    state["meeting_link_sent"] = prospect.meeting_link_sent or False
                else:
                    state["meeting_link_sent"] = False
                
                return state
                
            except Exception as e:
                print(f"Error en receive_message: {e}")
                state["conversation_history"] = []
                state["meeting_link_sent"] = False
                return state
        
        def classify_intent(state: Dict[str, Any]) -> Dict[str, Any]:
            """Nodo: Clasifica la intención del mensaje"""
            try:
                message = state["current_message"]
                history = state.get("conversation_history", [])
                
                intent = self.parser.classify_intent(message, history)
                state["intent"] = intent
                
            except Exception as e:
                print(f"Error en classify_intent: {e}")
                state["intent"] = "GREETING"  # Default fallback
                
            return state
        
        def extract_data(state: Dict[str, Any]) -> Dict[str, Any]:
            """Nodo: Extrae datos del mensaje"""
            try:
                message = state["current_message"]
                history = state.get("conversation_history", [])
                
                # Crear contexto de conversación para mejor extracción
                context = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in history[-3:]])
                
                extracted_data = self.parser.extract_entities(message, context)
                state["extracted_data"] = extracted_data
                
                # Actualizar prospecto en base de datos
                if state.get("prospect_id"):
                    self.extractor.update_prospect_data(state["prospect_id"], extracted_data)
                    
            except Exception as e:
                print(f"Error en extract_data: {e}")
                state["extracted_data"] = {}
            
            return state
        
        def check_qualification(state: Dict[str, Any]) -> Dict[str, Any]:
            """Nodo: Verifica si el prospecto está calificado"""
            try:
                prospect_id = state.get("prospect_id")
                prospect = self.db.get_prospect(prospect_id) if prospect_id else None
                
                if prospect:
                    state["qualification_complete"] = self.extractor.is_qualified(prospect)
                    
                    # Actualizar estado del prospecto
                    if state["qualification_complete"] and not getattr(prospect, 'meeting_link_sent', False):
                        prospect.status = LeadStatus.QUALIFIED.value
                        self.db.update_prospect(prospect)
                else:
                    state["qualification_complete"] = False
                    
            except Exception as e:
                print(f"Error en check_qualification: {e}")
                state["qualification_complete"] = False
            
            return state
        
        def generate_response(state: Dict[str, Any]) -> Dict[str, Any]:
            """Nodo: Genera la respuesta apropiada"""
            try:
                intent = state.get("intent", "GREETING")
                prospect_id = state.get("prospect_id")
                history = state.get("conversation_history", [])
                meeting_link_sent = state.get("meeting_link_sent", False)
                
                # Obtener datos del prospecto
                prospect = self.db.get_prospect(prospect_id) if prospect_id else None
                prospect_data = prospect.to_dict() if prospect else {}
                
                # Identificar información faltante (solo si no se envió el link)
                missing_info = []
                if not meeting_link_sent:
                    if not prospect_data.get('name'): missing_info.append('nombre')
                    if not prospect_data.get('company'): missing_info.append('empresa')
                    if not prospect_data.get('location'): missing_info.append('ubicación')
                    if not prospect_data.get('industry'): missing_info.append('industria')
                
                # Generar respuesta
                response = self.response_gen.generate_response(intent, prospect_data, history, missing_info)
                state["response"] = response
                
                # Agregar respuesta al historial
                if hasattr(self.db, 'add_conversation_message') and prospect_id:
                    self.db.add_conversation_message(prospect_id, response, "assistant")
                
            except Exception as e:
                print(f"Error en generate_response: {e}")
                state["response"] = "¡Hola! ¿Cómo estás? ¿En qué puedo ayudarte hoy?"
            
            return state
        
        def decide_next_action(state: Dict[str, Any]) -> str:
            """Nodo de decisión: Determina la siguiente acción"""
            try:
                intent = state.get("intent", "GREETING")
                qualification_complete = state.get("qualification_complete", False)
                meeting_link_sent = state.get("meeting_link_sent", False)
                prospect_id = state.get("prospect_id")
                
                # Si ya se envió el link, continuar conversación
                if meeting_link_sent:
                    if intent == "REJECTION" or intent == "CLOSING":
                        return "end_conversation"
                    else:
                        return "continue_conversation"
                
                # Si no se ha enviado el link pero está calificado
                if qualification_complete and not meeting_link_sent and prospect_id:
                    prospect = self.db.get_prospect(prospect_id)
                    if prospect and self.extractor.should_send_meeting_link(prospect):
                        return "send_meeting_link"
                
                # Casos de finalización
                if intent == "REJECTION" or intent == "CLOSING":
                    return "end_conversation"
                
                # Continuar conversación normal
                return "continue_conversation"
                
            except Exception as e:
                print(f"Error en decide_next_action: {e}")
                return "continue_conversation"
        
        def send_meeting_link(state: Dict[str, Any]) -> Dict[str, Any]:
            """Nodo: Envía link de reunión para leads calificados"""
            try:
                prospect_id = state.get("prospect_id")
                prospect = self.db.get_prospect(prospect_id) if prospect_id else None
                
                # Generar mensaje personalizado con link de Brevo
                meeting_message = self.response_gen.generate_meeting_link_message(
                    prospect.name if prospect else None
                )
                
                state["response"] = meeting_message
                
                if hasattr(self.db, 'add_conversation_message') and prospect_id:
                    self.db.add_conversation_message(prospect_id, meeting_message, "assistant")
                
                # Marcar que se envió el link
                if prospect:
                    prospect.meeting_link_sent = True
                    prospect.status = LeadStatus.MEETING_SENT.value
                    self.db.update_prospect(prospect)
                
                state["meeting_link_sent"] = True
                
            except Exception as e:
                print(f"Error en send_meeting_link: {e}")
                state["response"] = "¡Excelente! Te enviaré la información para agendar una reunión."
                
            return state
        
        def end_conversation(state: Dict[str, Any]) -> Dict[str, Any]:
            """Nodo: Finaliza la conversación"""
            try:
                prospect_id = state.get("prospect_id")
                prospect = self.db.get_prospect(prospect_id) if prospect_id else None
                
                if prospect:
                    prospect.status = LeadStatus.CLOSED.value
                    self.db.update_prospect(prospect)
                
                state["should_end"] = True
                
            except Exception as e:
                print(f"Error en end_conversation: {e}")
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
        
        # Nodo condicional mejorado
        workflow.add_conditional_edges(
            "generate_response",
            decide_next_action,
            {
                "continue_conversation": END,
                "send_meeting_link": "send_meeting_link",
                "end_conversation": "end_conversation"
            }
        )
        
        # El link de reunión NO termina la conversación
        workflow.add_edge("send_meeting_link", END)
        workflow.add_edge("end_conversation", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def process_message(self, message: str, prospect_id: Optional[int] = None) -> Dict[str, Any]:
        """Procesa un mensaje y devuelve la respuesta"""
        try:
            initial_state = {
                "current_message": message,
                "prospect_id": prospect_id,
                "conversation_history": [],
                "intent": "",
                "extracted_data": {},
                "response": "",
                "should_end": False,
                "qualification_complete": False,
                "meeting_link_sent": False
            }
            
            # Ejecutar el grafo
            config = {"configurable": {"thread_id": str(prospect_id or "new")}}
            result = self.graph.invoke(initial_state, config)
            
            return result
            
        except Exception as e:
            print(f"Error en process_message: {e}")
            # Fallback response
            return {
                "current_message": message,
                "prospect_id": prospect_id,
                "response": "¡Hola! Disculpa, tuve un pequeño problema técnico. ¿Podrías repetir tu mensaje?",
                "intent": "ERROR",
                "should_end": False
            }
    
    def get_prospect_summary(self, prospect_id: int) -> Dict[str, Any]:
        """Obtiene un resumen del prospecto - VERSIÓN CORREGIDA"""
        try:
            print(f"🔍 DEBUG - Buscando prospect_id: {prospect_id}")
            
            prospect = self.db.get_prospect(prospect_id)
            if not prospect:
                print(f"❌ DEBUG - No se encontró prospect con ID: {prospect_id}")
                return {"error": "Prospect not found"}
            
            print(f"✅ DEBUG - Prospect encontrado: {prospect.name}, {prospect.company}")
            print(f"📊 DEBUG - Score raw del DB: {prospect.qualification_score} (tipo: {type(prospect.qualification_score)})")
            
            # Obtener historial de conversación si la función existe
            conversation_history = []
            try:
                if hasattr(self.db, 'get_conversation_history'):
                    conversation_history = self.db.get_conversation_history(prospect_id)
                    print(f"📚 DEBUG - Conversaciones encontradas: {len(conversation_history)}")
                else:
                    print("⚠️ DEBUG - get_conversation_history no disponible")
            except Exception as e:
                print(f"⚠️ DEBUG - Error obteniendo conversaciones: {e}")
                conversation_history = []
            
            # Arreglar el score antes de procesar
            score = prospect.qualification_score
            if score is None:
                score = 0
            elif isinstance(score, str):
                try:
                    score = int(float(score))
                except:
                    score = 0
            else:
                score = int(score)
            
            # Actualizar el prospect con el score corregido
            prospect.qualification_score = score
            
            # Generar resumen de calificación
            try:
                if score >= 80:
                    qualification_summary = "🟢 Lead altamente calificado - Programar reunión inmediatamente"
                elif score >= 60:
                    qualification_summary = "🟡 Lead calificado - Continuar nutrición y programar reunión"
                elif score >= 40:
                    qualification_summary = "🟠 Lead parcialmente calificado - Requiere más información"
                else:
                    qualification_summary = "🔴 Lead no calificado - Considerar descarte o nurturing a largo plazo"
            except Exception as e:
                print(f"⚠️ DEBUG - Error generando qualification_summary: {e}")
                qualification_summary = "❓ Error al calcular calificación"
            
            # Construir resultado
            result = {
                "prospect": prospect.to_dict(),
                "conversation_count": len(conversation_history),
                "qualification_summary": qualification_summary,
                "last_interaction": conversation_history[-1] if conversation_history else None
            }
            
            print(f"📊 DEBUG - Summary generado correctamente para {prospect.name} con score {score}")
            return result
            
        except Exception as e:
            print(f"❌ ERROR en get_prospect_summary: {e}")
            import traceback
            print(f"📍 Traceback: {traceback.format_exc()}")
            return {"error": str(e)}