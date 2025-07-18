# agents/app/nodes/data_extractor.py - SISTEMA DE SCORING CORREGIDO
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
        
        # Actualizar campos con nueva información (solo si no están vacíos)
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
        
        # Actualizar notas SIN DUPLICAR
        self._update_notes_smart(prospect, extracted_data)
        
        # Calcular score de calificación - SISTEMA MEJORADO
        prospect.qualification_score = self._calculate_qualification_score_improved(prospect, extracted_data)
        
        return self.db.update_prospect(prospect)
    
    def _update_notes_smart(self, prospect: Prospect, extracted_data: Dict[str, Any]) -> None:
        """Actualiza notas evitando duplicación"""
        existing_notes = prospect.notes or ""
        new_notes = []
        
        # Agregar nueva información solo si no existe
        if extracted_data.get('notes') and extracted_data['notes'] not in existing_notes:
            new_notes.append(f"• {extracted_data['notes']}")
        
        if extracted_data.get('needs') and f"Necesidades: {extracted_data['needs']}" not in existing_notes:
            new_notes.append(f"Necesidades: {extracted_data['needs']}")
            
        if extracted_data.get('pain_points'):
            pain_points = extracted_data['pain_points']
            if isinstance(pain_points, list):
                for pain in pain_points:
                    pain_note = f"Pain point: {pain}"
                    if pain_note not in existing_notes:
                        new_notes.append(pain_note)
        
        if extracted_data.get('timeline') and f"Timeline: {extracted_data['timeline']}" not in existing_notes:
            new_notes.append(f"Timeline: {extracted_data['timeline']}")
        
        # Agregar nuevas notas sin duplicar
        if new_notes:
            if existing_notes:
                prospect.notes = existing_notes + "\n" + "\n".join(new_notes)
            else:
                prospect.notes = "\n".join(new_notes)
    
    def _calculate_qualification_score_improved(self, prospect: Prospect, extracted_data: Dict[str, Any]) -> int:
        """Calcula el puntaje de calificación - SISTEMA MEJORADO E INTELIGENTE"""
        score = 0
        
        # INFORMACIÓN BÁSICA (30 puntos)
        if prospect.name: score += 10
        if prospect.company: score += 10
        if prospect.industry: score += 10
        
        # INFORMACIÓN DE PRESUPUESTO (10 puntos) - Opcional
        if prospect.budget: 
            budget_str = str(prospect.budget).lower()
            if any(keyword in budget_str for keyword in ['k', 'mil', 'thousand', 'million', '$', '€', 'euros', 'pesos']):
                score += 10
            else:
                score += 5
        
        # INFORMACIÓN DE UBICACIÓN (5 puntos) - Menos crítico
        if prospect.location: score += 5
        
        # PAIN POINTS ACUMULADOS (20 puntos) - Contar desde las notas
        pain_points_count = self._count_pain_points_from_notes(prospect.notes)
        if pain_points_count >= 3:
            score += 20
        elif pain_points_count >= 2:
            score += 15
        elif pain_points_count >= 1:
            score += 10
        
        # ENGAGEMENT Y NECESIDADES (15 puntos)
        if extracted_data.get('decision_maker') or 'decision_maker' in str(prospect.notes):
            score += 10
        
        if extracted_data.get('needs') or 'Necesidades:' in str(prospect.notes):
            score += 5
        
        # PROFUNDIDAD DE CONVERSACIÓN (20 puntos) - MEJORADO
        conversation_depth = self._calculate_conversation_depth_improved(prospect, extracted_data)
        score += conversation_depth
        
        # ASEGURAR QUE SIEMPRE SEA UN ENTERO
        final_score = int(min(score, 100))
        
        print(f"🎯 Score calculado: {final_score} para prospect {prospect.name}")
        print(f"   📊 Breakdown detallado:")
        print(f"   - Básico: {10 if prospect.name else 0} + {10 if prospect.company else 0} + {10 if prospect.industry else 0} = {(10 if prospect.name else 0) + (10 if prospect.company else 0) + (10 if prospect.industry else 0)}")
        print(f"   - Pain points: {pain_points_count} = {20 if pain_points_count >= 3 else 15 if pain_points_count >= 2 else 10 if pain_points_count >= 1 else 0} puntos")
        print(f"   - Engagement: {10 if extracted_data.get('decision_maker') or 'decision_maker' in str(prospect.notes) else 0} + {5 if extracted_data.get('needs') or 'Necesidades:' in str(prospect.notes) else 0} = {(10 if extracted_data.get('decision_maker') or 'decision_maker' in str(prospect.notes) else 0) + (5 if extracted_data.get('needs') or 'Necesidades:' in str(prospect.notes) else 0)}")
        print(f"   - Conversación: {conversation_depth} puntos")
        
        return final_score
    
    def _count_pain_points_from_notes(self, notes: str) -> int:
        """Cuenta pain points únicos desde las notas"""
        if not notes:
            return 0
        
        # Contar líneas únicas que contengan "Pain point:"
        pain_lines = [line.strip() for line in notes.split('\n') if 'Pain point:' in line]
        unique_pain_points = set(pain_lines)  # Eliminar duplicados
        
        return len(unique_pain_points)
    
    def _calculate_conversation_depth_improved(self, prospect: Prospect, extracted_data: Dict[str, Any]) -> int:
        """Calcula la profundidad de la conversación - MEJORADO"""
        depth_score = 0
        notes = str(prospect.notes) if prospect.notes else ""
        
        # Longitud de notas (más generoso)
        notes_length = len(notes)
        if notes_length > 300:
            depth_score += 15
        elif notes_length > 200:
            depth_score += 12
        elif notes_length > 100:
            depth_score += 8
        elif notes_length > 50:
            depth_score += 5
        
        # Diversidad de información
        info_types = 0
        if 'Necesidades:' in notes: info_types += 1
        if 'Pain point:' in notes: info_types += 1
        if 'Canal:' in notes: info_types += 1
        if 'Timeline:' in notes: info_types += 1
        
        depth_score += info_types * 2  # 2 puntos por cada tipo de información
        
        # Indicadores de interés alto
        interest_indicators = [
            'interesa', 'me gustaria', 'podria', 'quiero', 'necesito', 
            'factible', 'posible', 'conversacion', 'reunión', 'agendar'
        ]
        
        for indicator in interest_indicators:
            if indicator in notes.lower():
                depth_score += 3
                break  # Solo contar una vez
        
        print(f"   🔍 Conversation depth: notes_length={notes_length}, info_types={info_types}, depth_score={min(depth_score, 20)}")
        
        return min(depth_score, 20)  # Máximo 20 puntos
    
    def _safe_score_conversion(self, score_value) -> int:
        """Convierte cualquier valor a int de forma segura"""
        if score_value is None:
            return 0
        
        if isinstance(score_value, int):
            return score_value
        
        if isinstance(score_value, str):
            try:
                return int(float(score_value))
            except (ValueError, TypeError):
                return 0
        
        if isinstance(score_value, float):
            return int(score_value)
        
        return 0
    
    def is_qualified(self, prospect: Prospect) -> bool:
        """Determina si un prospecto está calificado - UMBRAL AJUSTADO"""
        score = self._safe_score_conversion(prospect.qualification_score)
        qualified = score >= 65  # BAJADO DE 75 A 65 - más realista
        print(f"📊 Qualification check: score={score}, qualified={qualified} (umbral: 65)")
        return qualified
    
    def should_send_meeting_link(self, prospect: Prospect) -> bool:
        """Determina si se debe enviar el link de reunión - CRITERIOS AJUSTADOS"""
        score = self._safe_score_conversion(prospect.qualification_score)
        meeting_sent = getattr(prospect, 'meeting_link_sent', False) or False
        has_name = bool(prospect.name)
        has_company = bool(prospect.company)
        has_industry = bool(prospect.industry)
        
        # Verificar profundidad de conversación (más permisivo)
        conversation_depth = self._check_conversation_depth_improved(prospect)
        
        should_send = (
            score >= 65 and           # BAJADO DE 75 A 65
            not meeting_sent and
            has_name and 
            has_company and
            has_industry and
            conversation_depth        # Verificación mejorada
        )
        
        print(f"🔗 Meeting link check: score={score}, sent={meeting_sent}, name={has_name}, company={has_company}, industry={has_industry}, depth={conversation_depth}, should_send={should_send}")
        return should_send
    
    def _check_conversation_depth_improved(self, prospect: Prospect) -> bool:
        """Verifica profundidad de conversación - MÁS PERMISIVO"""
        if not prospect.notes:
            return False
            
        notes = str(prospect.notes)
        
        # Contar diferentes tipos de información
        pain_point_count = notes.count('Pain point:')
        needs_count = notes.count('Necesidades:')
        channel_count = notes.count('Canal:')
        
        # Indicadores de interés
        interest_words = ['interesa', 'gustaria', 'podria', 'quiero', 'necesito', 'factible', 'posible']
        interest_count = sum(1 for word in interest_words if word in notes.lower())
        
        # Criterios más permisivos
        has_basic_info = pain_point_count >= 1 and needs_count >= 1
        has_sufficient_length = len(notes) >= 100
        has_interest = interest_count >= 2
        
        depth_ok = (has_basic_info and has_sufficient_length) or has_interest
        
        print(f"🔍 Conversation depth check IMPROVED:")
        print(f"   - Notes length: {len(notes)}")
        print(f"   - Pain points: {pain_point_count}")
        print(f"   - Needs: {needs_count}")
        print(f"   - Interest indicators: {interest_count}")
        print(f"   - Has basic info: {has_basic_info}")
        print(f"   - Has sufficient length: {has_sufficient_length}")
        print(f"   - Has interest: {has_interest}")
        print(f"   - Depth OK: {depth_ok}")
        
        return depth_ok
    
    def add_note(self, prospect_id: int, note: str) -> bool:
        """Agrega una nota específica al prospecto"""
        prospect = self.db.get_prospect(prospect_id)
        if not prospect:
            return False
            
        existing_notes = prospect.notes or ""
        timestamp = "• "
        new_note = f"{timestamp}{note}"
        
        if existing_notes:
            prospect.notes = existing_notes + "\n" + new_note
        else:
            prospect.notes = new_note
            
        return self.db.update_prospect(prospect)
    
    def should_improve_notes(self, prospect: Prospect) -> bool:
        """Determina si las notas deben mejorarse con IA"""
        if not prospect.notes:
            return False
        
        notes = str(prospect.notes)
        
        # Criterios para mejorar:
        # 1. Más de 150 caracteres
        # 2. Múltiples líneas
        # 3. Al menos 3 tipos de información diferentes
        
        has_length = len(notes) > 150
        has_multiple_lines = notes.count('\n') >= 3
        
        info_types = 0
        if 'Pain point:' in notes: info_types += 1
        if 'Necesidades:' in notes: info_types += 1
        if 'Canal:' in notes: info_types += 1
        if '•' in notes: info_types += 1
        
        has_diversity = info_types >= 3
        
        should_improve = has_length and has_multiple_lines and has_diversity
        
        print(f"📝 Should improve notes: length={has_length}, lines={has_multiple_lines}, diversity={has_diversity}, result={should_improve}")
        
        return should_improve