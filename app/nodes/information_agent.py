# agents/app/nodes/information_agent.py
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from ..core.rag_system import CompanyRAGSystem

class InformationAgent:
    def __init__(self, llm: ChatOpenAI, rag_system: Optional[CompanyRAGSystem] = None):
        self.llm = llm
        self.rag_system = rag_system
        
    def get_information(self, message: str, conversation_history: List[Dict], prospect_data: Dict[str, Any]) -> str:
        """Obtiene información específica usando RAG"""
        try:
            # Primero intentar obtener información del RAG
            rag_info = ""
            if self.rag_system:
                try:
                    rag_info = self.rag_system.get_context_for_question(message)
                except Exception as e:
                    print(f"Error obteniendo info del RAG: {e}")
            
            # Si no hay información del RAG, usar información básica predeterminada
            if not rag_info:
                rag_info = self._get_basic_company_info(message)
            
            # Generar respuesta usando LLM con la información obtenida
            system_prompt = self._get_info_system_prompt(rag_info)
            
            # Contexto de conversación
            context = ""
            if conversation_history:
                recent_history = conversation_history[-3:]  # Últimos 3 mensajes
                context = "\\n".join([f"{msg['sender']}: {msg['message']}" for msg in recent_history])
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Contexto de conversación:\\n{context}\\n\\nPregunta del usuario: {message}")
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            print(f"Error en get_information: {e}")
            return self._get_fallback_response(message)
    
    def _get_info_system_prompt(self, rag_info: str) -> str:
        """Genera el prompt del sistema para respuestas informativas"""
        return f"""Eres un asistente virtual amigable que trabaja PARA Lucas Benites. Lucas es especialista en tecnología para PyMEs.

⚠️ IDENTIDAD CRÍTICA:
- TÚ ERES EL ASISTENTE DE LUCAS BENITES
- NUNCA te identifiques como Lucas Benites mismo
- NUNCA digas "Soy Lucas" o "Soy Lucas Benites"
- SIEMPRE di "Soy el asistente de Lucas" o "Trabajo con Lucas Benites"
- Cuando hablen sobre Lucas, refiere a él en TERCERA PERSONA: "Lucas ayuda a...", "Lucas se especializa en..."

INFORMACIÓN DISPONIBLE DE LA EMPRESA:
{rag_info}

TU TRABAJO:
- Responder preguntas específicas usando la información disponible  
- Ser conciso pero completo en tus respuestas
- Mantener un tono amigable y profesional
- Referir SIEMPRE a Lucas en tercera persona, nunca como si fueras él

REGLAS IMPORTANTES:
- NO inventes información que no tengas
- Si no sabes algo específico, dilo claramente pero ofrece lo que sí sabes
- Mantén las respuestas enfocadas en la pregunta específica
- Usa un lenguaje simple, como si hablaras con un dueño de negocio

INFORMACIÓN DE CONTACTO DE LUCAS (si preguntan):
- Email: lucas@lucasbenites.com
- WhatsApp: +54 3517554495
- Teléfono: +54 3517554495
- Calendario: https://meet.brevo.com/lucas-benites
- LinkedIn: /in/lucas-benites
- Sitio web: www.lucasbenites.com

Responde solo la pregunta específica que te hacen, siempre identificándote como su ASISTENTE."""

    def _get_basic_company_info(self, message: str) -> str:
        """Información básica de la empresa cuando RAG no está disponible"""
        message_lower = message.lower()
        
        # Información básica por categorías
        if any(word in message_lower for word in ['contacto', 'email', 'teléfono', 'telefono', 'whatsapp']):
            return """INFORMACIÓN DE CONTACTO - LUCAS BENITES:

Email: lucas@lucasbenites.com
WhatsApp: +54 3517554495
Teléfono: +54 3517554495
Calendario para reuniones: https://meet.brevo.com/lucas-benites
LinkedIn: /in/lucas-benites
Sitio web: www.lucasbenites.com

Lucas es especialista en IA para PyMEs y ayuda a empresarios a automatizar sus negocios.

Puedes contactarlo por cualquiera de estos medios según tu preferencia."""
        
        elif any(word in message_lower for word in ['servicio', 'que hacen', 'que ofrece', 'tecnología', 'tecnologia']):
            return """SERVICIOS:
- Especialización en tecnología para pequeñas y medianas empresas (PyMEs)
- Desarrollo de soluciones tecnológicas personalizadas
- Consultoría en automatización de procesos
- Implementación de chatbots y sistemas de atención automatizada
- Soluciones para optimizar operaciones comerciales"""
        
        elif any(word in message_lower for word in ['precio', 'costo', 'cuánto', 'cuanto']):
            return """PRECIOS:
- Los precios varían según las necesidades específicas de cada negocio
- Se realizan presupuestos personalizados después de entender los requerimientos
- La consulta inicial es gratuita para evaluar las necesidades
- Los costos dependen del tipo de solución y alcance del proyecto"""
        
        elif any(word in message_lower for word in ['lucas', 'quien es', 'quién es']):
            return """LUCAS BENITES:
- Especialista en tecnología para PyMEs
- Ayuda a empresarios a implementar soluciones tecnológicas
- Experiencia trabajando con pequeños y medianos negocios
- Enfoque en hacer la tecnología accesible y práctica para empresarios"""
        
        else:
            return """INFORMACIÓN GENERAL:
- Lucas Benites es especialista en tecnología para PyMEs
- Ayuda a empresarios a implementar soluciones tecnológicas prácticas
- Los servicios incluyen automatización, chatbots y sistemas personalizados
- Ofrece consulta inicial gratuita para evaluar necesidades específicas"""
    
    def _get_fallback_response(self, message: str) -> str:
        """Respuesta de respaldo cuando hay errores"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['contacto', 'email', 'teléfono', 'whatsapp']):
            return "Para contactar a Lucas Benites: Email: lucas@lucasbenites.com, WhatsApp: +54 3517554495, o agenda una reunión en: https://meet.brevo.com/lucas-benites"
        
        elif any(word in message_lower for word in ['precio', 'costo', 'cuánto']):
            return "Los precios se establecen según las necesidades específicas de cada negocio. En una charla con Lucas podrías obtener un presupuesto personalizado."
        
        else:
            return "Lucas se especializa en tecnología para PyMEs. ¿Te gustaría saber algo específico sobre cómo él puede ayudarte?"
    
    def should_use_rag(self, message: str) -> bool:
        """Determina si debe usar RAG para esta consulta"""
        message_lower = message.lower()
        
        # Palabras clave que indican necesidad de información específica
        info_keywords = [
            'qué es', 'que es', 'cómo funciona', 'como funciona', 'cuánto cuesta', 'cuanto cuesta',
            'precio', 'contacto', 'email', 'teléfono', 'telefono', 'whatsapp', 'dirección', 'direccion',
            'horario', 'información', 'informacion', 'servicio', 'que hacen', 'que ofrece',
            'lucas', 'empresa', 'ubicación', 'ubicacion', 'metodología', 'metodologia',
            'experiencia', 'casos', 'ejemplos', 'referencias'
        ]
        
        return any(keyword in message_lower for keyword in info_keywords)