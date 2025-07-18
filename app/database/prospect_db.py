# agents/app/database/prospect_db.py
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
    MEETING_SENT = "meeting_sent"  # Nuevo estado

@dataclass
class Prospect:
    id: Optional[int] = None
    name: Optional[str] = None
    company: Optional[str] = None
    budget: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    notes: Optional[str] = None  # NUEVO CAMPO
    status: str = LeadStatus.NEW.value
    qualification_score: int = 0
    meeting_date: Optional[str] = None
    meeting_link_sent: bool = False  # NUEVO CAMPO
    brevo_contact_id: Optional[str] = None
    conversation_history: str = "[]"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ProspectDatabase:
    def __init__(self, db_path: str = "prospects.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos con las tablas necesarias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar si la tabla ya existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prospects'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            # Crear tabla nueva
            cursor.execute('''
                CREATE TABLE prospects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    company TEXT,
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
        else:
            # Agregar nuevas columnas si no existen
            try:
                cursor.execute('ALTER TABLE prospects ADD COLUMN notes TEXT')
            except sqlite3.OperationalError:
                pass  # La columna ya existe
            
            try:
                cursor.execute('ALTER TABLE prospects ADD COLUMN meeting_link_sent BOOLEAN DEFAULT FALSE')
            except sqlite3.OperationalError:
                pass  # La columna ya existe
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prospect_id INTEGER,
                message TEXT,
                sender TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prospect_id) REFERENCES prospects (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_prospect(self, prospect: Prospect) -> int:
        """Crea un nuevo prospecto"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO prospects (name, company, budget, location, industry, notes, status, 
                                 qualification_score, meeting_date, meeting_link_sent, brevo_contact_id, conversation_history)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prospect.name, prospect.company, prospect.budget, prospect.location,
            prospect.industry, prospect.notes, prospect.status, prospect.qualification_score,
            prospect.meeting_date, prospect.meeting_link_sent, prospect.brevo_contact_id, prospect.conversation_history
        ))
        
        prospect_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return prospect_id
    
    def get_prospect(self, prospect_id: int) -> Optional[Prospect]:
        """Obtiene un prospecto por ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM prospects WHERE id = ?', (prospect_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Prospect(
                id=row[0], name=row[1], company=row[2], budget=row[3],
                location=row[4], industry=row[5], notes=row[6], status=row[7],
                qualification_score=row[8], meeting_date=row[9],
                meeting_link_sent=row[10], brevo_contact_id=row[11], 
                conversation_history=row[12], created_at=row[13], updated_at=row[14]
            )
        return None
    
    def update_prospect(self, prospect: Prospect) -> bool:
        """Actualiza un prospecto"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE prospects 
            SET name=?, company=?, budget=?, location=?, industry=?, notes=?, status=?,
                qualification_score=?, meeting_date=?, meeting_link_sent=?, brevo_contact_id=?, 
                conversation_history=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            prospect.name, prospect.company, prospect.budget, prospect.location,
            prospect.industry, prospect.notes, prospect.status, prospect.qualification_score,
            prospect.meeting_date, prospect.meeting_link_sent, prospect.brevo_contact_id, 
            prospect.conversation_history, prospect.id
        ))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def add_conversation_message(self, prospect_id: int, message: str, sender: str):
        """Añade un mensaje a la conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations (prospect_id, message, sender)
            VALUES (?, ?, ?)
        ''', (prospect_id, message, sender))
        
        conn.commit()
        conn.close()
    
    def get_conversation_history(self, prospect_id: int) -> List[Dict[str, Any]]:
        """Obtiene el historial de conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message, sender, timestamp 
            FROM conversations 
            WHERE prospect_id = ? 
            ORDER BY timestamp ASC
        ''', (prospect_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'message': row[0],
                'sender': row[1],
                'timestamp': row[2]
            })
        
        conn.close()
        return messages