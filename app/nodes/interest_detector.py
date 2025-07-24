"""
Nodo para detectar falta de interés y ofrecer conexión directa con Lucas.
"""

from typing import Dict, Any
from app.core.prompt_manager import PromptManager


class InterestDetector:
    def __init__(self):
        self.prompt_manager = PromptManager()
        
        # Palabras clave que indican falta de interés
        self.disinterest_keywords = [
            "no me interesa", "no estoy interesado", "no tengo tiempo",
            "no es para mí", "no necesito", "no puedo", "muy caro",
            "no tengo presupuesto", "tal vez más tarde", "quizás después",
            "no ahora", "estoy ocupado", "no es prioritario",
            "no veo la necesidad", "no me convence", "gracias pero no"
        ]
        
        # Frases que sugieren dudas o necesidad de más información
        self.hesitation_keywords = [
            "no estoy seguro", "tengo dudas", "necesito pensarlo",
            "tengo que consultarlo", "no sé", "me parece complejo",
            "no entiendo bien", "necesito más información",
            "tengo preguntas", "no me queda claro"
        ]

    def detect_interest_level(self, message: str, conversation_history: list) -> Dict[str, Any]:
        """
        Detecta el nivel de interés basado en el mensaje y historial de conversación.
        
        Returns:
            Dict con 'interest_level', 'should_offer_human_contact', 'reasoning'
        """
        message_lower = message.lower()
        
        # Contar indicadores de desinterés
        disinterest_count = sum(1 for keyword in self.disinterest_keywords 
                              if keyword in message_lower)
        
        # Contar indicadores de duda/hesitación
        hesitation_count = sum(1 for keyword in self.hesitation_keywords 
                             if keyword in message_lower)
        
        # Analizar contexto de la conversación
        context_analysis = self._analyze_conversation_context(conversation_history)
        
        # Determinar nivel de interés
        interest_level = "high"  # default
        should_offer_human = False
        reasoning = []
        
        if disinterest_count >= 2:
            interest_level = "very_low"
            should_offer_human = True
            reasoning.append(f"Múltiples indicadores de desinterés ({disinterest_count})")
            
        elif disinterest_count >= 1:
            interest_level = "low"
            should_offer_human = True
            reasoning.append("Indicadores claros de desinterés")
            
        elif hesitation_count >= 2:
            interest_level = "medium"
            should_offer_human = True
            reasoning.append("Múltiples dudas expresadas, podría beneficiarse de contacto humano")
            
        elif context_analysis["repeated_questions"] >= 3:
            interest_level = "medium"
            should_offer_human = True
            reasoning.append("Preguntas repetidas, posible confusión")
            
        elif context_analysis["conversation_length"] >= 10 and context_analysis["no_progress"]:
            interest_level = "medium"
            should_offer_human = True
            reasoning.append("Conversación larga sin progreso claro")
        
        # Casos especiales donde NO ofrecer contacto humano
        if any(phrase in message_lower for phrase in ["quiero agendar", "programar reunión", "cuando podemos hablar"]):
            should_offer_human = False
            interest_level = "high"
            reasoning = ["Usuario expresó interés en agendar reunión"]
        
        return {
            "interest_level": interest_level,
            "should_offer_human_contact": should_offer_human,
            "reasoning": reasoning,
            "disinterest_indicators": disinterest_count,
            "hesitation_indicators": hesitation_count,
            "context_analysis": context_analysis
        }

    def _analyze_conversation_context(self, conversation_history: list) -> Dict[str, Any]:
        """Analiza el contexto de la conversación para detectar patrones."""
        if not conversation_history:
            return {
                "conversation_length": 0,
                "repeated_questions": 0,
                "no_progress": False,
                "user_engagement": "unknown"
            }
        
        user_messages = [msg for msg in conversation_history if msg.get("sender") == "user"]
        
        # Detectar preguntas repetidas
        questions = [msg["message"] for msg in user_messages if "?" in msg["message"]]
        repeated_questions = 0
        
        for i, question in enumerate(questions):
            for j, other_question in enumerate(questions[i+1:], i+1):
                # Similitud simple basada en palabras clave
                if self._are_similar_questions(question, other_question):
                    repeated_questions += 1
                    break
        
        # Determinar si hay progreso en la conversación
        recent_messages = user_messages[-3:] if len(user_messages) >= 3 else user_messages
        no_progress = self._detect_lack_of_progress(recent_messages)
        
        return {
            "conversation_length": len(conversation_history),
            "repeated_questions": repeated_questions,
            "no_progress": no_progress,
            "user_engagement": self._assess_user_engagement(user_messages)
        }

    def _are_similar_questions(self, q1: str, q2: str) -> bool:
        """Determina si dos preguntas son similares."""
        words1 = set(q1.lower().split())
        words2 = set(q2.lower().split())
        
        # Si comparten más del 60% de las palabras, son similares
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if len(union) == 0:
            return False
            
        similarity = len(intersection) / len(union)
        return similarity > 0.6

    def _detect_lack_of_progress(self, recent_messages: list) -> bool:
        """Detecta si la conversación no está progresando."""
        if len(recent_messages) < 2:
            return False
        
        # Indicadores de falta de progreso
        stagnation_phrases = [
            "no entiendo", "sigo sin entender", "no me queda claro",
            "pero no", "sin embargo", "aunque", "pero mi duda es"
        ]
        
        stagnation_count = 0
        for msg in recent_messages:
            msg_lower = msg["message"].lower()
            for phrase in stagnation_phrases:
                if phrase in msg_lower:
                    stagnation_count += 1
                    break
        
        return stagnation_count >= 2

    def _assess_user_engagement(self, user_messages: list) -> str:
        """Evalúa el nivel de engagement del usuario."""
        if not user_messages:
            return "unknown"
        
        total_chars = sum(len(msg["message"]) for msg in user_messages)
        avg_length = total_chars / len(user_messages)
        
        if avg_length > 100:
            return "high"
        elif avg_length > 30:
            return "medium"
        else:
            return "low"

    def generate_human_contact_offer(self, prospect_data: Dict[str, Any], 
                                   interest_analysis: Dict[str, Any]) -> str:
        """
        Genera una oferta personalizada para hablar directamente con Lucas.
        """
        name = prospect_data.get("name", "")
        company = prospect_data.get("company", "")
        interest_level = interest_analysis["interest_level"]
        
        # Personalizar mensaje según el nivel de interés
        if interest_level == "very_low":
            message = f"""Entiendo {name}, parece que quizás no es el momento adecuado para esta conversación.
            
Antes de que te vayas, ¿te gustaría hablar directamente conmigo (Lucas) por unos minutos? 
A veces es más fácil resolver dudas o encontrar la mejor solución hablando de persona a persona.

Si te parece bien, puedo reservarte 15 minutos en mi calendario para una llamada sin compromiso.
¿Qué te parece?"""

        elif interest_level == "low":
            message = f"""Hola {name}, noto que tienes algunas reservas sobre nuestra propuesta.
            
Me gustaría ofrecerte la oportunidad de hablar directamente conmigo (Lucas), el fundador de la empresa.
Podemos tener una conversación de 15-20 minutos para:

• Resolver cualquier duda específica sobre {company if company else 'tu proyecto'}
• Explorar si realmente hay un fit entre lo que necesitas y lo que ofrecemos
• Sin ningún tipo de presión comercial

¿Te gustaría que coordinemos una llamada?"""

        else:  # medium interest
            message = f"""Hola {name}, veo que tienes algunas preguntas importantes que quizás pueda resolver mejor en una conversación directa.
            
¿Te gustaría hablar conmigo (Lucas) por unos 20 minutos? Podemos:

• Revisar específicamente cómo podríamos ayudar a {company if company else 'tu empresa'}
• Resolver todas tus dudas de manera personalizada  
• Explorar opciones que se adapten mejor a tu situación

Si te interesa, puedo apartarte un espacio en mi agenda. ¿Qué te parece?"""

        return message

    def should_sync_to_brevo(self, prospect_data: Dict[str, Any], 
                           interest_analysis: Dict[str, Any]) -> bool:
        """
        Determina si el prospecto debe sincronizarse con Brevo.
        
        Se sincroniza cuando:
        1. Se ofrece contacto humano (independientemente de si acepta)
        2. El score de calificación es >= 30
        3. Se ha agendado una reunión
        """
        should_offer_human = interest_analysis.get("should_offer_human_contact", False)
        qualification_score = prospect_data.get("qualification_score", 0)
        meeting_scheduled = prospect_data.get("meeting_date") is not None
        
        return (should_offer_human or 
                qualification_score >= 30 or 
                meeting_scheduled)