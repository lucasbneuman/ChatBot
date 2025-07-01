# agents/test/test_prospecting_agent.py
import pytest
import os
import tempfile
from unittest.mock import Mock, patch
from app.agents.prospecting_agent import ProspectingAgent
from app.database.prospect_db import ProspectDatabase, Prospect

class TestProspectingAgent:
    
    @pytest.fixture
    def temp_db(self):
        """Crea una base de datos temporal para pruebas"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = ProspectDatabase(db_path)
        yield db_path
        
        # Limpiar
        os.unlink(db_path)
    
    @pytest.fixture
    def mock_agent(self, temp_db):
        """Crea un agente mock para pruebas"""
        with patch('app.agents.prospecting_agent.ChatOpenAI') as mock_llm:
            agent = ProspectingAgent("fake-api-key", temp_db)
            yield agent
    
    def test_create_prospect(self, temp_db):
        """Prueba creación de prospecto"""
        db = ProspectDatabase(temp_db)
        
        prospect = Prospect(
            name="Juan Pérez",
            company="TechCorp",
            industry="Tecnología"
        )
        
        prospect_id = db.create_prospect(prospect)
        assert prospect_id is not None
        
        retrieved = db.get_prospect(prospect_id)
        assert retrieved.name == "Juan Pérez"
        assert retrieved.company == "TechCorp"
    
    def test_update_prospect(self, temp_db):
        """Prueba actualización de prospecto"""
        db = ProspectDatabase(temp_db)
        
        # Crear prospecto
        prospect = Prospect(name="Ana García")
        prospect_id = db.create_prospect(prospect)
        
        # Actualizar
        prospect.id = prospect_id
        prospect.company = "StartupXYZ"
        prospect.budget = "$50,000"
        
        success = db.update_prospect(prospect)
        assert success
        
        # Verificar actualización
        updated = db.get_prospect(prospect_id)
        assert updated.company == "StartupXYZ"
        assert updated.budget == "$50,000"
    
    def test_conversation_history(self, temp_db):
        """Prueba historial de conversación"""
        db = ProspectDatabase(temp_db)
        
        # Crear prospecto
        prospect = Prospect()
        prospect_id = db.create_prospect(prospect)
        
        # Agregar mensajes
        db.add_conversation_message(prospect_id, "Hola, me interesa su producto", "user")
        db.add_conversation_message(prospect_id, "¡Excelente! Cuéntame más sobre tu empresa", "assistant")
        
        # Obtener historial
        history = db.get_conversation_history(prospect_id)
        
        assert len(history) == 2
        assert history[0]['message'] == "Hola, me interesa su producto"
        assert history[0]['sender'] == "user"
        assert history[1]['sender'] == "assistant"
    
    @patch('app.agents.prospecting_agent.ChatOpenAI')
    def test_message_processing(self, mock_llm, temp_db):
        """Prueba procesamiento de mensajes"""
        # Configurar mock
        mock_llm_instance = Mock()
        mock_llm.return_value = mock_llm_instance
        
        # Mock para clasificación de intención
        mock_response = Mock()
        mock_response.content = "GREETING"
        mock_llm_instance.invoke.return_value = mock_response
        
        agent = ProspectingAgent("fake-api-key", temp_db)
        
        # Procesar mensaje
        result = agent.process_message("Hola, ¿cómo están?")
        
        assert "prospect_id" in result
        assert result["intent"] == "GREETING"
    
    def test_qualification_scoring(self, temp_db):
        """Prueba sistema de scoring"""
        from app.nodes.data_extractor import DataExtractor
        
        db = ProspectDatabase(temp_db)
        extractor = DataExtractor(db)
        
        # Crear prospecto con información completa
        prospect = Prospect(
            name="Carlos Rodríguez",
            company="InnovaCorp", 
            budget="$100,000",
            location="México",
            industry="Fintech"
        )
        prospect_id = db.create_prospect(prospect)
        
        # Datos extraídos simulados
        extracted_data = {
            "pain_points": ["escalabilidad", "costos"],
            "decision_maker": True
        }
        
        # Actualizar con scoring
        extractor.update_prospect_data(prospect_id, extracted_data)
        
        # Verificar scoring
        updated_prospect = db.get_prospect(prospect_id)
        assert updated_prospect.qualification_score > 60  # Debería estar calificado
        assert extractor.is_qualified(updated_prospect)