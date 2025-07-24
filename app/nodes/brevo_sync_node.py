"""
Nodo para sincronizar prospectos con Brevo CRM.
"""

import os
from typing import Dict, Any, Optional
from app.brevo_integration import BrevoIntegration
from app.database.prospect_db_fixed import ProspectDatabaseFixed
from app.nodes.interest_detector import InterestDetector


class BrevoSyncNode:
    def __init__(self):
        api_key = os.getenv("BREVO_API_KEY")
        if not api_key:
            raise ValueError("BREVO_API_KEY no encontrada en variables de entorno")
        
        self.brevo = BrevoIntegration(api_key)
        self.db = ProspectDatabaseFixed("prospects_production.db")
        self.interest_detector = InterestDetector()
        
        # Importar configuración de Brevo
        try:
            from app.config.brevo_config import brevo_config
            self.brevo_config = brevo_config
        except ImportError:
            from ..config.brevo_config import brevo_config
            self.brevo_config = brevo_config

    def sync_prospect_on_meeting_scheduled(self, prospect_id: int) -> Dict[str, Any]:
        """
        Sincroniza prospecto cuando se agenda una reunión.
        """
        prospect = self.db.get_prospect(prospect_id)
        if not prospect:
            return {"success": False, "error": "Prospecto no encontrado"}
        
        # Obtener email - necesario para la sincronización
        email = self._extract_email_from_prospect(prospect)
        if not email:
            return {"success": False, "error": "Email no encontrado para el prospecto"}
        
        prospect_data = self._prepare_prospect_data(prospect, email)
        
        # Sincronizar con Brevo
        sync_result = self.brevo.sync_prospect_to_brevo(prospect_data)
        
        # Actualizar el brevo_contact_id en nuestra BD si se creó/encontró el contacto
        if sync_result["success"] and sync_result["contact_id"]:
            prospect = self.db.get_prospect(prospect_id)
            if prospect:
                prospect.brevo_contact_id = str(sync_result["contact_id"])
                self.db.update_prospect(prospect)
        
        return sync_result

    def sync_prospect_on_human_contact_offer(self, prospect_id: int, 
                                           user_response: str = None) -> Dict[str, Any]:
        """
        Sincroniza prospecto cuando se ofrece contacto humano.
        """
        prospect = self.db.get_prospect(prospect_id)
        if not prospect:
            return {"success": False, "error": "Prospecto no encontrado"}
        
        # Obtener email
        email = self._extract_email_from_prospect(prospect)
        if not email:
            return {"success": False, "error": "Email no encontrado para el prospecto"}
        
        prospect_data = self._prepare_prospect_data(prospect, email)
        
        # Añadir información sobre la respuesta del usuario
        if user_response:
            current_notes = prospect_data.get("notes", "")
            prospect_data["notes"] = f"{current_notes}\n\nRespuesta a contacto humano: {user_response}".strip()
        
        # Actualizar estado según la respuesta
        if user_response and any(phrase in user_response.lower() 
                               for phrase in ["sí", "si", "me interesa", "perfecto", "ok", "vale"]):
            prospect_data["status"] = "INTERESTED_HUMAN_CONTACT"
        else:
            prospect_data["status"] = "OFFERED_HUMAN_CONTACT"
        
        # Sincronizar con Brevo
        sync_result = self.brevo.sync_prospect_to_brevo(prospect_data)
        
        # Actualizar BD local
        updates = {"status": prospect_data["status"]}
        if user_response:
            updates["notes"] = prospect_data["notes"]
        
        if sync_result["success"] and sync_result["contact_id"]:
            updates["brevo_contact_id"] = str(sync_result["contact_id"])
        
        # Obtener el prospecto, actualizar campos y guardarlo
        prospect = self.db.get_prospect(prospect_id)
        if prospect:
            for key, value in updates.items():
                setattr(prospect, key, value)
            self.db.update_prospect(prospect)
        
        return sync_result

    def sync_new_lead_from_external_traffic(self, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sincroniza un nuevo lead que viene de tráfico externo (no Brevo).
        """
        email = prospect_data.get("email")
        if not email:
            return {"success": False, "error": "Email requerido para nuevos leads"}
        
        # Marcar como nuevo lead externo
        prospect_data["status"] = "NEW_EXTERNAL_LEAD"
        prospect_data["notes"] = prospect_data.get("notes", "") + "\n\nOrigen: Tráfico externo al chatbot"
        
        # Sincronizar con Brevo
        sync_result = self.brevo.sync_prospect_to_brevo(prospect_data)
        
        return sync_result

    def should_sync_prospect(self, prospect_id: int, conversation_history: list) -> Dict[str, Any]:
        """
        Determina si un prospecto debe sincronizarse basado en el análisis de interés.
        """
        prospect = self.db.get_prospect(prospect_id)
        if not prospect:
            return {"should_sync": False, "reason": "Prospecto no encontrado"}
        
        # Obtener último mensaje del usuario
        user_messages = [msg for msg in conversation_history if msg.get("sender") == "user"]
        if not user_messages:
            return {"should_sync": False, "reason": "No hay mensajes del usuario"}
        
        last_message = user_messages[-1]["message"]
        
        # Analizar nivel de interés
        prospect_data = self._prospect_to_dict(prospect)
        interest_analysis = self.interest_detector.detect_interest_level(
            last_message, conversation_history
        )
        
        should_sync = self.interest_detector.should_sync_to_brevo(
            prospect_data, interest_analysis
        )
        
        return {
            "should_sync": should_sync,
            "interest_analysis": interest_analysis,
            "prospect_data": prospect_data
        }

    def _extract_email_from_prospect(self, prospect) -> Optional[str]:
        """
        Extrae el email del prospecto. 
        Busca en conversation_history si no está en los campos principales.
        """
        # Primero buscar en campos directos (si los tuviéramos)
        if hasattr(prospect, 'email') and prospect.email:
            return prospect.email
        
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Buscar en conversation_history
        try:
            import json
            conversation_history = json.loads(prospect.conversation_history or "[]")
            
            for message in conversation_history:
                msg_text = message.get("message", "")
                emails = re.findall(email_pattern, msg_text)
                if emails:
                    print(f"Email encontrado en conversacion: {emails[0]}")
                    return emails[0]
        except Exception as e:
            print(f"Error buscando email en conversation_history: {e}")
        
        # Buscar en notes
        if prospect.notes:
            emails = re.findall(email_pattern, prospect.notes)
            if emails:
                print(f"Email encontrado en notas: {emails[0]}")
                return emails[0]
        
        # Buscar directamente en la tabla conversations
        try:
            from ..database.prospect_db_fixed import ProspectDatabaseFixed
            db = ProspectDatabaseFixed("prospects_production.db")
            conversations = db.get_conversation_history(prospect.id)
            
            for conv in conversations:
                emails = re.findall(email_pattern, conv.get("message", ""))
                if emails:
                    print(f"Email encontrado en tabla conversations: {emails[0]}")
                    return emails[0]
        except Exception as e:
            print(f"Error buscando email en tabla conversations: {e}")
        
        print("No se encontro email para sincronizacion con Brevo")
        
        # Como último recurso, generar email temporal para permitir sincronización
        if prospect.name and prospect.company:
            # Crear email temporal basado en nombre y empresa
            name_clean = re.sub(r'[^a-zA-Z]', '', prospect.name.lower())
            company_clean = re.sub(r'[^a-zA-Z]', '', prospect.company.lower())
            temp_email = f"{name_clean}@{company_clean}.temp"
            print(f"Generando email temporal para sync: {temp_email}")
            return temp_email
        elif prospect.name:
            # Solo con nombre
            name_clean = re.sub(r'[^a-zA-Z]', '', prospect.name.lower())
            temp_email = f"{name_clean}@chatbot.temp"
            print(f"Generando email temporal para sync: {temp_email}")
            return temp_email
        else:
            # Email genérico
            temp_email = f"prospect{prospect.id}@chatbot.temp"
            print(f"Generando email temporal para sync: {temp_email}")
            return temp_email

    def _prepare_prospect_data(self, prospect, email: str) -> Dict[str, Any]:
        """Convierte el objeto prospect a diccionario con email."""
        data = self._prospect_to_dict(prospect)
        data["email"] = email
        return data

    def _prospect_to_dict(self, prospect) -> Dict[str, Any]:
        """Convierte el objeto prospect a diccionario."""
        return {
            "id": prospect.id,
            "name": prospect.name,
            "company": prospect.company,
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

    def test_brevo_connection(self) -> Dict[str, Any]:
        """Prueba la conexión con Brevo API."""
        try:
            # Intentar hacer una petición simple para probar la API
            test_email = "test@example.com"
            contact = self.brevo.get_contact(test_email)
            
            return {
                "success": True,
                "message": "Conexión con Brevo exitosa",
                "api_accessible": True
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error de conexión: {str(e)}",
                "error": str(e)
            }