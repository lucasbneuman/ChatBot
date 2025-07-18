# agents/app/nodes/message_parser.py
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
import re
import json

class MessageParser:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    def classify_intent(self, message: str, conversation_history: List[Dict]) -> str:
        """Clasifica la intención del mensaje"""
        
        system_prompt = """
        Eres un experto en clasificación de intenciones para prospección de ventas de servicios de IA..
        Trabajas para Lucas Benites, experto en implementación de IA para PyMEs.
        
        Clasifica el mensaje del usuario en una de estas categorías:
        
        - GREETING: Saludos iniciales
        - INFORMATION: Proporciona información sobre su empresa o necesidades de IA
        - INTEREST: Muestra interés en automatización/IA/chatbots
        - OBJECTION: Pone objeciones o dudas sobre IA
        - REJECTION: Rechaza explícitamente
        - SCHEDULING: Quiere agendar una consulta con Lucas
        - NOTES: Información adicional después de enviar link de reunión
        - CLOSING: Finaliza la conversación
        
        Responde solo con la categoría en mayúsculas.
        """
        
        context = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in conversation_history[-5:]])
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Contexto:\n{context}\n\nMensaje actual: {message}")
        ]
        
        try:
            response = self.llm.invoke(messages)
            return response.content.strip().upper()
        except:
            return "INFORMATION"  # Default fallback
    
    def extract_entities(self, message: str, conversation_context: str = "") -> Dict[str, Any]:
        """Extrae entidades del mensaje con múltiples métodos"""
        
        # Método 1: Extracción con LLM mejorada
        llm_extracted = self._extract_with_llm(message, conversation_context)
        
        # Método 2: Extracción con regex como respaldo
        regex_extracted = self._extract_with_regex(message)
        
        # Método 3: Extracción por palabras clave
        keyword_extracted = self._extract_with_keywords(message)
        
        # Combinar todos los métodos (prioridad: LLM > regex > keywords)
        final_result = {}
        
        # Empezar con keywords (más básico)
        final_result.update(keyword_extracted)
        
        # Sobrescribir con regex (más específico)
        for key, value in regex_extracted.items():
            if value:
                final_result[key] = value
        
        # Sobrescribir con LLM (más inteligente)
        for key, value in llm_extracted.items():
            if value:
                final_result[key] = value
        
        # Debug: Imprimir lo que se extrajo
        print(f"🔍 DEBUG - Mensaje: {message}")
        print(f"📊 DEBUG - Extraído: {final_result}")
        
        return final_result
    
    def _extract_with_llm(self, message: str, context: str) -> Dict[str, Any]:
        """Extracción con LLM mejorada"""
        
        system_prompt = """
        Eres un experto extractor de información. Analiza el mensaje y extrae TODA la información posible.
        
        REGLAS CRÍTICAS:
        1. Si dice "Soy [nombre]" → name: "[nombre]"
        2. Si menciona "empresa de [tipo]" → industry: "[tipo]", company: "Empresa de [tipo]"
        3. Si dice "mi empresa" o "mi negocio" → inferir company y/o industry
        4. Si menciona problemas → pain_points: ["problema"]
        5. Si quiere chatbot/automatización → needs: "automatización"
        6. Si menciona WhatsApp/Instagram → notes: "Canal: [plataforma]"
        
        EJEMPLOS ESPECÍFICOS:
        - "Soy Agustín" → {"name": "Agustín"}
        - "empresa de autopartes" → {"industry": "autopartes", "company": "Empresa de autopartes"}
        - "chatbot en whatsapp" → {"needs": "chatbot WhatsApp", "notes": "Canal: WhatsApp"}
        - "me preguntan por precios" → {"pain_points": ["consultas repetitivas de precios"]}
        
        Devuelve JSON válido. NO uses null, usa cadenas vacías o arrays vacíos.
        
        {
            "name": "",
            "company": "",
            "industry": "",
            "budget": "",
            "location": "",
            "pain_points": [],
            "needs": "",
            "notes": "",
            "decision_maker": false
        }
        """
        
        full_context = f"Contexto: {context}\n\nMensaje a analizar: {message}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=full_context)
        ]
        
        try:
            response = self.llm.invoke(messages)
            result = json.loads(response.content)
            
            # Limpiar valores vacíos y convertir a formato esperado
            cleaned_result = {}
            for key, value in result.items():
                if value and value != "" and value != []:
                    if key == "decision_maker" and isinstance(value, bool):
                        cleaned_result[key] = value
                    elif isinstance(value, list) and len(value) > 0:
                        cleaned_result[key] = value
                    elif isinstance(value, str) and value.strip():
                        cleaned_result[key] = value.strip()
            
            return cleaned_result
            
        except Exception as e:
            print(f"Error en LLM extraction: {e}")
            return {}
    
    def _extract_with_regex(self, message: str) -> Dict[str, Any]:
        """Extracción con regex específicos - ARREGLADO"""
        result = {}
        
        # Patrones para nombres - MÁS ESTRICTOS
        name_patterns = [
            r'(?:soy|me\s+llamo|mi\s+nombre\s+es)\s+([A-Z][a-zA-ZáéíóúÁÉÍÓÚñÑ]{2,})',  # Min 3 chars
            r'(?:soy|me\s+llamo)\s+([A-Z][a-zA-ZáéíóúÁÉÍÓÚñÑ]{2,})(?:\s|,|\.|\s+y\s|\s+de\s)',  # Seguido de separador
        ]
        
        # NO extraer nombres de palabras sueltas como "cual", "que", etc.
        excluded_words = ['cual', 'que', 'como', 'donde', 'cuando', 'porque', 'para', 'por', 'con', 'sin', 'sobre', 'bajo', 'ante', 'desde', 'hasta', 'hacia', 'según', 'durante', 'mediante', 'entre', 'dentro', 'fuera', 'además', 'también', 'solo', 'otra', 'otro', 'esta', 'este', 'esa', 'ese', 'aquella', 'aquel', 'toda', 'todo', 'algunas', 'algunos', 'muchas', 'muchos', 'pocas', 'pocos', 'más', 'menos', 'mejor', 'peor', 'mayor', 'menor', 'primera', 'primer', 'segunda', 'segundo', 'tercera', 'tercer', 'última', 'último', 'siguiente', 'anterior', 'nueva', 'nuevo', 'vieja', 'viejo', 'grande', 'pequeña', 'pequeño', 'buena', 'bueno', 'mala', 'malo', 'alta', 'alto', 'baja', 'bajo', 'larga', 'largo', 'corta', 'corto', 'fácil', 'difícil', 'importante', 'necesaria', 'necesario', 'posible', 'imposible', 'segura', 'seguro', 'peligrosa', 'peligroso', 'clara', 'claro', 'oscura', 'oscuro', 'rápida', 'rápido', 'lenta', 'lento', 'fuerte', 'débil', 'rica', 'rico', 'pobre', 'feliz', 'triste', 'alegre', 'enojada', 'enojado', 'cansada', 'cansado', 'aburrida', 'aburrido', 'interesante', 'divertida', 'divertido', 'seria', 'serio', 'joven', 'vieja', 'viejo', 'casada', 'casado', 'soltera', 'soltero', 'trabajadora', 'trabajador', 'estudiante', 'profesor', 'profesora', 'doctor', 'doctora', 'ingeniero', 'ingeniera', 'abogado', 'abogada', 'artista', 'escritor', 'escritora', 'músico', 'música', 'cantante', 'actor', 'actriz', 'deportista', 'cocinero', 'cocinera', 'vendedor', 'vendedora', 'comprador', 'compradora', 'cliente', 'jefe', 'jefa', 'empleado', 'empleada', 'trabajador', 'trabajadora', 'dueño', 'dueña', 'propietario', 'propietaria', 'socio', 'socia', 'amigo', 'amiga', 'hermano', 'hermana', 'primo', 'prima', 'tío', 'tía', 'abuelo', 'abuela', 'padre', 'madre', 'hijo', 'hija', 'nieto', 'nieta', 'esposo', 'esposa', 'novio', 'novia', 'vecino', 'vecina', 'conocido', 'conocida', 'extraño', 'extraña', 'persona', 'gente', 'hombre', 'mujer', 'niño', 'niña', 'bebé', 'adulto', 'adulta', 'anciano', 'anciana', 'joven']
        
        for pattern in name_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                potential_name = match.group(1).strip()
                # Verificar que no sea una palabra excluida
                if potential_name.lower() not in excluded_words and len(potential_name) > 2:
                    result['name'] = potential_name
                    break
        
        # Patrones para empresa/industria
        business_patterns = [
            r'empresa\s+de\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)',
            r'negocio\s+de\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)',
            r'venta\s+de\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)',
            r'trabajo\s+en\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)',
        ]
        
        for pattern in business_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                industry = match.group(1).strip()
                result['industry'] = industry
                result['company'] = f"Empresa de {industry}"
                break
        
        # Patrones para necesidades
        if any(keyword in message.lower() for keyword in ['chatbot', 'bot', 'automatiz', 'responder automático']):
            result['needs'] = 'chatbot/automatización'
        
        # Patrones para pain points
        pain_indicators = [
            'me preguntan', 'preguntas repetitivas', 'pierdo tiempo', 'mismo mensaje',
            'consultas frecuentes', 'respuestas automáticas'
        ]
        
        pain_points = []
        for indicator in pain_indicators:
            if indicator in message.lower():
                pain_points.append(f"problema: {indicator}")
        
        if pain_points:
            result['pain_points'] = pain_points
        
        # Patrones para plataformas
        platform_patterns = [
            (r'whatsapp|wapp', 'WhatsApp'),
            (r'instagram|ig', 'Instagram'),
            (r'facebook|fb', 'Facebook')
        ]
        
        for pattern, platform in platform_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                result['notes'] = f"Canal preferido: {platform}"
                break
        
        return result
    
    def _extract_with_keywords(self, message: str) -> Dict[str, Any]:
        """Extracción básica por palabras clave"""
        result = {}
        message_lower = message.lower()
        
        # Industrias comunes
        industries = {
            'autopartes': 'autopartes',
            'auto partes': 'autopartes',
            'repuestos': 'autopartes',
            'e-commerce': 'e-commerce',
            'ecommerce': 'e-commerce',
            'tienda': 'retail',
            'restaurante': 'restaurantes',
            'comida': 'restaurantes',
            'software': 'tecnología',
            'tech': 'tecnología',
            'consultoría': 'consultoría',
            'asesoría': 'consultoría'
        }
        
        for keyword, industry in industries.items():
            if keyword in message_lower:
                result['industry'] = industry
                if not result.get('company'):
                    result['company'] = f"Empresa de {industry}"
                break
        
        # Necesidades comunes
        needs_keywords = {
            'chatbot': 'chatbot',
            'bot': 'chatbot',
            'automatización': 'automatización',
            'respuestas automáticas': 'automatización',
            'atención al cliente': 'customer service'
        }
        
        for keyword, need in needs_keywords.items():
            if keyword in message_lower:
                result['needs'] = need
                break
        
        # Pain points comunes
        if any(word in message_lower for word in ['preguntan', 'consultas', 'tiempo', 'repetitiv']):
            result['pain_points'] = ['consultas repetitivas']
        
        return result