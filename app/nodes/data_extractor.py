# agents/app/nodes/data_extractor.py - SISTEMA DE SCORING CORREGIDO
import re
from typing import Dict, Any, Optional
from ..database.prospect_db_fixed import Prospect, ProspectDatabaseFixed

class DataExtractor:
    def __init__(self, db: ProspectDatabaseFixed):
        self.db = db
    
    def update_prospect_data(self, prospect_id: int, extracted_data: Dict[str, Any]) -> bool:
        """Actualiza los datos del prospecto con información extraída"""
        prospect = self.db.get_prospect(prospect_id)
        if not prospect:
            return False
        
        # Actualizar campos estructurados con nueva información (ahora permite actualización)
        if extracted_data.get('name'):
            prospect.name = self._update_field_with_better_data(prospect.name, extracted_data['name'])
        
        if extracted_data.get('company'):
            prospect.company = self._update_field_with_better_data(prospect.company, extracted_data['company'])
        
        if extracted_data.get('email'):
            prospect.email = self._update_field_with_better_data(prospect.email, extracted_data['email'])
        
        if extracted_data.get('budget'):
            prospect.budget = self._update_field_with_better_data(prospect.budget, extracted_data['budget'])
        
        if extracted_data.get('location'):
            prospect.location = self._update_field_with_better_data(prospect.location, extracted_data['location'])
        
        if extracted_data.get('industry'):
            prospect.industry = self._update_field_with_better_data(prospect.industry, extracted_data['industry'])
        
        # Actualizar SOLO notas de resumen (no datos estructurados)
        self._update_notes_summary_only(prospect, extracted_data)
        
        # Calcular score de calificación - SISTEMA MEJORADO
        prospect.qualification_score = self._calculate_qualification_score_improved(prospect, extracted_data)
        
        return self.db.update_prospect(prospect)
    
    def _update_field_with_better_data(self, current_value: str, new_value: str) -> str:
        """Actualiza un campo solo si la nueva información es mejor"""
        if not current_value:
            return new_value
        
        if not new_value:
            return current_value
        
        # Convertir a strings para comparación segura
        current_str = str(current_value).strip()
        new_str = str(new_value).strip()
        
        if not current_str:
            return new_str
        if not new_str:
            return current_str
        
        # Criterios para determinar si la nueva información es mejor
        
        # 1. La nueva es más larga y específica (contiene la actual como substring)
        if len(new_str) > len(current_str) and current_str.lower() in new_str.lower():
            return new_str
        
        # 2. La nueva tiene formato más profesional (nombre completo vs apodo o inicial)
        if " " in new_str and " " not in current_str and len(new_str) > len(current_str):
            return new_str
        
        # 3. La actual parece ser un apodo, abreviación o dato incorrecto
        if len(current_str) <= 3 and len(new_str) > 3:
            return new_str
        
        # 4. Mejorar capitalización (nombres propios)
        if new_str.istitle() and not current_str.istitle() and len(new_str) >= len(current_str):
            return new_str
        
        # 5. Casos específicos para nombres que parecen incorrectos
        # Si la actual parece ser un nombre de empresa/producto y la nueva un nombre de persona
        if self._seems_like_personal_name(new_str) and not self._seems_like_personal_name(current_str):
            return new_str
        
        # 6. Si la nueva información es sustancialmente diferente pero más detallada
        if len(new_str) > len(current_str) * 1.5 and " " in new_str:
            return new_str
        
        # Por defecto, mantener el valor actual
        return current_str
    
    def _seems_like_personal_name(self, text: str) -> bool:
        """Detecta si un texto parece ser un nombre personal"""
        if not text or len(text) < 2:
            return False
        
        # Patrones que sugieren nombre personal
        personal_patterns = [
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+$',  # Nombre Apellido
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+$',  # Nombre Apellido1 Apellido2
        ]
        
        for pattern in personal_patterns:
            if re.match(pattern, text):
                return True
        
        # Nombres comunes en español
        common_names = [
            'maria', 'jose', 'antonio', 'francisco', 'manuel', 'david', 'jose antonio',
            'jose luis', 'jesus', 'javier', 'fernando', 'daniel', 'miguel', 'rafael',
            'ana', 'carmen', 'dolores', 'maria carmen', 'josefa', 'isabel', 'antonia',
            'teresa', 'angela', 'francisca', 'cristina', 'laura', 'marta', 'elena'
        ]
        
        first_word = text.split()[0].lower() if ' ' in text else text.lower()
        return first_word in common_names
    
    def _update_notes_summary_only(self, prospect: Prospect, extracted_data: Dict[str, Any]) -> None:
        """Actualiza notas SOLO con resúmenes, no con datos estructurados"""
        existing_notes = prospect.notes or ""
        new_summary_notes = []
        
        # SOLO agregar información de resumen/contexto, NO datos estructurados
        if extracted_data.get('notes') and not self._is_structured_data(extracted_data['notes']):
            if extracted_data['notes'] not in existing_notes:
                new_summary_notes.append(f"• {extracted_data['notes']}")
        
        # Necesidades específicas (resumen de qué quiere, no el dato en sí)
        if extracted_data.get('needs'):
            needs_summary = f"Cliente busca: {extracted_data['needs']}"
            if needs_summary not in existing_notes:
                new_summary_notes.append(needs_summary)
        
        # Pain points (problemas específicos del cliente)        
        if extracted_data.get('pain_points'):
            pain_points = extracted_data['pain_points']
            if isinstance(pain_points, list):
                for pain in pain_points:
                    pain_summary = f"Problema: {pain}"
                    if pain_summary not in existing_notes:
                        new_summary_notes.append(pain_summary)
        
        # Timeline/urgencia (contexto del proyecto)
        if extracted_data.get('timeline'):
            timeline_summary = f"Timing: {extracted_data['timeline']}"
            if timeline_summary not in existing_notes:
                new_summary_notes.append(timeline_summary)
        
        # Agregar nuevas notas de resumen sin duplicar
        if new_summary_notes:
            if existing_notes:
                prospect.notes = existing_notes + "\n" + "\n".join(new_summary_notes)
            else:
                prospect.notes = "\n".join(new_summary_notes)
    
    def _is_structured_data(self, text: str) -> bool:
        """Detecta si un texto contiene datos estructurados que no deberían estar en notas"""
        if not text:
            return False
        
        # Patrones que indican datos estructurados
        structured_patterns = [
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+$',  # Nombre y apellido
            r'^[A-Z][a-z]+\s+(S\.A\.|SRL|LTDA)',  # Nombre de empresa
            r'\b\d+\s*(pesos|dolares|euros)\b',  # Montos
            r'\b[A-Z][a-z]+,\s+[A-Z][a-z]+\b',  # Ubicaciones
            r'^(tecnología|retail|restaurantes|consultoría|autopartes)$'  # Industrias
        ]
        
        for pattern in structured_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _calculate_qualification_score_improved(self, prospect: Prospect, extracted_data: Dict[str, Any]) -> int:
        """Calcula el puntaje de calificación - SISTEMA MEJORADO E INTELIGENTE"""
        score = 0
        
        # INFORMACIÓN BÁSICA (30 puntos)
        if prospect.name: score += 10
        if prospect.company: score += 10
        if prospect.industry: score += 10
        
        # INFORMACIÓN DE PRESUPUESTO (15 puntos) - Mejorado
        if prospect.budget: 
            budget_str = str(prospect.budget).lower()
            if any(keyword in budget_str for keyword in ['k', 'mil', 'thousand', 'million', '$', '€', 'euros', 'pesos']):
                score += 15  # Aumentado de 10 a 15
            else:
                score += 8   # Aumentado de 5 a 8
        
        # INFORMACIÓN DE UBICACIÓN (5 puntos) - Menos crítico
        if prospect.location: score += 5
        
        # PAIN POINTS ACUMULADOS (25 puntos) - Contar desde las notas
        pain_points_count = self._count_pain_points_from_notes(prospect.notes)
        if pain_points_count >= 3:
            score += 25  # Aumentado de 20 a 25
        elif pain_points_count >= 2:
            score += 18  # Aumentado de 15 a 18
        elif pain_points_count >= 1:
            score += 15  # Aumentado de 12 a 15
        
        # ENGAGEMENT Y NECESIDADES (18 puntos)
        if extracted_data.get('decision_maker') or 'decision_maker' in str(prospect.notes):
            score += 10
        
        if extracted_data.get('needs') or 'Cliente busca:' in str(prospect.notes):
            score += 12  # Aumentado de 8 a 12
        
        # PROFUNDIDAD DE CONVERSACIÓN (20 puntos) - MEJORADO
        conversation_depth = self._calculate_conversation_depth_improved(prospect, extracted_data)
        score += conversation_depth
        
        # ASEGURAR QUE SIEMPRE SEA UN ENTERO
        final_score = int(min(score, 100))
        
        print(f"DEBUG scoring for prospect:")
        print(f"   - Name: {bool(prospect.name)} (+10)")
        print(f"   - Company: {bool(prospect.company)} (+10)")
        print(f"   - Industry: {bool(prospect.industry)} (+10)")
        print(f"   - Budget: {bool(prospect.budget)} (+15)")
        print(f"   - Location: {bool(prospect.location)} (+5)")
        print(f"   - Pain points: {pain_points_count} (+{12 if pain_points_count >= 1 else 0})")
        print(f"   - Needs: {bool(extracted_data.get('needs') or 'Cliente busca:' in str(prospect.notes))} (+8)")
        print(f"   - Conversation depth: +{conversation_depth}")
        print(f"   - Final score: {final_score}")
        
        return final_score
    
    def _count_pain_points_from_notes(self, notes: str) -> int:
        """Cuenta pain points únicos desde las notas (actualizado para nuevo formato)"""
        if not notes:
            return 0
        
        # Contar líneas únicas que contengan "Problema:" (nuevo formato)
        pain_lines = [line.strip() for line in notes.split('\n') if 'Problema:' in line]
        unique_pain_points = set(pain_lines)  # Eliminar duplicados
        
        return len(unique_pain_points)
    
    def _calculate_conversation_depth_improved(self, prospect: Prospect, extracted_data: Dict[str, Any]) -> int:
        """Calcula la profundidad de la conversación - MEJORADO para nuevo formato"""
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
        
        # Diversidad de información (actualizado para nuevo formato)
        info_types = 0
        if 'Cliente busca:' in notes: info_types += 1
        if 'Problema:' in notes: info_types += 1
        if 'Canal:' in notes: info_types += 1
        if 'Timing:' in notes: info_types += 1
        
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
        
        # Conversation depth calculado
        
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
        qualified = score >= 60  # BAJADO DE 65 A 60 - aún más realista
        # Qualification check realizado
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
        
        # Criterio más permisivo - ser flexible con company
        should_send = (
            score >= 60 and                    # BAJADO DE 65 A 60
            not meeting_sent and
            (has_company or has_industry) and  # Empresa O industria clara
            conversation_depth                 # Verificación mejorada
        )
        
        # Bonus si tiene más datos, pero no es obligatorio
        if has_name and has_company:
            should_send = should_send  # Ya cumple los criterios
        
        print(f"DEBUG should_send_meeting_link details:")
        print(f"   - Score >= 65: {score >= 65} (score: {score})")
        print(f"   - Not meeting_sent: {not meeting_sent}")
        print(f"   - Has company: {has_company}")
        print(f"   - Has industry: {has_industry}")
        print(f"   - Conversation depth: {conversation_depth}")
        print(f"   - Final should_send: {should_send}")
        
        # Meeting link check realizado
        return should_send
    
    def _check_conversation_depth_improved(self, prospect: Prospect) -> bool:
        """Verifica profundidad de conversación - MÁS PERMISIVO con nuevo formato"""
        if not prospect.notes:
            return False
            
        notes = str(prospect.notes)
        
        # Contar diferentes tipos de información (actualizado para nuevo formato)
        problem_count = notes.count('Problema:')
        needs_count = notes.count('Cliente busca:')
        channel_count = notes.count('Canal:')
        timing_count = notes.count('Timing:')
        
        # Indicadores de interés
        interest_words = ['interesa', 'gustaria', 'podria', 'quiero', 'necesito', 'factible', 'posible']
        interest_count = sum(1 for word in interest_words if word in notes.lower())
        
        # Criterios más permisivos
        has_basic_info = problem_count >= 1 and needs_count >= 1
        has_sufficient_length = len(notes) >= 100
        has_interest = interest_count >= 2
        has_multiple_info_types = (problem_count + needs_count + channel_count + timing_count) >= 2
        
        depth_ok = (has_basic_info and has_sufficient_length) or has_interest or has_multiple_info_types
        
        # Conversation depth check improved
        
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
        if 'Problema:' in notes: info_types += 1
        if 'Cliente busca:' in notes: info_types += 1
        if 'Canal:' in notes: info_types += 1
        if 'Timing:' in notes: info_types += 1
        if '•' in notes: info_types += 1
        
        has_diversity = info_types >= 3
        
        should_improve = has_length and has_multiple_lines and has_diversity
        
        # Should improve notes check
        
        return should_improve