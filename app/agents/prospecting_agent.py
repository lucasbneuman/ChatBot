# agents/app/agents/prospecting_agent.py
import json
import os
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage

from ..database.prospect_db_fixed import ProspectDatabaseFixed, Prospect, LeadStatus
from ..nodes.message_parser import MessageParser
from ..nodes.data_extractor import DataExtractor  
from ..nodes.response_generator import ResponseGenerator
from ..nodes.interest_detector import InterestDetector
from ..nodes.brevo_sync_node import BrevoSyncNode
from ..core.rag_system import CompanyRAGSystem

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
        self.should_offer_human_contact: bool = False
        self.brevo_synced: bool = False

class ProspectingAgent:
    def __init__(self, openai_api_key: str, db_path: str = "prospects.db"):
        self.llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4o-mini", temperature=0.3,max_tokens=150)
        self.db = ProspectDatabaseFixed(db_path)
        self.parser = MessageParser(self.llm)
        self.extractor = DataExtractor(self.db)
        
        # Inicializar sistema RAG
        self.rag_system = None
        try:
            self.rag_system = CompanyRAGSystem(openai_api_key)
        except Exception as e:
            print(f"RAG system no disponible: {e}")
        
        self.response_gen = ResponseGenerator(self.llm, self.rag_system)
        self.memory = MemorySaver()
        
        # Inicializar componentes de Brevo
        self.interest_detector = None
        self.brevo_sync = None
        
        try:
            self.interest_detector = InterestDetector()
            print("✅ InterestDetector inicializado correctamente")
        except Exception as e:
            print(f"❌ Error inicializando InterestDetector: {e}")
        
        try:
            self.brevo_sync = BrevoSyncNode()
            print("✅ BrevoSyncNode inicializado correctamente")
        except Exception as e:
            print(f"❌ Error inicializando BrevoSyncNode: {e}")
            import traceback
            print(f"📍 Traceback: {traceback.format_exc()}")
        
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
                    prospect_id = state["prospect_id"]
                    self.extractor.update_prospect_data(prospect_id, extracted_data)
                    
                    # Sincronización incremental si ya se envió el link y hay nuevos datos importantes
                    meeting_link_sent = state.get("meeting_link_sent", False)
                    if meeting_link_sent and self.brevo_sync and self._has_important_new_data(extracted_data):
                        try:
                            prospect = self.db.get_prospect(prospect_id)
                            if prospect and prospect.brevo_contact_id:
                                sync_result = self.brevo_sync.sync_prospect_on_meeting_scheduled(prospect_id)
                                if sync_result.get("success"):
                                    print(f"Sincronización incremental exitosa: {sync_result}")
                                else:
                                    print(f"Error en sincronización incremental: {sync_result}")
                        except Exception as e:
                            print(f"Error en sincronización incremental: {e}")
                    
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
                
                # Detectar nivel de interés antes de generar respuesta
                if self.interest_detector and not meeting_link_sent:
                    current_message = state.get("current_message", "")
                    interest_analysis = self.interest_detector.detect_interest_level(current_message, history)
                    state["should_offer_human_contact"] = interest_analysis.get("should_offer_human_contact", False)
                    
                    # Si se debe ofrecer contacto humano, generar mensaje personalizado
                    if state["should_offer_human_contact"]:
                        human_contact_message = self.interest_detector.generate_human_contact_offer(
                            prospect_data, interest_analysis
                        )
                        state["response"] = human_contact_message
                        
                        # Sincronizar con Brevo si está disponible
                        if self.brevo_sync:
                            try:
                                self.brevo_sync.sync_prospect_on_human_contact_offer(prospect_id)
                                state["brevo_synced"] = True
                            except Exception as e:
                                print(f"Error sincronizando con Brevo: {e}")
                    else:
                        # Generar respuesta normal
                        response = self.response_gen.generate_response(intent, prospect_data, history, missing_info)
                        state["response"] = response
                else:
                    # Generar respuesta normal
                    response = self.response_gen.generate_response(intent, prospect_data, history, missing_info)
                    state["response"] = response
                
                # Agregar respuesta al historial
                if hasattr(self.db, 'add_conversation_message') and prospect_id:
                    self.db.add_conversation_message(prospect_id, state["response"], "assistant")
                
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
                waiting_for_email = state.get("waiting_for_email", False)
                prospect_id = state.get("prospect_id")
                
                # Detectar si en este mensaje están dando un email después de haberlo pedido
                if not meeting_link_sent and prospect_id:
                    current_message = state.get("current_message", "")
                    prospect = self.db.get_prospect(prospect_id)
                    
                    # Si ya se calificó pero aún no se envió el link, y el mensaje contiene un email
                    if (qualification_complete and prospect and 
                        self.extractor.should_send_meeting_link(prospect) and 
                        self._contains_email(current_message)):
                        
                        # Guardar el email y enviar el link
                        self._save_email_from_message(current_message, prospect_id)
                        return "send_meeting_link"
                
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
                        return "request_email_before_meeting"
                
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
                prospect_data = self._prospect_to_dict(prospect) if prospect else None
                meeting_message = self.response_gen.generate_meeting_link_message(
                    prospect.name if prospect else None,
                    prospect_data
                )
                
                state["response"] = meeting_message
                
                if hasattr(self.db, 'add_conversation_message') and prospect_id:
                    self.db.add_conversation_message(prospect_id, meeting_message, "assistant")
                
                # Marcar que se envió el link
                if prospect:
                    prospect.meeting_link_sent = True
                    prospect.status = LeadStatus.MEETING_SENT.value
                    self.db.update_prospect(prospect)
                
                # Sincronizar con Brevo cuando se programa reunión
                if self.brevo_sync and prospect:
                    try:
                        sync_result = self.brevo_sync.sync_prospect_on_meeting_scheduled(prospect_id)
                        if sync_result.get("success"):
                            state["brevo_synced"] = True
                            print(f"Prospecto sincronizado con Brevo: {sync_result}")
                        else:
                            print(f"Error sincronizando con Brevo: {sync_result}")
                    except Exception as e:
                        print(f"Error en sincronización Brevo: {e}")
                
                state["meeting_link_sent"] = True
                
            except Exception as e:
                print(f"Error en send_meeting_link: {e}")
                state["response"] = "¡Excelente! Te enviaré la información para agendar una reunión."
                
            return state
        
        def request_email_before_meeting(state: Dict[str, Any]) -> Dict[str, Any]:
            """Nodo: Solicita email antes de enviar link de reunión"""
            try:
                prospect_id = state.get("prospect_id")
                prospect = self.db.get_prospect(prospect_id) if prospect_id else None
                
                # Crear mensaje solicitando email de manera amigable
                prospect_name = prospect.name if prospect else ""
                company = prospect.company if prospect else ""
                problems = self._extract_main_problems(prospect) if prospect else []
                
                # Mensaje personalizado solicitando email
                email_request = f"""Perfecto{' ' + prospect_name if prospect_name else ''}! 

Por todo lo que me contaste sobre {company if company else 'tu negocio'}{self._format_problems(problems)}, estoy convencido de que Lucas te va a poder ayudar mucho.

Para poder sincronizar tus datos y ayudarte mejor, ¿me pasas tu email de contacto? De esta manera nos aseguramos de tenerlo bien y Lucas va a poder preparar mejor la charla específicamente para vos."""

                state["response"] = email_request
                state["waiting_for_email"] = True
                
                # Guardar conversación
                if hasattr(self.db, 'add_conversation_message') and prospect_id:
                    self.db.add_conversation_message(prospect_id, email_request, "assistant")
                
                return state
            
            except Exception as e:
                print(f"Error en request_email_before_meeting: {e}")
                state["response"] = "¡Genial! ¿Me das tu email para coordinar mejor?"
                state["waiting_for_email"] = True
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
        workflow.add_node("request_email_before_meeting", request_email_before_meeting)
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
                "request_email_before_meeting": "request_email_before_meeting",
                "send_meeting_link": "send_meeting_link",
                "end_conversation": "end_conversation"
            }
        )
        
        # Conectar request_email de vuelta al flujo principal para esperar respuesta
        workflow.add_edge("request_email_before_meeting", END)
        
        # El link de reunión NO termina la conversación
        workflow.add_edge("send_meeting_link", END)
        workflow.add_edge("end_conversation", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def _extract_main_problems(self, prospect) -> list:
        """Extrae los principales problemas de las notas del prospecto"""
        if not prospect or not prospect.notes:
            return []
        
        problems = []
        notes = prospect.notes.lower()
        
        # Buscar indicadores de problemas comunes
        if "atención" in notes or "atencion" in notes:
            problems.append("atención al cliente")
        if "tiempo" in notes or "horas" in notes:
            problems.append("gestión del tiempo")
        if "automatizar" in notes or "automatización" in notes:
            problems.append("procesos manuales")
        if "clientes" in notes:
            problems.append("gestión de clientes")
        if "ventas" in notes:
            problems.append("proceso de ventas")
            
        return problems[:2]  # Máximo 2 problemas principales
    
    def _format_problems(self, problems: list) -> str:
        """Formatea los problemas para incluir en el mensaje"""
        if not problems:
            return ""
        
        if len(problems) == 1:
            return f" y especialmente con {problems[0]}"
        else:
            return f" y especialmente con {problems[0]} y {problems[1]}"
    
    def _contains_email(self, message: str) -> bool:
        """Detecta si un mensaje contiene un email válido"""
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return bool(re.search(email_pattern, message))
    
    def _save_email_from_message(self, message: str, prospect_id: int) -> bool:
        """Extrae y guarda el email de un mensaje en la columna específica"""
        if not prospect_id:
            return False
        
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, message)
        
        if emails:
            email = emails[0]  # Tomar el primer email encontrado
            prospect = self.db.get_prospect(prospect_id)
            if prospect:
                # Guardar el email en la columna específica (no en notas)
                prospect.email = email
                self.db.update_prospect(prospect)
                print(f"Email guardado en prospecto {prospect_id}: {email}")
                return True
        
        return False
    
    def _prospect_to_dict(self, prospect) -> dict:
        """Convierte el objeto prospect a diccionario"""
        if not prospect:
            return {}
        
        return {
            "id": prospect.id,
            "name": prospect.name,
            "company": prospect.company,
            "email": prospect.email,
            "budget": prospect.budget,
            "location": prospect.location,
            "industry": prospect.industry,
            "notes": prospect.notes,
            "status": prospect.status,
            "qualification_score": prospect.qualification_score,
            "meeting_date": prospect.meeting_date,
            "meeting_link_sent": prospect.meeting_link_sent,
            "brevo_contact_id": prospect.brevo_contact_id,
            "conversation_history": prospect.conversation_history,
            "created_at": prospect.created_at,
            "updated_at": prospect.updated_at
        }
    
    def _has_important_new_data(self, extracted_data: dict) -> bool:
        """Determina si los datos extraídos contienen información importante para sincronizar"""
        if not extracted_data:
            return False
        
        important_fields = ['budget', 'location', 'phone', 'urgency', 'decision_maker']
        
        for field in important_fields:
            if field in extracted_data and extracted_data[field]:
                return True
        
        # También sincronizar si hay nuevas notas sustanciales
        notes = extracted_data.get('notes', '')
        if notes and len(notes.strip()) > 20:
            return True
            
        return False
    
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

# Exportar el grafo para LangGraph dev
import os
if os.getenv("OPENAI_API_KEY"):
    agent = ProspectingAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
    graph = agent.graph
else:
    # Fallback si no hay API key
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    
    def dummy_node(state):
        return {"response": "API key no configurada"}
    
    workflow = StateGraph(dict)
    workflow.add_node("dummy", dummy_node)
    workflow.set_entry_point("dummy")
    workflow.add_edge("dummy", END)
    graph = workflow.compile(checkpointer=MemorySaver())