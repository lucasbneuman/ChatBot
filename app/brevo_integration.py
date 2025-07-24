# agents/app/brevo_integration.py
import requests
from typing import Dict, Any, Optional, List

class BrevoIntegration:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.brevo.com/v3"
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json", 
            "api-key": api_key
        }
    
    def get_contact(self, email: str) -> Optional[Dict[str, Any]]:
        """Obtiene un contacto por email"""
        url = f"{self.base_url}/contacts/{email}"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error obteniendo contacto: {e}")
            return None
    
    def create_contact(self, email: str, attributes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Crea un nuevo contacto"""
        url = f"{self.base_url}/contacts"
        
        data = {
            "email": email,
            "attributes": attributes
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            
            if response.status_code == 201:
                return response.json()
            elif response.status_code == 400:
                print(f"Error 400 - Datos inválidos: {response.text}")
            elif response.status_code == 401:
                print(f"Error 401 - API key inválida")
            elif response.status_code == 409:
                print(f"Error 409 - Contacto ya existe: {response.text}")
            else:
                print(f"Error {response.status_code}: {response.text}")
                
            return None
        except Exception as e:
            print(f"Error creando contacto: {e}")
            return None
    
    def update_contact(self, email: str, attributes: Dict[str, Any]) -> bool:
        """Actualiza un contacto existente"""
        url = f"{self.base_url}/contacts/{email}"
        
        data = {"attributes": attributes}
        
        try:
            response = requests.put(url, json=data, headers=self.headers)
            return response.status_code == 204
        except Exception as e:
            print(f"Error actualizando contacto: {e}")
            return False
    
    def send_transactional_email(self, to_email: str, template_id: int, 
                                params: Dict[str, Any]) -> bool:
        """Envía un email transaccional"""
        url = f"{self.base_url}/smtp/email"
        
        data = {
            "to": [{"email": to_email}],
            "templateId": template_id,
            "params": params
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            return response.status_code == 201
        except Exception as e:
            print(f"Error enviando email: {e}")
            return False
    
    def add_contact_to_list(self, email: str, list_id: int) -> bool:
        """Añade un contacto a una lista específica"""
        url = f"{self.base_url}/contacts/lists/{list_id}/contacts/add"
        
        data = {"emails": [email]}
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            return response.status_code == 204
        except Exception as e:
            print(f"Error añadiendo contacto a lista: {e}")
            return False
    
    def create_deal(self, deal_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Crea una nueva oportunidad en Brevo CRM"""
        url = f"{self.base_url}/crm/deals"
        
        try:
            response = requests.post(url, json=deal_data, headers=self.headers)
            
            # Brevo devuelve 200 para deals exitosos, no 201
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error creando deal: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creando deal: {e}")
            return None
    
    def create_task(self, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Crea una nueva tarea en Brevo CRM"""
        url = f"{self.base_url}/crm/tasks"
        
        try:
            response = requests.post(url, json=task_data, headers=self.headers)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"Error creando tarea: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creando tarea: {e}")
            return None
    
    def create_note(self, note_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Crea una nueva nota en Brevo CRM"""
        url = f"{self.base_url}/crm/notes"
        
        try:
            response = requests.post(url, json=note_data, headers=self.headers)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"Error creando nota: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creando nota: {e}")
            return None
    
    def update_contact_email(self, contact_id: str, new_email: str) -> bool:
        """Actualiza el email de un contacto existente"""
        url = f"{self.base_url}/contacts/{contact_id}"
        
        data = {"email": new_email}
        
        try:
            response = requests.put(url, json=data, headers=self.headers)
            return response.status_code == 204
        except Exception as e:
            print(f"Error actualizando email del contacto: {e}")
            return False
    
    def update_deal(self, deal_id: str, deal_data: Dict[str, Any]) -> bool:
        """Actualiza una oportunidad existente"""
        url = f"{self.base_url}/crm/deals/{deal_id}"
        
        try:
            response = requests.patch(url, json=deal_data, headers=self.headers)
            return response.status_code == 204
        except Exception as e:
            print(f"Error actualizando deal: {e}")
            return False
    
    def get_deal_by_contact(self, contact_id: str) -> Optional[List[Dict[str, Any]]]:
        """Obtiene los deals asociados a un contacto"""
        url = f"{self.base_url}/crm/deals"
        params = {"filters[linkedContactsIds]": contact_id}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json().get("items", [])
            return None
        except Exception as e:
            print(f"Error obteniendo deals del contacto: {e}")
            return None
    
    def sync_prospect_to_brevo(self, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sincroniza un prospecto con Brevo:
        1. Crea/actualiza contacto
        2. Añade a lista 'Habló con Chatbot'
        3. Crea oportunidad
        """
        result = {
            "success": False,
            "contact_created": False,
            "deal_created": False,
            "contact_id": None,
            "deal_id": None,
            "errors": []
        }
        
        email = prospect_data.get("email")
        if not email:
            result["errors"].append("Email requerido para sincronización")
            return result
        
        try:
            # 1. Verificar si el contacto existe
            existing_contact = self.get_contact(email)
            contact_id = None
            
            if existing_contact:
                # Actualizar contacto existente
                attributes = self._prepare_contact_attributes(prospect_data)
                if self.update_contact(email, attributes):
                    contact_id = existing_contact.get("id")
                else:
                    result["errors"].append("Error actualizando contacto")
            else:
                # Crear nuevo contacto
                attributes = self._prepare_contact_attributes(prospect_data)
                new_contact = self.create_contact(email, attributes)
                if new_contact:
                    contact_id = new_contact.get("id")
                    result["contact_created"] = True
                else:
                    result["errors"].append("Error creando contacto - verificar logs")
            
            if contact_id:
                result["contact_id"] = contact_id
                
                # 2. Añadir a lista "Habló con Chatbot" 
                from app.config.brevo_config import brevo_config
                chatbot_list_id = brevo_config.CHATBOT_LIST_ID
                self.add_contact_to_list(email, chatbot_list_id)
                
                # 3. Crear oportunidad
                deal_data = self._prepare_deal_data(prospect_data, contact_id)
                new_deal = self.create_deal(deal_data)
                
                if new_deal:
                    result["deal_created"] = True
                    deal_id = new_deal.get("id")
                    result["deal_id"] = deal_id
                    
                    # 4. Crear tarea automática para la oportunidad
                    task_result = self._create_automatic_task(deal_id, prospect_data, contact_id)
                    result["task_created"] = task_result is not None
                    if task_result:
                        result["task_id"] = task_result.get("id")
                    
                    # 5. Crear nota con información detallada de la conversación
                    note_result = self._create_deal_note(deal_id, prospect_data)
                    result["note_created"] = note_result is not None
                    if note_result:
                        result["note_id"] = note_result.get("id")
                    
                    # 6. Actualizar email del contacto si se detectó uno real
                    extracted_email = self._extract_real_email_from_data(prospect_data)
                    if extracted_email and not extracted_email.endswith('.temp'):
                        email_updated = self.update_contact_email(contact_id, extracted_email)
                        result["email_updated"] = email_updated
                    
                    result["success"] = True
                else:
                    result["errors"].append("Error creando oportunidad")
        
        except Exception as e:
            result["errors"].append(f"Error general: {str(e)}")
        
        return result
    
    def _prepare_contact_attributes(self, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara los atributos del contacto para Brevo"""
        attributes = {}
        
        # Mapeo de campos
        field_mapping = {
            "name": "FIRSTNAME",
            "company": "COMPANY", 
            "industry": "INDUSTRY",
            "location": "LOCATION",
            "budget": "BUDGET",
            "qualification_score": "SCORE_CHATBOT",
            "status": "STATUS_CHATBOT"
        }
        
        for our_field, brevo_field in field_mapping.items():
            if prospect_data.get(our_field):
                attributes[brevo_field] = prospect_data[our_field]
        
        return attributes
    
    def _prepare_deal_data(self, prospect_data: Dict[str, Any], contact_id: str) -> Dict[str, Any]:
        """Prepara los datos de la oportunidad para Brevo"""
        from app.config.brevo_config import brevo_config
        
        # Formato: "Nombre lead - Empresa o Industria"
        name = prospect_data.get('name', 'Sin nombre')
        company_or_industry = prospect_data.get('company') or prospect_data.get('industry') or 'Sin empresa'
        deal_name = f"{name} - {company_or_industry}"
        
        # Determinar el stage según el estado del prospecto
        status = prospect_data.get("status", "").upper()
        stage_id = brevo_config.PIPELINE_STAGES["new_lead"]  # Default
        
        if "QUALIFIED" in status:
            stage_id = brevo_config.PIPELINE_STAGES["qualified"]
        elif "MEETING" in status or prospect_data.get("meeting_date"):
            stage_id = brevo_config.PIPELINE_STAGES["meeting_scheduled"]
        elif "CLOSED" in status:
            stage_id = brevo_config.PIPELINE_STAGES["closed_won"]
        elif "REJECTED" in status or "DISQUALIFIED" in status:
            stage_id = brevo_config.PIPELINE_STAGES["closed_lost"]
        
        deal_data = {
            "name": deal_name,
            "stageId": stage_id,
            "attributes": {
                "deal_description": self._build_deal_description(prospect_data),
                "deal_owner": "Lucas Benites"
            },
            "linkedContactsIds": [contact_id]
        }
        
        # Si hay una fecha de reunión, añadirla a la descripción
        if prospect_data.get("meeting_date"):
            deal_data["attributes"]["deal_description"] += f"\n\nReunión programada: {prospect_data['meeting_date']}"
        
        # Determinar el valor estimado basado en el presupuesto
        deal_value = brevo_config.get_deal_value_from_budget(prospect_data.get("budget", ""))
        deal_data["value"] = deal_value
        
        return deal_data
    
    def _build_deal_description(self, prospect_data: Dict[str, Any]) -> str:
        """Construye una descripción detallada del deal usando los datos del prospecto"""
        description_parts = [
            "=== PROSPECTO DESDE CHATBOT ===",
            f"Score de calificación: {prospect_data.get('qualification_score', 0)}/100",
            f"Estado: {prospect_data.get('status', 'N/A')}"
        ]
        
        if prospect_data.get("company"):
            description_parts.append(f"Empresa: {prospect_data.get('company')}")
        if prospect_data.get("industry"):
            description_parts.append(f"Industria: {prospect_data.get('industry')}")
        if prospect_data.get("budget"):
            description_parts.append(f"Presupuesto: {prospect_data.get('budget')}")
        if prospect_data.get("location"):
            description_parts.append(f"Ubicación: {prospect_data.get('location')}")
        
        # Añadir notas si existen
        if prospect_data.get("notes") and prospect_data.get("notes") != "Sin notas":
            description_parts.append("")
            description_parts.append("=== NOTAS DE LA CONVERSACIÓN ===")
            description_parts.append(prospect_data.get("notes"))
        
        return "\n".join(description_parts)
    
    def _create_automatic_task(self, deal_id: str, prospect_data: Dict[str, Any], contact_id: str) -> Optional[Dict[str, Any]]:
        """Crea una tarea automática asociada al deal"""
        from datetime import datetime, timedelta
        
        # Determinar el tipo de tarea según si se envió link o no
        meeting_sent = prospect_data.get("meeting_link_sent", False)
        
        if meeting_sent:
            task_name = f"Seguimiento reunión - {prospect_data.get('name', 'Sin nombre')}"
            task_content = f"Hacer seguimiento de la reunión programada con {prospect_data.get('name')} de {prospect_data.get('company', 'empresa sin especificar')}."
            due_days = 3  # 3 días después
        else:
            task_name = f"Contactar lead - {prospect_data.get('name', 'Sin nombre')}"
            task_content = f"Contactar a {prospect_data.get('name')} de {prospect_data.get('company', 'empresa sin especificar')} para agendar reunión."
            due_days = 1  # 1 día después
        
        # Calcular fecha de vencimiento (formato ISO con tiempo)
        due_date = datetime.now() + timedelta(days=due_days)
        due_date_str = due_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        from app.config.brevo_config import brevo_config
        
        task_data = {
            "name": task_name,
            "content": task_content,
            "assignToUserId": brevo_config.get_user_id(),
            "dealsIds": [str(deal_id)],  # Brevo requiere array de dealsIds
            "taskTypeId": brevo_config.get_task_type_id(),
            "date": due_date_str,
            "done": False
        }
        
        return self.create_task(task_data)
    
    def _create_deal_note(self, deal_id: str, prospect_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Crea una nota detallada para la oportunidad"""
        
        # Construir contenido de la nota
        note_content = f"""=== INFORMACIÓN DEL PROSPECTO ===
Nombre: {prospect_data.get('name', 'N/A')}
Empresa: {prospect_data.get('company', 'N/A')}
Industria: {prospect_data.get('industry', 'N/A')}
Ubicación: {prospect_data.get('location', 'N/A')}
Presupuesto: {prospect_data.get('budget', 'N/A')}
Score de calificación: {prospect_data.get('qualification_score', 0)}/100

=== ESTADO DE LA CONVERSACIÓN ===
Estado: {prospect_data.get('status', 'N/A')}
Link de reunión enviado: {'Sí' if prospect_data.get('meeting_link_sent') else 'No'}

=== NOTAS DE LA CONVERSACIÓN ===
{prospect_data.get('notes', 'Sin notas adicionales')}

=== INFORMACIÓN TÉCNICA ===
Prospecto ID: {prospect_data.get('id', 'N/A')}
Email: {prospect_data.get('email', 'N/A')}
Fecha de creación: {prospect_data.get('created_at', 'N/A')}
Origen: Chatbot de prospección automatizada"""
        
        note_data = {
            "text": note_content,  # Brevo usa "text" no "content"
            "dealIds": [str(deal_id)]  # Brevo requiere array de dealIds
        }
        
        return self.create_note(note_data)
    
    def _extract_real_email_from_data(self, prospect_data: Dict[str, Any]) -> Optional[str]:
        """Extrae el email real de los datos del prospecto (no temporal)"""
        email = prospect_data.get('email', '')
        
        # Si el email es temporal, intentar extraer uno real
        if not email or email.endswith('.temp'):
            # Buscar en notes u otros campos
            notes = prospect_data.get('notes', '')
            if notes:
                import re
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, notes)
                for found_email in emails:
                    if not found_email.endswith('.temp'):
                        return found_email
        
        return email if not email.endswith('.temp') else None
