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
