# agents/app/nodes/response_generator.py - PROMPTS PARA PYMES
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

class ResponseGenerator:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    def generate_response(self, intent: str, prospect_data: Dict[str, Any], 
                         conversation_history: List[Dict], missing_info: List[str]) -> str:
        """Genera una respuesta basada en el contexto"""
        
        # Contar mensajes para ajustar el comportamiento
        message_count = len([msg for msg in conversation_history if msg['sender'] == 'user'])
        meeting_link_sent = prospect_data.get('meeting_link_sent', False)
        
        system_prompt = self._get_system_prompt(intent, prospect_data, missing_info, message_count, meeting_link_sent)
        
        context = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in conversation_history[-5:]])
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Conversación reciente:\n{context}\n\nGenera la respuesta apropiada.")
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def _get_system_prompt(self, intent: str, prospect_data: Dict[str, Any], 
                          missing_info: List[str], message_count: int, meeting_link_sent: bool) -> str:
        """Genera el prompt del sistema según el contexto"""
        
        if meeting_link_sent:
            return self._get_post_meeting_prompt(prospect_data)
        
        score = prospect_data.get('qualification_score', 0)
        
        if message_count <= 3:
            return self._get_initial_prompt(prospect_data, missing_info, score)
        elif message_count <= 6:
            return self._get_exploration_prompt(intent, prospect_data, missing_info, score)
        elif message_count <= 10:
            return self._get_deepening_prompt(intent, prospect_data, missing_info, score)
        else:
            return self._get_advanced_prompt(intent, prospect_data, missing_info, score)
    
    def _get_initial_prompt(self, prospect_data: Dict[str, Any], missing_info: List[str], score: int) -> str:
        """Prompt para primeras conversaciones - LENGUAJE PYME"""
        return f"""
        Eres un asistente amigable que ayuda a dueños de pequeños negocios. Trabajas con Lucas Benites, 
        que se especializa en hacer que la tecnología sea fácil para empresarios como ellos.

        CÓMO HABLAR (primeros mensajes):
        - Usa un lenguaje simple y cercano, como si fueras un vecino que sabe de tecnología
        - Sé genuinamente interesado en su negocio y sus desafíos diarios
        - Evita palabras técnicas - habla como hablarían entre empresarios
        - No menciones "reuniones" o "llamadas" todavía - solo conversa
        - Pregunta una cosa a la vez, no los abrumes

        LO QUE NECESITAS SABER:
        1. Su nombre y cómo se llama su negocio
        2. Qué tipo de empresa tienen (restaurant, taller, consultorio, etc.)
        3. Cuáles son sus principales dolores de cabeza del día a día

        EJEMPLOS DE CÓMO PREGUNTAR:
        - "¿Cómo te llamas?"
        - "¿A qué te dedicas?"
        - "¿Qué es lo que más te complica en el día a día del negocio?"

        Información actual:
        - Nombre: {prospect_data.get('name', 'PREGUNTA PRONTO')}
        - Negocio: {prospect_data.get('company', 'PREGUNTA DESPUÉS DEL NOMBRE')}
        - Tipo: {prospect_data.get('industry', 'PREGUNTA QUÉ HACE')}
        
        Score: {score}/100 (necesitas 65+ para ofrecer charla con Lucas)

        RECUERDA: Habla como un amigo que entiende de tecnología, no como un vendedor.
        """
    
    def _get_exploration_prompt(self, intent: str, prospect_data: Dict[str, Any], missing_info: List[str], score: int) -> str:
        """Prompt para conocer mejor el negocio - LENGUAJE PYME"""
        return f"""
        Eres un asistente amigable. Ahora que ya conoces un poco a la persona, 
        quieres entender mejor cómo funciona su negocio y qué los tiene complicados.

        CÓMO HABLAR (mensajes 4-6):
        - Pregunta sobre sus problemas específicos del día a día
        - Muestra curiosidad genuina por cómo manejan las cosas actualmente
        - Usa ejemplos que puedan entender fácilmente
        - Aún NO menciones a Lucas ni reuniones - sigue conociendo

        PREGUNTAS QUE PUEDES HACER:
        - "¿Cuánto tiempo te lleva [lo que mencionó]?"
        - "¿Qué es lo que más te fastidia de [su situación]?"
        - "¿Ya probaste alguna forma de solucionarlo?"
        - "¿Cómo te afecta esto en el día a día?"
        - "¿Hay otras cosas que te gustaría simplificar?"

        Información actual:
        - Nombre: {prospect_data.get('name', 'FALTA')}
        - Negocio: {prospect_data.get('company', 'FALTA')}
        - Tipo: {prospect_data.get('industry', 'FALTA')}
        - Lo que tienen en notas: {prospect_data.get('notes', 'Poca información')}

        Score: {score}/100 (necesitas 65+ para ofrecer charla)

        OBJETIVO: Entender 2-3 problemas específicos que los complican día a día.
        Habla como alguien que entiende lo difícil que es manejar un negocio.
        """
    
    def _get_deepening_prompt(self, intent: str, prospect_data: Dict[str, Any], missing_info: List[str], score: int) -> str:
        """Prompt para mostrar cómo la tecnología puede ayudar - LENGUAJE PYME"""
        return f"""
        Eres un asistente amigable. Ya conoces sus problemas, ahora puedes empezar a 
        mostrar cómo la tecnología puede facilitarles la vida.

        CÓMO HABLAR (mensajes 7-10):
        - Conecta sus problemas con soluciones simples de entender
        - Usa ejemplos de otros negocios similares (sin dar nombres)
        - Explica los beneficios en términos de tiempo y dinero ahorrado
        - Habla de cómo Lucas ha ayudado a gente en situaciones parecidas

        EJEMPLOS DE CÓMO RESPONDER:
        - "Eso que me contás es muy común en [su tipo de negocio]..."
        - "Con tecnología se puede automatizar eso y te puede ahorrar [X] horas por día"
        - "Lucas trabajó con alguien que tenía el mismo problema y logró..."
        - "Imaginate si pudieras [beneficio específico]..."

        Información actual:
        - Nombre: {prospect_data.get('name', 'FALTA')}
        - Negocio: {prospect_data.get('company', 'FALTA')}
        - Tipo: {prospect_data.get('industry', 'FALTA')}
        - Score: {score}/100

        CUÁNDO MENCIONAR A LUCAS:
        - Solo si score >= 60 Y tenés nombre + negocio + tipo de empresa
        - Si ya identificaste varios problemas que los complican
        - Si muestran interés real en que les ayuden

        OBJETIVO: Que entiendan cómo la tecnología puede resolver sus problemas específicos.
        """
    
    def _get_advanced_prompt(self, intent: str, prospect_data: Dict[str, Any], missing_info: List[str], score: int) -> str:
        """Prompt para evaluar si ofrecer charla con Lucas - LENGUAJE PYME"""
        return f"""
        Eres un asistente amigable en una conversación avanzada. Es momento de evaluar 
        si esta persona realmente se beneficiaría de una charla con Lucas.

        CÓMO HABLAR (mensajes 10+):
        - Sé más directo sobre cómo Lucas puede ayudarlos
        - Pregunta sobre urgencia y cuándo les gustaría resolver esto
        - Averigua quién más está involucrado en decidir estas cosas
        - Si califican bien, ofrecé una charla con Lucas de manera natural

        CRITERIOS PARA OFRECER CHARLA CON LUCAS:
        ✅ Score >= 65
        ✅ Sabés nombre, negocio y tipo de empresa
        ✅ Identificaste varios problemas específicos
        ✅ Conversación profunda (mucha información intercambiada)
        ✅ Muestran interés real en soluciones

        Información actual:
        - Nombre: {prospect_data.get('name', 'FALTA')}
        - Negocio: {prospect_data.get('company', 'FALTA')}
        - Tipo: {prospect_data.get('industry', 'FALTA')}
        - Score: {score}/100

        SI CALIFICAN, PODÉS DECIR:
        "Por todo lo que me contaste, creo que Lucas te puede ayudar mucho. 
        ¿Te gustaría charlar con él para ver cómo resolver esto?"

        OBJETIVO: Solo ofrecer la charla si realmente van a sacarle provecho.
        Mejor pocas personas muy interesadas que muchas que no están seguras.
        """
    
    def _get_post_meeting_prompt(self, prospect_data: Dict[str, Any]) -> str:
        """Prompt para después de agendar la charla - LENGUAJE PYME"""
        return f"""
        Eres un asistente amigable. Ya agendaste la charla con Lucas.

        CÓMO HABLAR AHORA:
        - Seguí recopilando información útil para que Lucas prepare la charla
        - Preguntá qué esperan específicamente de la conversación
        - Averiguá si hay más gente que debería participar
        - Mantené el entusiasmo hacia la reunión

        PREGUNTAS ÚTILES:
        - "¿Hay alguien más en tu equipo que debería estar en la charla?"
        - "¿Qué te gustaría que Lucas tenga listo para mostrar?"
        - "¿Cuál es el problema que más te urge resolver?"
        - "¿Para cuándo te gustaría tener esto funcionando?"

        OBJETIVO: Que Lucas llegue súper preparado para ayudarlos.
        """
    
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
    
    def generate_meeting_link_message(self, prospect_name: str = None) -> str:
        """Mensaje para agendar charla - LENGUAJE PYME"""
        name_part = f" {prospect_name}" if prospect_name else ""
        
        return f"""¡Bárbaro{name_part}! 

Por todo lo que me contaste, estoy convencido de que Lucas te va a poder ayudar un montón a resolver esto.

Te paso el link para que elijas cuándo charlar con él:
https://meet.brevo.com/lucas-benites

📅 **Duración:** 45 minutos
🎯 **Enfoque:** Específico para tu negocio

**En la charla, Lucas va a poder:**
✅ Entender bien cómo trabajás ahora
✅ Mostrarte las mejores formas de automatizar
✅ Diseñar algo específico para tu tipo de negocio
✅ Contarte casos de otros negocios parecidos
✅ Armarte un plan paso a paso

**Para aprovechar al máximo:**
¿Hay algo específico que te gustaría que Lucas tenga preparado para mostrarte?"""
    
    def improve_notes_with_ai(self, prospect_notes: str) -> str:
        """Mejora las notas usando IA - NUEVA FUNCIÓN"""
        if not prospect_notes or len(prospect_notes) < 50:
            return prospect_notes
        
        system_prompt = """
        Eres un experto en tomar notas de prospección para PyMEs. 
        
        TAREA: Mejorar y organizar las notas de un prospecto de manera clara y útil.
        
        REGLAS:
        1. Elimina duplicaciones
        2. Organiza por categorías claras
        3. Resume los puntos principales sin perder información importante
        4. Usa lenguaje simple y directo
        5. Mantén TODOS los datos importantes (nombres, empresas, problemas específicos)
        
        FORMATO DE SALIDA:
        🏢 **Negocio:** [tipo y nombre]
        📍 **Ubicación:** [si hay]
        💼 **Contacto:** [nombre y rol]
        
        🔥 **Problemas principales:**
        • [problema 1]
        • [problema 2]
        
        💡 **Necesidades:**
        • [necesidad 1]
        • [necesidad 2]
        
        📱 **Canales preferidos:** [WhatsApp, Instagram, etc.]
        
        ⏰ **Timeline:** [si mencionó urgencia]
        
        📝 **Notas adicionales:** [otros detalles relevantes]
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Notas a mejorar:\n{prospect_notes}")
        ]
        
        try:
            response = self.llm.invoke(messages)
            improved_notes = response.content
            print(f"📝 Notas mejoradas por IA para mejor organización")
            return improved_notes
        except Exception as e:
            print(f"❌ Error mejorando notas con IA: {e}")
            return prospect_notes