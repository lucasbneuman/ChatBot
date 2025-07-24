# agents/app/database/prospect_db_fixed.py
import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum

class LeadStatus(Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    CLOSED = "closed"
    MEETING_SENT = "meeting_sent"

@dataclass
class Prospect:
    id: Optional[int] = None
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    budget: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    notes: Optional[str] = None  # Solo resúmenes
    status: str = LeadStatus.NEW.value
    qualification_score: int = 0
    meeting_date: Optional[str] = None
    meeting_link_sent: bool = False
    brevo_contact_id: Optional[str] = None
    conversation_history: str = "[]"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario con validación de tipos"""
        return {
            "id": self.id,
            "name": self._safe_string(self.name),
            "company": self._safe_string(self.company),
            "email": self._safe_string(self.email),
            "budget": self._safe_string(self.budget),
            "location": self._safe_string(self.location),
            "industry": self._safe_string(self.industry),
            "notes": self._safe_string(self.notes),
            "status": self._safe_string(self.status),
            "qualification_score": self._safe_int(self.qualification_score),
            "meeting_date": self._safe_string(self.meeting_date),
            "meeting_link_sent": self._safe_bool(self.meeting_link_sent),
            "brevo_contact_id": self._safe_string(self.brevo_contact_id),
            "conversation_history": self._safe_string(self.conversation_history),
            "created_at": self._safe_string(self.created_at),
            "updated_at": self._safe_string(self.updated_at)
        }
    
    def _safe_string(self, value: Any) -> Optional[str]:
        """Convierte a string de manera segura"""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return str(value)
    
    def _safe_int(self, value: Any) -> int:
        """Convierte a int de manera segura"""
        if value is None:
            return 0
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return 0
        return 0
    
    def _safe_bool(self, value: Any) -> bool:
        """Convierte a bool de manera segura"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        if isinstance(value, int):
            return bool(value)
        return False

class ProspectDatabaseFixed:
    def __init__(self, db_path: str = "prospects_fixed.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos con estructura limpia"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Crear tabla limpia con tipos específicos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prospects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                company TEXT,
                email TEXT,
                budget TEXT,
                location TEXT,
                industry TEXT,
                notes TEXT,
                status TEXT DEFAULT 'new',
                qualification_score INTEGER DEFAULT 0,
                meeting_date TEXT,
                meeting_link_sent BOOLEAN DEFAULT FALSE,
                brevo_contact_id TEXT,
                conversation_history TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Crear tabla de conversaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prospect_id INTEGER,
                message TEXT NOT NULL,
                sender TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prospect_id) REFERENCES prospects (id)
            )
        ''')
        
        # Crear índices para mejor rendimiento
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prospect_email ON prospects(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prospect_status ON prospects(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_prospect ON conversations(prospect_id)')
        
        conn.commit()
        conn.close()
    
    def create_prospect(self, prospect: Prospect) -> int:
        """Crea un nuevo prospecto con validación estricta"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Validar y limpiar datos antes de insertar
            data = (
                self._clean_string(prospect.name),
                self._clean_string(prospect.company),
                self._clean_email(prospect.email),
                self._clean_string(prospect.budget),
                self._clean_string(prospect.location),
                self._clean_string(prospect.industry),
                self._clean_notes(prospect.notes),
                self._clean_status(prospect.status),
                self._clean_int(prospect.qualification_score),
                self._clean_string(prospect.meeting_date),
                self._clean_bool(prospect.meeting_link_sent),
                self._clean_string(prospect.brevo_contact_id),
                self._clean_json(prospect.conversation_history)
            )
            
            cursor.execute('''
                INSERT INTO prospects (
                    name, company, email, budget, location, industry, notes, status,
                    qualification_score, meeting_date, meeting_link_sent, 
                    brevo_contact_id, conversation_history
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', data)
            
            prospect_id = cursor.lastrowid
            conn.commit()
            return prospect_id
            
        except Exception as e:
            print(f"Error creando prospecto: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_prospect(self, prospect_id: int) -> Optional[Prospect]:
        """Obtiene un prospecto por ID con validación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM prospects WHERE id = ?', (prospect_id,))
            row = cursor.fetchone()
            
            if row:
                return Prospect(
                    id=row[0],
                    name=self._safe_extract_string(row[1]),
                    company=self._safe_extract_string(row[2]),
                    email=self._safe_extract_string(row[3]),
                    budget=self._safe_extract_string(row[4]),
                    location=self._safe_extract_string(row[5]),
                    industry=self._safe_extract_string(row[6]),
                    notes=self._safe_extract_string(row[7]),
                    status=self._safe_extract_string(row[8], "new"),
                    qualification_score=self._safe_extract_int(row[9]),
                    meeting_date=self._safe_extract_string(row[10]),
                    meeting_link_sent=self._safe_extract_bool(row[11]),
                    brevo_contact_id=self._safe_extract_string(row[12]),
                    conversation_history=self._safe_extract_string(row[13], "[]"),
                    created_at=self._safe_extract_string(row[14]),
                    updated_at=self._safe_extract_string(row[15])
                )
            return None
            
        except Exception as e:
            print(f"Error obteniendo prospecto {prospect_id}: {e}")
            return None
        finally:
            conn.close()
    
    def update_prospect(self, prospect: Prospect) -> bool:
        """Actualiza un prospecto con validación estricta"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            data = (
                self._clean_string(prospect.name),
                self._clean_string(prospect.company),
                self._clean_email(prospect.email),
                self._clean_string(prospect.budget),
                self._clean_string(prospect.location),
                self._clean_string(prospect.industry),
                self._clean_notes(prospect.notes),
                self._clean_status(prospect.status),
                self._clean_int(prospect.qualification_score),
                self._clean_string(prospect.meeting_date),
                self._clean_bool(prospect.meeting_link_sent),
                self._clean_string(prospect.brevo_contact_id),
                self._clean_json(prospect.conversation_history),
                prospect.id
            )
            
            cursor.execute('''
                UPDATE prospects SET
                    name=?, company=?, email=?, budget=?, location=?, industry=?, 
                    notes=?, status=?, qualification_score=?, meeting_date=?, 
                    meeting_link_sent=?, brevo_contact_id=?, conversation_history=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            ''', data)
            
            success = cursor.rowcount > 0
            conn.commit()
            return success
            
        except Exception as e:
            print(f"Error actualizando prospecto {prospect.id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def add_conversation_message(self, prospect_id: int, message: str, sender: str) -> bool:
        """Añade un mensaje a la conversación con validación"""
        if not message or not sender or not prospect_id:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO conversations (prospect_id, message, sender)
                VALUES (?, ?, ?)
            ''', (prospect_id, str(message)[:2000], str(sender)[:50]))  # Limitar longitud
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error añadiendo mensaje de conversación: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_conversation_history(self, prospect_id: int) -> List[Dict[str, Any]]:
        """Obtiene el historial de conversación con validación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT message, sender, timestamp 
                FROM conversations 
                WHERE prospect_id = ? 
                ORDER BY timestamp ASC
            ''', (prospect_id,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'message': str(row[0]) if row[0] else "",
                    'sender': str(row[1]) if row[1] else "unknown", 
                    'timestamp': str(row[2]) if row[2] else ""
                })
            
            return messages
            
        except Exception as e:
            print(f"Error obteniendo historial de conversación: {e}")
            return []
        finally:
            conn.close()
    
    # Métodos de limpieza y validación
    def _clean_string(self, value: Any) -> Optional[str]:
        """Limpia y valida strings"""
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned if cleaned else None
        return str(value).strip() if str(value).strip() else None
    
    def _clean_email(self, value: Any) -> Optional[str]:
        """Limpia y valida emails"""
        if not value:
            return None
        
        email_str = str(value).strip().lower()
        
        # Validación básica de email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if re.match(email_pattern, email_str):
            return email_str
        
        return None
    
    def _clean_notes(self, value: Any) -> Optional[str]:
        """Limpia notas eliminando datos corruptos"""
        if not value:
            return None
        
        notes_str = str(value).strip()
        
        # Filtrar líneas que parecen datos corruptos
        lines = notes_str.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            # Saltar líneas que parecen timestamps o datos corruptos
            if (line and 
                not line.startswith('2025-') and 
                not line.isdigit() and
                len(line) > 3):
                clean_lines.append(line)
        
        return '\n'.join(clean_lines) if clean_lines else None
    
    def _clean_status(self, value: Any) -> str:
        """Limpia y valida status"""
        if not value:
            return LeadStatus.NEW.value
        
        status_str = str(value).strip().lower()
        
        # Verificar que sea un status válido
        valid_statuses = [status.value for status in LeadStatus]
        
        if status_str in valid_statuses:
            return status_str
        
        return LeadStatus.NEW.value
    
    def _clean_int(self, value: Any) -> int:
        """Limpia y valida enteros"""
        if value is None:
            return 0
        
        if isinstance(value, int):
            return max(0, min(value, 100))  # Score entre 0-100
        
        if isinstance(value, str):
            try:
                num = int(float(value))
                return max(0, min(num, 100))
            except (ValueError, TypeError):
                return 0
        
        return 0
    
    def _clean_bool(self, value: Any) -> bool:
        """Limpia y valida booleanos"""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        
        if isinstance(value, int):
            return bool(value)
        
        return False
    
    def _clean_json(self, value: Any) -> str:
        """Limpia y valida JSON"""
        if not value:
            return "[]"
        
        if isinstance(value, str):
            try:
                # Intentar parsear para validar
                parsed = json.loads(value)
                return json.dumps(parsed)  # Re-serializar limpio
            except (json.JSONDecodeError, TypeError):
                return "[]"
        
        try:
            return json.dumps(value)
        except (TypeError, ValueError):
            return "[]"
    
    def _safe_extract_string(self, value: Any, default: str = None) -> Optional[str]:
        """Extrae string de manera segura de la DB"""
        if value is None:
            return default
        
        return str(value).strip() if str(value).strip() else default
    
    def _safe_extract_int(self, value: Any, default: int = 0) -> int:
        """Extrae int de manera segura de la DB"""
        if value is None:
            return default
        
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def _safe_extract_bool(self, value: Any, default: bool = False) -> bool:
        """Extrae bool de manera segura de la DB"""
        if value is None:
            return default
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, int):
            return bool(value)
        
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        
        return default