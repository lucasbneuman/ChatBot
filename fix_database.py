# agents/fix_database.py
# Usar SOLO para arreglar bases de datos corruptas
# Este script elimina la base de datos corrupta y la recrea desde cero

import sqlite3
import os

def fix_corrupted_database():
    """Arregla la base de datos corrupta"""
    db_path = "prospects.db"
    
    # Borrar la DB corrupta
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️ Base de datos corrupta eliminada")
    
    # Recrear la DB limpia
    from app.database.prospect_db import ProspectDatabase
    db = ProspectDatabase(db_path)
    print("✅ Base de datos recreada correctamente")
    
    # Verificar estructura
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(prospects)")
    columns = cursor.fetchall()
    print("📊 Estructura de tabla prospects:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    conn.close()

if __name__ == "__main__":
    fix_corrupted_database()