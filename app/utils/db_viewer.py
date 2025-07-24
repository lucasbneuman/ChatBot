"""
Utilidad básica para visualizar la base de datos de clientes/prospectos.
Permite ver y verificar la información almacenada de manera clara.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

class DatabaseViewer:
    def __init__(self, db_path: str = None):
        """Inicializa el visualizador de base de datos."""
        if db_path is None:
            # Buscar la base de datos principal
            possible_paths = [
                Path("prospects.db"),
                Path("app/agents/prospects.db"),
                Path("../prospects.db")
            ]
            for path in possible_paths:
                if path.exists():
                    db_path = str(path)
                    break
            else:
                raise FileNotFoundError("No se encontró la base de datos de prospectos")
        
        self.db_path = db_path
        print(f"Conectando a base de datos: {db_path}")
    
    def get_connection(self):
        """Obtiene conexión a la base de datos."""
        return sqlite3.connect(self.db_path)
    
    def show_prospects_summary(self):
        """Muestra un resumen general de los prospectos."""
        with self.get_connection() as conn:
            # Estadísticas básicas
            total_prospects = pd.read_sql("SELECT COUNT(*) as total FROM prospects", conn).iloc[0]['total']
            
            # Distribución por estado
            status_dist = pd.read_sql("""
                SELECT status, COUNT(*) as count 
                FROM prospects 
                GROUP BY status 
                ORDER BY count DESC
            """, conn)
            
            # Prospectos por industria
            industry_dist = pd.read_sql("""
                SELECT industry, COUNT(*) as count 
                FROM prospects 
                WHERE industry IS NOT NULL AND industry != ''
                GROUP BY industry 
                ORDER BY count DESC
                LIMIT 10
            """, conn)
            
            print("="*50)
            print("RESUMEN DE BASE DE DATOS DE PROSPECTOS")
            print("="*50)
            print(f"Total de prospectos: {total_prospects}")
            print()
            
            print("DISTRIBUCIÓN POR ESTADO:")
            print("-"*30)
            for _, row in status_dist.iterrows():
                print(f"{row['status']:20} {row['count']:3}")
            print()
            
            if not industry_dist.empty:
                print("TOP INDUSTRIAS:")
                print("-"*30)
                for _, row in industry_dist.iterrows():
                    print(f"{row['industry']:20} {row['count']:3}")
                print()
    
    def show_recent_prospects(self, limit: int = 10):
        """Muestra los prospectos más recientes."""
        with self.get_connection() as conn:
            recent = pd.read_sql(f"""
                SELECT id, name, company, status, qualification_score, 
                       created_at, updated_at
                FROM prospects 
                ORDER BY created_at DESC 
                LIMIT {limit}
            """, conn)
            
            print("PROSPECTOS MÁS RECIENTES:")
            print("-"*80)
            if recent.empty:
                print("No hay prospectos en la base de datos.")
                return
            
            for _, row in recent.iterrows():
                print(f"ID: {row['id']:3} | {row['name']:20} | {row['company']:15}")
                print(f"     Estado: {row['status']:15} | Score: {row['qualification_score']:3}")
                print(f"     Creado: {row['created_at']}")
                print("-"*80)
    
    def show_prospect_details(self, prospect_id: int):
        """Muestra detalles completos de un prospecto específico."""
        with self.get_connection() as conn:
            prospect = pd.read_sql("""
                SELECT * FROM prospects WHERE id = ?
            """, conn, params=(prospect_id,))
            
            if prospect.empty:
                print(f"No se encontró el prospecto con ID {prospect_id}")
                return
            
            row = prospect.iloc[0]
            print("="*60)
            print(f"DETALLES DEL PROSPECTO ID: {prospect_id}")
            print("="*60)
            
            print(f"Nombre:           {row['name']}")
            print(f"Empresa:          {row['company']}")
            print(f"Presupuesto:      {row['budget']}")
            print(f"Ubicación:        {row['location']}")
            print(f"Industria:        {row['industry']}")
            print(f"Estado:           {row['status']}")
            print(f"Score:            {row['qualification_score']}")
            print(f"Fecha reunión:    {row['meeting_date']}")
            print(f"Link enviado:     {row['meeting_link_sent']}")
            print(f"ID Brevo:         {row['brevo_contact_id']}")
            print(f"Creado:           {row['created_at']}")
            print(f"Actualizado:      {row['updated_at']}")
            
            if row['notes']:
                print(f"\nNotas:\n{row['notes']}")
            
            # Historial de conversaciones
            conversations = pd.read_sql("""
                SELECT message, sender, timestamp 
                FROM conversations 
                WHERE prospect_id = ? 
                ORDER BY timestamp
            """, conn, params=(prospect_id,))
            
            if not conversations.empty:
                print(f"\nHISTORIAL DE CONVERSACIONES ({len(conversations)} mensajes):")
                print("-"*50)
                for _, conv in conversations.iterrows():
                    print(f"[{conv['timestamp']}] {conv['sender']}: {conv['message'][:100]}...")
    
    def search_prospects(self, search_term: str):
        """Busca prospectos por nombre o empresa."""
        with self.get_connection() as conn:
            results = pd.read_sql("""
                SELECT id, name, company, status, qualification_score 
                FROM prospects 
                WHERE name LIKE ? OR company LIKE ?
                ORDER BY qualification_score DESC
            """, conn, params=(f"%{search_term}%", f"%{search_term}%"))
            
            if results.empty:
                print(f"No se encontraron prospectos con el término: {search_term}")
                return
            
            print(f"RESULTADOS DE BÚSQUEDA PARA: '{search_term}'")
            print("-"*60)
            for _, row in results.iterrows():
                print(f"ID: {row['id']:3} | {row['name']:20} | {row['company']:15}")
                print(f"     Estado: {row['status']:15} | Score: {row['qualification_score']:3}")
                print("-"*60)
    
    def show_all_prospects_table(self):
        """Muestra todos los prospectos en formato tabla."""
        with self.get_connection() as conn:
            prospects = pd.read_sql("""
                SELECT id, name, company, industry, status, qualification_score, 
                       budget, location, meeting_date, created_at
                FROM prospects 
                ORDER BY created_at DESC
            """, conn)
            
            if prospects.empty:
                print("No hay prospectos en la base de datos.")
                return
            
            print("\nTABLA COMPLETA DE PROSPECTOS:")
            print("="*120)
            
            # Configurar pandas para mostrar todas las columnas
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', 20)
            
            # Truncar campos largos para mejor visualización
            display_df = prospects.copy()
            display_df['name'] = display_df['name'].str[:15]
            display_df['company'] = display_df['company'].str[:15]
            display_df['industry'] = display_df['industry'].str[:12]
            display_df['status'] = display_df['status'].str[:10]
            display_df['budget'] = display_df['budget'].str[:10]
            display_df['location'] = display_df['location'].str[:12]
            display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d')
            
            print(display_df.to_string(index=False))
            print(f"\nTotal de prospectos: {len(prospects)}")

    def show_conversation_stats(self):
        """Muestra estadísticas de conversaciones."""
        with self.get_connection() as conn:
            stats = pd.read_sql("""
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(DISTINCT prospect_id) as prospects_with_conversations,
                    sender,
                    COUNT(*) as messages_by_sender
                FROM conversations 
                GROUP BY sender
            """, conn)
            
            total_conversations = pd.read_sql("SELECT COUNT(*) as total FROM conversations", conn).iloc[0]['total']
            
            print("ESTADÍSTICAS DE CONVERSACIONES:")
            print("-"*40)
            print(f"Total mensajes: {total_conversations}")
            
            if not stats.empty:
                print("\nMensajes por remitente:")
                for _, row in stats.iterrows():
                    print(f"{row['sender']:15} {row['messages_by_sender']:5}")


def main():
    """Función principal para ejecutar el visualizador."""
    try:
        viewer = DatabaseViewer()
        
        while True:
            print("\n" + "="*60)
            print("VISUALIZADOR DE BASE DE DATOS DE PROSPECTOS")
            print("="*60)
            print("1. Resumen general")
            print("2. Prospectos recientes")
            print("3. Ver detalles de prospecto (por ID)")
            print("4. Buscar prospecto")
            print("5. Estadísticas de conversaciones")
            print("6. Tabla completa de prospectos")
            print("0. Salir")
            print("-"*60)
            
            try:
                option = input("Selecciona una opción: ").strip()
                
                if option == "0":
                    break
                elif option == "1":
                    viewer.show_prospects_summary()
                elif option == "2":
                    limit = input("¿Cuántos mostrar? (default 10): ").strip()
                    limit = int(limit) if limit.isdigit() else 10
                    viewer.show_recent_prospects(limit)
                elif option == "3":
                    prospect_id = input("ID del prospecto: ").strip()
                    if prospect_id.isdigit():
                        viewer.show_prospect_details(int(prospect_id))
                    else:
                        print("Por favor ingresa un ID válido")
                elif option == "4":
                    search_term = input("Término de búsqueda (nombre o empresa): ").strip()
                    if search_term:
                        viewer.search_prospects(search_term)
                elif option == "5":
                    viewer.show_conversation_stats()
                elif option == "6":
                    viewer.show_all_prospects_table()
                else:
                    print("Opción no válida")
                
                input("\nPresiona Enter para continuar...")
                
            except KeyboardInterrupt:
                print("\n\nSaliendo...")
                break
            except Exception as e:
                print(f"Error: {e}")
                input("Presiona Enter para continuar...")
    
    except Exception as e:
        print(f"Error al inicializar el visualizador: {e}")


if __name__ == "__main__":
    main()