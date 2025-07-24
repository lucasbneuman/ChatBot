# agents/app/agents/unified_agent.py
"""
Agente Único Inteligente para Lucas Benites
Combina información + prospección en una sola conversación natural
"""

import os
import re
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from ..database.prospect_db_fixed import ProspectDatabaseFixed, Prospect, LeadStatus
from ..nodes.message_parser import MessageParser
from ..nodes.data_extractor import DataExtractor  
from ..nodes.response_generator import ResponseGenerator
from ..core.rag_system import CompanyRAGSystem
from ..core.prompt_manager import get_prompt


class UnifiedAgent:
    """
    Agente único que maneja información y prospección de forma inteligente.
    Detecta automáticamente la intención y responde apropiadamente.
    """
    
    def __init__(self, openai_api_key: str, db_path: str = "prospects_production.db"):
        self.llm = ChatOpenAI(
            api_key=openai_api_key, 
            model="gpt-4o-mini", 
            temperature=0.3,
            max_tokens=200
        )
        self.db = ProspectDatabaseFixed(db_path)
        self.parser = MessageParser(self.llm)
        self.extractor = DataExtractor(self.db)
        
        # Inicializar sistema RAG
        self.rag_system = None
        try:
            self.rag_system = CompanyRAGSystem(openai_api_key)
            print("RAG system inicializado correctamente")
        except Exception as e:
            print(f"RAG system no disponible: {e}")
        
        self.response_gen = ResponseGenerator(self.llm, self.rag_system)
        
        # Inicializar componentes de Brevo (opcional)
        self.brevo_sync = None
        try:
            from ..nodes.brevo_sync_node import BrevoSyncNode
            self.brevo_sync = BrevoSyncNode()
            print("BrevoSyncNode inicializado correctamente")
        except Exception as e:
            print(f"BrevoSyncNode no disponible: {e}")
    
    def process_message(self, message: str, prospect_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Procesa un mensaje de forma inteligente:
        1. Detecta intención (información vs prospección)
        2. Obtiene contexto RAG si es necesario
        3. Actualiza datos del prospecto
        4. Genera respuesta unificada
        5. Sincroniza con Brevo si corresponde
        """
        try:
            # 1. Obtener o crear prospecto
            if not prospect_id:
                prospect = Prospect()
                prospect_id = self.db.create_prospect(prospect)
            
            prospect = self.db.get_prospect(prospect_id)
            if not prospect:
                return self._error_response("Prospect not found")
            
            # 2. Guardar mensaje del usuario
            self._save_conversation_message(prospect_id, message, "user")
            
            # 3. Obtener historial de conversación
            conversation_history = self._get_conversation_history(prospect_id)
            
            # 4. Detectar intención del mensaje
            intent_analysis = self._analyze_intent(message, conversation_history, prospect)
            
            # 5. Obtener información RAG si es necesario
            rag_context = self._get_rag_context_if_needed(message, intent_analysis)
            
            # 6. Extraer y actualizar datos del prospecto
            extracted_data = self._extract_and_update_data(message, prospect_id, conversation_history)
            
            # 7. Generar respuesta inteligente
            response = self._generate_intelligent_response(
                message=message,
                intent_analysis=intent_analysis,
                prospect=prospect,
                conversation_history=conversation_history,
                rag_context=rag_context,
                extracted_data=extracted_data
            )
            
            # 8. Guardar respuesta del asistente
            self._save_conversation_message(prospect_id, response, "assistant")
            
            # 9. Verificar si enviar link de reunión
            should_send_link = self._should_send_meeting_link(prospect, message)
            print(f"Should send meeting link: {should_send_link}")
            
            if should_send_link and not prospect.meeting_link_sent:
                print(f"Enviando link de reunion...")
                meeting_response = self._send_meeting_link(prospect)
                if meeting_response:
                    response = meeting_response
                    self._save_conversation_message(prospect_id, response, "assistant")
                    print(f"Link de reunion enviado correctamente")
                else:
                    print(f"Error enviando link de reunion")
            elif prospect.meeting_link_sent:
                print(f"Link ya enviado anteriormente")
            else:
                print(f"Prospect no califica aun para link de reunion")
            
            # 10. Sincronizar con Brevo si corresponde
            self._sync_with_brevo_if_needed(prospect, intent_analysis, should_send_link)
            
            return {
                "prospect_id": prospect_id,
                "response": response,
                "intent": intent_analysis.get("primary_intent", "unknown"),
                "rag_used": bool(rag_context),
                "data_extracted": bool(extracted_data),
                "meeting_link_sent": should_send_link
            }
            
        except Exception as e:
            print(f"Error en process_message: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return self._error_response(str(e))
    
    def _analyze_intent(self, message: str, history: List[Dict], prospect: Prospect) -> Dict[str, Any]:
        """
        Analiza la intención del mensaje de forma inteligente.
        Detecta si es consulta informativa, prospección, o mixta.
        """
        message_lower = message.lower()
        
        # Patrones de consulta de información
        info_patterns = [
            'qué es', 'que es', 'cómo funciona', 'como funciona', 
            'cuánto cuesta', 'cuanto cuesta', 'precio', 'contacto', 
            'email', 'teléfono', 'telefono', 'whatsapp', 'dirección', 
            'direccion', 'horario', 'información', 'informacion', 
            'servicio', 'que hacen', 'que ofrece', 'lucas', 'empresa',
            'herramientas', 'metodología', 'metodologia', 'experiencia',
            'casos', 'ejemplos', 'referencias'
        ]
        
        # Patrones de prospección/conversación
        prospect_patterns = [
            'mi negocio', 'mi empresa', 'trabajo en', 'soy de', 
            'me dedico', 'tengo una', 'necesito', 'me gustaría',
            'problema', 'ayuda', 'consulta', 'asesoría'
        ]
        
        # Detectar patrones
        has_info_intent = any(pattern in message_lower for pattern in info_patterns)
        has_prospect_intent = any(pattern in message_lower for pattern in prospect_patterns)
        
        # Determinar intención principal
        if has_info_intent and not has_prospect_intent:
            primary_intent = "information"
            confidence = 0.9
        elif has_prospect_intent and not has_info_intent:
            primary_intent = "prospecting" 
            confidence = 0.9
        elif has_info_intent and has_prospect_intent:
            primary_intent = "mixed"
            confidence = 0.8
        else:
            # Basado en contexto de conversación
            if len(history) <= 2:
                primary_intent = "prospecting"  # Primeros mensajes
            else:
                primary_intent = "prospecting"  # Default
            confidence = 0.6
        
        return {
            "primary_intent": primary_intent,
            "confidence": confidence,
            "has_info_intent": has_info_intent,
            "has_prospect_intent": has_prospect_intent,
            "message_number": len(history) + 1
        }
    
    def _get_rag_context_if_needed(self, message: str, intent_analysis: Dict) -> Optional[str]:
        """
        Obtiene contexto RAG solo si es necesario para responder la pregunta.
        """
        if not self.rag_system:
            return None
        
        # Solo usar RAG para consultas informativas o mixtas
        if intent_analysis["primary_intent"] in ["information", "mixed"]:
            try:
                context = self.rag_system.get_context_for_question(message)
                return context if context else None
            except Exception as e:
                print(f"Error obteniendo contexto RAG: {e}")
                return None
        
        return None
    
    def _extract_and_update_data(self, message: str, prospect_id: int, history: List[Dict]) -> Dict[str, Any]:
        """
        Extrae datos del mensaje y actualiza el prospecto.
        """
        try:
            # Crear contexto para mejor extracción
            context = "\\n".join([f"{msg['sender']}: {msg['message']}" for msg in history[-3:]])
            
            # Extraer datos usando el parser existente
            extracted_data = self.parser.extract_entities(message, context)
            
            # Actualizar prospecto si hay datos
            if extracted_data:
                self.extractor.update_prospect_data(prospect_id, extracted_data)
            
            return extracted_data or {}
            
        except Exception as e:
            print(f"Error extrayendo datos: {e}")
            return {}
    
    def _generate_intelligent_response(self, message: str, intent_analysis: Dict, 
                                     prospect: Prospect, conversation_history: List[Dict],
                                     rag_context: Optional[str], extracted_data: Dict) -> str:
        """
        Genera una respuesta inteligente basada en la intención detectada.
        """
        try:
            # Preparar contexto
            prospect_data = prospect.to_dict() if prospect else {}
            message_count = len(conversation_history)
            
            # Crear prompt dinámico basado en intención
            system_prompt = self._build_dynamic_system_prompt(
                intent_analysis, rag_context, message_count, prospect_data
            )
            
            # Crear contexto de conversación
            conversation_context = self._build_conversation_context(conversation_history)
            
            # Generar respuesta
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Contexto de conversación:\\n{conversation_context}\\n\\nMensaje del usuario: {message}")
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            print(f"Error generando respuesta: {e}")
            return "Disculpa, tuve un problema técnico. ¿Podrías repetir tu mensaje?"
    
    def _build_dynamic_system_prompt(self, intent_analysis: Dict, rag_context: Optional[str], 
                                   message_count: int, prospect_data: Dict) -> str:
        """
        Construye un prompt dinámico basado en la intención detectada.
        """
        base_prompt = f"""Eres un asistente virtual inteligente que trabaja PARA Lucas Benites, especialista en tecnología para PyMEs.

⚠️ IDENTIDAD CRÍTICA:
- TÚ ERES EL ASISTENTE DE LUCAS BENITES, NO LUCAS MISMO
- NUNCA te identifiques como "Lucas" o "Lucas Benites" 
- SIEMPRE di "Soy el asistente de Lucas" o "Trabajo con Lucas Benites"
- Refiere a Lucas en TERCERA PERSONA: "Lucas ayuda a...", "Lucas se especializa en..."

INTENCIÓN DETECTADA: {intent_analysis['primary_intent']} (confianza: {intent_analysis['confidence']:.1f})
MENSAJE NÚMERO: {message_count}"""

        # Agregar información RAG si está disponible
        if rag_context:
            base_prompt += f"""

📚 INFORMACIÓN DE LA EMPRESA (para consultas informativas):
{rag_context}

IMPORTANTE: Usa esta información SOLO para responder preguntas específicas sobre Lucas o su empresa."""

        # Ajustar comportamiento según intención
        if intent_analysis['primary_intent'] == 'information':
            base_prompt += """

🎯 MODO: CONSULTA INFORMATIVA
- Responde la pregunta específica usando la información disponible
- Sé conciso pero completo
- Si no tienes la información exacta, da la más cercana disponible
- Mantén un tono profesional y amigable
- NO hagas prospección activa, solo responde lo que preguntan"""

        elif intent_analysis['primary_intent'] == 'prospecting':
            base_prompt += f"""

🎯 MODO: PROSPECCIÓN NATURAL
- Mantén una conversación natural sobre su negocio
- Haz preguntas relevantes para entender sus necesidades
- {"Sigue construyendo rapport" if message_count <= 3 else "Profundiza en sus problemas específicos"}
- Recopila información gradualmente sin ser invasivo
- NO menciones reuniones hasta que califique bien"""

        elif intent_analysis['primary_intent'] == 'mixed':
            base_prompt += """

🎯 MODO: INFORMACIÓN + PROSPECCIÓN
- Primero responde su consulta informativa
- Luego, de forma natural, conecta con su situación de negocio
- Combina información útil con conversación sobre sus necesidades
- Mantén el flujo natural sin forzar la prospección"""

        # Agregar información de contacto siempre disponible
        base_prompt += """

📞 INFORMACIÓN DE CONTACTO DE LUCAS (si preguntan):
- Email: lucas@lucasbenites.com
- WhatsApp: +54 3517554495
- Teléfono: +54 3517554495
- Calendario: https://meet.brevo.com/lucas-benites
- LinkedIn: /in/lucas-benites
- Sitio web: www.lucasbenites.com

REGLAS IMPORTANTES:
- NO inventes información que no tengas
- Usa un lenguaje simple y cercano
- Una pregunta a la vez, no abrumes
- Mantén la conversación enfocada y natural"""

        return base_prompt
    
    def _build_conversation_context(self, history: List[Dict]) -> str:
        """
        Construye contexto de conversación para el LLM.
        """
        if not history:
            return "Inicio de conversación"
        
        # Tomar los últimos 4 mensajes para contexto
        recent_history = history[-4:] if len(history) > 4 else history
        context_lines = []
        
        for msg in recent_history:
            role = "Usuario" if msg['sender'] == 'user' else "Asistente"
            context_lines.append(f"{role}: {msg['message']}")
        
        return "\\n".join(context_lines)
    
    def _should_send_meeting_link(self, prospect: Prospect, message: str) -> bool:
        """
        Determina si enviar el link de reunión basado en calificación.
        """
        if prospect.meeting_link_sent:
            return False
        
        # Verificar score de calificación
        if prospect.qualification_score < 65:
            print(f"Score insuficiente: {prospect.qualification_score} < 65")
            return False
        
        # Verificar datos mínimos (name + company son suficientes)
        if not (prospect.name and prospect.company):
            print(f"Meeting link no enviado - faltan datos: name={bool(prospect.name)}, company={bool(prospect.company)}")
            return False
        
        print(f"Prospect calificado: score={prospect.qualification_score}, name={prospect.name}, company={prospect.company}")
        
        # Verificar si el usuario está pidiendo explícitamente agendar
        message_lower = message.lower()
        meeting_requests = [
            'agendar', 'reunión', 'reunion', 'charla', 'conversar', 
            'hablar con lucas', 'contactar', 'citas', 'programar'
        ]
        
        is_requesting_meeting = any(word in message_lower for word in meeting_requests)
        
        # Verificar si el mensaje contiene email
        has_email = self._contains_email(message)
        if has_email:
            self._extract_and_save_email(message, prospect.id)
            print(f"Email detectado y guardado")
            return True
        
        # Verificar si ya tiene email guardado
        if prospect.email:
            print(f"Prospect ya tiene email: {prospect.email}")
            return True
        
        # Si está pidiendo explícitamente reunión, solicitar email
        if is_requesting_meeting:
            print(f"Solicitando reunion explicitamente - necesita email")
            return True  # Enviará mensaje pidiendo email
        
        print(f"No se cumplen condiciones para enviar link")
        return False
    
    def _contains_email(self, message: str) -> bool:
        """Detecta si un mensaje contiene un email válido"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return bool(re.search(email_pattern, message))
    
    def _extract_and_save_email(self, message: str, prospect_id: int) -> bool:
        """Extrae y guarda email del mensaje"""
        try:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, message)
            
            if emails:
                email = emails[0]
                prospect = self.db.get_prospect(prospect_id)
                if prospect:
                    prospect.email = email
                    self.db.update_prospect(prospect)
                    print(f"Email guardado: {email}")
                    return True
            return False
        except Exception as e:
            print(f"Error guardando email: {e}")
            return False
    
    def _send_meeting_link(self, prospect: Prospect) -> Optional[str]:
        """
        Genera y envía el mensaje con link de reunión o solicita email.
        """
        try:
            # Si no tiene email, solicitar primero
            if not prospect.email:
                email_request = f"""¡Perfecto {prospect.name}! 

Por todo lo que me contaste sobre {prospect.company}, estoy convencido de que Lucas te va a poder ayudar mucho.

Para poder coordinar la reunión y que Lucas esté bien preparado, ¿me pasas tu email de contacto?"""
                
                print(f"Solicitando email a {prospect.name}")
                return email_request
            
            # Si tiene email, enviar link directamente
            prospect_data = prospect.to_dict()
            meeting_message = self.response_gen.generate_meeting_link_message(
                prospect.name, prospect_data
            )
            
            # Marcar como enviado
            prospect.meeting_link_sent = True
            prospect.status = LeadStatus.MEETING_SENT.value
            self.db.update_prospect(prospect)
            
            print(f"Link de reunion enviado a {prospect.name}")
            return meeting_message
            
        except Exception as e:
            print(f"Error enviando link de reunion: {e}")
            return None
    
    def _sync_with_brevo_if_needed(self, prospect: Prospect, intent_analysis: Dict, meeting_sent: bool):
        """
        Sincroniza con Brevo cuando es apropiado.
        """
        if not self.brevo_sync:
            return
        
        try:
            # Sincronizar cuando se envía link de reunión
            if meeting_sent and not prospect.brevo_contact_id:
                sync_result = self.brevo_sync.sync_prospect_on_meeting_scheduled(prospect.id)
                if sync_result.get("success"):
                    print(f"Sincronizado con Brevo: {sync_result}")
                else:
                    print(f"Error sincronizando con Brevo: {sync_result}")
                    
        except Exception as e:
            print(f"Error en sincronizacion Brevo: {e}")
    
    def _save_conversation_message(self, prospect_id: int, message: str, sender: str):
        """Guarda mensaje en el historial de conversación"""
        try:
            if hasattr(self.db, 'add_conversation_message'):
                self.db.add_conversation_message(prospect_id, message, sender)
        except Exception as e:
            print(f"Error guardando mensaje: {e}")
    
    def _get_conversation_history(self, prospect_id: int) -> List[Dict]:
        """Obtiene historial de conversación"""
        try:
            if hasattr(self.db, 'get_conversation_history'):
                return self.db.get_conversation_history(prospect_id)
            return []
        except Exception as e:
            print(f"Error obteniendo historial: {e}")
            return []
    
    def _error_response(self, error_msg: str) -> Dict[str, Any]:
        """Respuesta de error estándar"""
        return {
            "prospect_id": None,
            "response": "Disculpa, tuve un problema técnico. ¿Podrías repetir tu mensaje?",
            "intent": "error",
            "error": error_msg
        }
    
    def get_prospect_summary(self, prospect_id: int) -> Dict[str, Any]:
        """
        Obtiene resumen del prospecto - compatible con interfaz existente.
        """
        try:
            prospect = self.db.get_prospect(prospect_id)
            if not prospect:
                return {"error": "Prospect not found"}
            
            # Obtener historial de conversación
            conversation_history = self._get_conversation_history(prospect_id)
            
            return {
                "prospect": prospect.to_dict(),
                "conversation_count": len(conversation_history),
                "last_interaction": conversation_history[-1] if conversation_history else None
            }
            
        except Exception as e:
            print(f"Error en get_prospect_summary: {e}")
            return {"error": str(e)}