"""
Configuración específica para la integración con Brevo.
"""

import os
from typing import Dict, Any

class BrevoConfig:
    """Configuración para la integración con Brevo CRM."""
    
    def __init__(self):
        # CONFIGURACIÓN ESTÁTICA - Modifica estos valores según tu cuenta Brevo
        
        # Lista "Habló con Chatbot" - ID real obtenido de la API
        self.CHATBOT_LIST_ID = 12  # Lista "Habló con Chatbot"
        
        # Pipeline stages - IDs reales de Brevo
        self.PIPELINE_STAGES = {
            "new_lead": "699cfac0-50bd-470d-81ee-5b8c30fde466",           # Novedad
            "qualified": "0806fde7-98ad-4621-a8c8-8381add47e91",          # En proceso de verificación  
            "meeting_scheduled": "030b6c85-54e6-42b0-a7ba-aa4b18c59152",  # Demostración programada
            "waiting_commitment": "9b001fd0-b13d-4241-a165-23423dd69886", # A la espera de compromiso
            "negotiation": "4aebc25f-93c1-4994-9e00-90ab09c06cda",       # En proceso de negociación
            "closed_won": "68a96070-dac2-422f-9902-f03d992aae27",        # Ganada
            "closed_lost": "89174947-fdeb-413e-84e4-801a6ae564dc"         # Perdida
        }
        
        # Mapeo de campos entre nuestra BD y Brevo
        self.FIELD_MAPPING = {
            "name": "FIRSTNAME",
            "company": "COMPANY",
            "industry": "INDUSTRY", 
            "location": "LOCATION",
            "budget": "BUDGET",
            "qualification_score": "CHATBOT_SCORE",
            "status": "CHATBOT_STATUS",
            "notes": "NOTES"
        }
        
        # Configuración de deal values por presupuesto
        self.DEAL_VALUE_MAPPING = {
            "pequeño": 5000,
            "mediano": 15000, 
            "grande": 50000,
            "muy grande": 100000,
            "enterprise": 200000
        }

    def get_deal_value_from_budget(self, budget_text: str) -> int:
        """
        Estima el valor del deal basado en el texto del presupuesto.
        """
        if not budget_text:
            return 10000  # Default value
        
        budget_lower = budget_text.lower()
        
        # Buscar números específicos
        import re
        numbers = re.findall(r'[\d,]+', budget_text.replace('.', ''))
        if numbers:
            try:
                # Tomar el primer número encontrado
                number_str = numbers[0].replace(',', '')
                return int(number_str)
            except:
                pass
        
        # Buscar por categorías de texto
        for category, value in self.DEAL_VALUE_MAPPING.items():
            if category in budget_lower:
                return value
        
        # Buscar rangos comunes
        if "k" in budget_lower or "mil" in budget_lower:
            numbers = re.findall(r'\d+', budget_lower)
            if numbers:
                return int(numbers[0]) * 1000
        
        return 10000  # Default fallback

    def get_list_ids(self) -> Dict[str, int]:
        """
        Retorna los IDs de las listas de Brevo.
        """
        return {
            "chatbot_conversations": 12,    # Habló con Chatbot
            "contact_page": 11,             # Página de Contacto  
            "pre_consulting": 10,           # Previo Consultoría
            "post_consulting": 9,           # Seguimiento Post-Consultoría
            "automation_examples": 8,      # Descargó Ejemplos Automatización
            "checklist": 7                  # Descargó Checklist
        }
        
    def get_user_id(self) -> int:
        """Retorna el ID del usuario principal para asignar tareas"""
        return 8966670  # Lucas Benites
    
    def get_task_type_id(self) -> str:
        """Retorna el primer tipo de tarea disponible"""
        # Usar el primer tipo de tarea disponible encontrado
        return "67e26702f21da69b551a2fd6"

    def validate_configuration(self) -> Dict[str, Any]:
        """
        Valida que la configuración de Brevo esté completa.
        """
        issues = []
        warnings = []
        
        # Verificar API key
        if not os.getenv("BREVO_API_KEY"):
            issues.append("BREVO_API_KEY no configurada")
        
        # Verificar list IDs
        if self.CHATBOT_LIST_ID == 1:
            warnings.append("BREVO_CHATBOT_LIST_ID usando valor por defecto (1)")
        
        # Verificar pipeline stages
        default_stages = sum(1 for v in self.PIPELINE_STAGES.values() if v in ["1", "2", "3", "4", "5"])
        if default_stages >= 3:
            warnings.append("Pipeline stages usando valores por defecto")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "configuration": {
                "chatbot_list_id": self.CHATBOT_LIST_ID,
                "pipeline_stages": self.PIPELINE_STAGES,
                "list_ids": self.get_list_ids()
            }
        }


# Instancia global para fácil acceso
brevo_config = BrevoConfig()