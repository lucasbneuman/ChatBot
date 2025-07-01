# agents/app/nodes/data_extractor.py
from typing import Dict, Any, Optional
from ..database.prospect_db import Prospect, ProspectDatabase

class DataExtractor:
    def __init__(self, db: ProspectDatabase):
        self.db = db
    
    def update_prospect_data(self, prospect_id: int, extracted_data: Dict[str, Any]) -> bool:
        """Actualiza los datos del prospecto con información extraída"""
        prospect = self.db.get_prospect(prospect_id)
        if not prospect:
            return False
        
        # Actualizar campos con nueva información
        if extracted_data.get('name') and not prospect.name:
            prospect.name = extracted_data['name']
        
        if extracted_data.get('company') and not prospect.company:
            prospect.company = extracted_data['company']
        
        if extracted_data.get('budget') and not prospect.budget:
            prospect.budget = extracted_data['budget']
        
        if extracted_data.get('location') and not prospect.location:
            prospect.location = extracted_data['location']
        
        if extracted_data.get('industry') and not prospect.industry:
            prospect.industry = extracted_data['industry']
        
        # Calcular score de calificación
        prospect.qualification_score = self._calculate_qualification_score(prospect, extracted_data)
        
        return self.db.update_prospect(prospect)
    
    def _calculate_qualification_score(self, prospect: Prospect, extracted_data: Dict[str, Any]) -> int:
        """Calcula el puntaje de calificación del prospecto"""
        score = 0
        
        # Información básica (30 puntos)
        if prospect.name: score += 10
        if prospect.company: score += 10
        if prospect.industry: score += 10
        
        # Información de presupuesto (25 puntos)
        if prospect.budget: 
            if any(keyword in prospect.budget.lower() for keyword in ['k', 'mil', 'thousand', 'million', '$']):
                score += 25
            else:
                score += 15
        
        # Información de ubicación (15 puntos)
        if prospect.location: score += 15
        
        # Interés demostrado (30 puntos)
        if extracted_data.get('pain_points'):
            score += len(extracted_data['pain_points']) * 5
        
        if extracted_data.get('decision_maker'):
            score += 15
        
        return min(score, 100)  # Máximo 100 puntos
    
    def is_qualified(self, prospect: Prospect) -> bool:
        """Determina si un prospecto está calificado"""
        return prospect.qualification_score >= 60  # 60% o más
