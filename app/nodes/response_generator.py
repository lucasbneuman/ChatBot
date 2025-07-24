# agents/app/nodes/response_generator.py - PROMPTS PARA PYMES
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from ..core.prompt_manager import get_prompt
from ..core.rag_system import CompanyRAGSystem

class ResponseGenerator:
    def __init__(self, llm: ChatOpenAI, rag_system: Optional[CompanyRAGSystem] = None):
        self.llm = llm
        self.rag_system = rag_system
    
    def generate_response(self, intent: str, prospect_data: Dict[str, Any], 
                         conversation_history: List[Dict], missing_info: List[str]) -> str:
        """Genera una respuesta basada en el contexto"""
        
        # Contar mensajes para ajustar el comportamiento
        message_count = len([msg for msg in conversation_history if msg['sender'] == 'user'])
        meeting_link_sent = prospect_data.get('meeting_link_sent', False)
        
        # Obtener el último mensaje del usuario
        last_user_message = ""
        for msg in reversed(conversation_history):
            if msg['sender'] == 'user':
                last_user_message = msg['message']
                break
        
        # Verificar si necesitamos usar RAG
        rag_context = ""
        if self.rag_system and self.rag_system.should_use_rag(last_user_message, intent):
            rag_context = self.rag_system.get_context_for_question(last_user_message)
        
        system_prompt = self._get_system_prompt(intent, prospect_data, missing_info, message_count, meeting_link_sent, rag_context)
        
        context = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in conversation_history[-5:]])
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Conversación reciente:\n{context}\n\nGenera la respuesta apropiada.")
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def _get_system_prompt(self, intent: str, prospect_data: Dict[str, Any], 
                          missing_info: List[str], message_count: int, meeting_link_sent: bool, 
                          rag_context: str = "") -> str:
        """Genera el prompt del sistema según el contexto"""
        
        if meeting_link_sent:
            return self._get_post_meeting_prompt(prospect_data)
        
        score = prospect_data.get('qualification_score', 0)
        
        if message_count <= 3:
            return self._get_initial_prompt(prospect_data, missing_info, score, rag_context)
        elif message_count <= 6:
            return self._get_exploration_prompt(intent, prospect_data, missing_info, score, rag_context)
        elif message_count <= 10:
            return self._get_deepening_prompt(intent, prospect_data, missing_info, score, rag_context)
        else:
            return self._get_advanced_prompt(intent, prospect_data, missing_info, score, rag_context)
    
    def _get_initial_prompt(self, prospect_data: Dict[str, Any], missing_info: List[str], score: int, rag_context: str = "") -> str:
        """Prompt para primeras conversaciones - LENGUAJE PYME"""
        return get_prompt('response_generator', 'initial_conversation',
                         prospect_data=prospect_data,
                         missing_info=missing_info,
                         score=score,
                         rag_context=rag_context)
    
    def _get_exploration_prompt(self, intent: str, prospect_data: Dict[str, Any], missing_info: List[str], score: int, rag_context: str = "") -> str:
        """Prompt para conocer mejor el negocio - LENGUAJE PYME"""
        return get_prompt('response_generator', 'exploration_conversation',
                         intent=intent,
                         prospect_data=prospect_data,
                         missing_info=missing_info,
                         score=score,
                         rag_context=rag_context)
    
    def _get_deepening_prompt(self, intent: str, prospect_data: Dict[str, Any], missing_info: List[str], score: int, rag_context: str = "") -> str:
        """Prompt para mostrar cómo la tecnología puede ayudar - LENGUAJE PYME"""
        return get_prompt('response_generator', 'deepening_conversation',
                         intent=intent,
                         prospect_data=prospect_data,
                         missing_info=missing_info,
                         score=score,
                         rag_context=rag_context)
    
    def _get_advanced_prompt(self, intent: str, prospect_data: Dict[str, Any], missing_info: List[str], score: int, rag_context: str = "") -> str:
        """Prompt para evaluar si ofrecer charla con Lucas - LENGUAJE PYME"""
        return get_prompt('response_generator', 'advanced_conversation',
                         intent=intent,
                         prospect_data=prospect_data,
                         missing_info=missing_info,
                         score=score,
                         rag_context=rag_context)
    
    def _get_post_meeting_prompt(self, prospect_data: Dict[str, Any]) -> str:
        """Prompt para después de agendar la charla - LENGUAJE PYME"""
        return get_prompt('response_generator', 'post_meeting_conversation',
                         prospect_data=prospect_data)
    
    def generate_qualification_summary(self, prospect_data: Dict[str, Any]) -> str:
        """Genera resumen de calificación - LENGUAJE SIMPLE"""
        score = prospect_data.get('qualification_score', 0)
        if isinstance(score, str):
            try:
                score = int(float(score))
            except:
                score = 0
        
        if score >= 85:
            return "🟢 Muy interesado - Agendar charla con Lucas YA"
        elif score >= 65:
            return "🟡 Buen candidato - Listo para charla con Lucas"
        elif score >= 50:
            return "🟠 Interés moderado - Necesita más información"
        elif score >= 30:
            return "🔴 Poco interés - Seguir cultivando relación"
        else:
            return "⚫ Sin interés - Considerar descarte"
    
    def generate_meeting_link_message(self, prospect_name: str = None, prospect_data: dict = None) -> str:
        """Mensaje personalizado y corto para agendar charla"""
        problems_summary = "tus desafíos"
        business_context = "tu negocio"
        
        if prospect_data:
            # Extraer problemas principales
            notes = prospect_data.get('notes', '').lower()
            problems = []
            
            if 'atención' in notes or 'atencion' in notes:
                problems.append('atención al cliente')
            if 'automatizar' in notes:
                problems.append('automatización')
            if 'tiempo' in notes:
                problems.append('optimización del tiempo')
            if 'ventas' in notes:
                problems.append('proceso de ventas')
            if 'clientes' in notes:
                problems.append('gestión de clientes')
                
            if problems:
                if len(problems) == 1:
                    problems_summary = problems[0]
                else:
                    problems_summary = f"{problems[0]} y {problems[1]}"
            
            # Contexto del negocio
            company = prospect_data.get('company', '')
            industry = prospect_data.get('industry', '')
            
            if company and industry:
                business_context = f"{company} ({industry})"
            elif company:
                business_context = company
            elif industry:
                business_context = f"tu {industry}"
        
        # Formatear nombre del prospecto
        prospect_name_text = f" {prospect_name}" if prospect_name else ""
        
        return get_prompt('response_generator', 'meeting_link_message',
                         prospect_name_text=prospect_name_text,
                         problems_summary=problems_summary,
                         business_context=business_context)
    
    def improve_notes_with_ai(self, prospect_notes: str) -> str:
        """Mejora las notas usando IA - NUEVA FUNCIÓN"""
        if not prospect_notes or len(prospect_notes) < 50:
            return prospect_notes
        
        system_prompt = get_prompt('response_generator', 'notes_improvement')
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Notas a mejorar:\n{prospect_notes}")
        ]
        
        try:
            response = self.llm.invoke(messages)
            improved_notes = response.content
            # Notas mejoradas por IA
            return improved_notes
        except Exception as e:
            # Error mejorando notas con IA
            return prospect_notes