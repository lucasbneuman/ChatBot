# agents/test/test_prospecting_agent.py
import pytest
import os
import tempfile
import shutil
import json
from unittest.mock import MagicMock, patch
from agents.app.agents.prospecting_agent import ProspectingAgent
from agents.app.database.prospect_db import ProspectDatabase, Prospect

class TestProspectingAgent:
    
    @pytest.fixture
    def temp_db(self):
        """Crea una base de datos temporal para pruebas"""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")
        
        db = ProspectDatabase(db_path)
        yield db_path
        
        # Limpiar
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_llm(self):
        # Mock completo de ChatOpenAI
        mock = MagicMock()
        
        # Configurar comportamiento por defecto
        default_response = MagicMock()
        default_response.content = "GREETING"
        mock.invoke.return_value = default_response
        
        return mock
    
    @pytest.fixture
    def agent(self, temp_db, mock_llm):
        with patch('agents.app.agents.prospecting_agent.ChatOpenAI', return_value=mock_llm):
            agent = ProspectingAgent("fake-api-key", temp_db)
            
            # También mockear el LLM en los componentes internos
            agent.parser.llm = mock_llm
            agent.response_gen.llm = mock_llm
            
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

    def test_notes_handling(self, agent, mock_llm):
        """Prueba el manejo de notas adicionales"""
        # Configurar mock específico para handle_notes
        mock_response = MagicMock()
        mock_response.content = "nota"
        mock_llm.invoke.return_value = mock_response
        
        test_message = "Prefiero reuniones los miércoles por la tarde"
        
        # Procesar mensaje
        result = agent.process_message(test_message)
        assert result["prospect_id"] is not None

    def test_flexible_data_extraction(self, agent, mock_llm):
        """Prueba la extracción flexible de datos"""
        test_cases = [
            ("Soy de TechCorp", {"company": "TechCorp"}),
            ("Presupuesto 50k", {"budget": "50k"}),
            ("Trabajo en logística", {"industry": "logística"})
        ]
        
        for message, expected in test_cases:
            # Configurar mock para cada caso
            mock_response = MagicMock()
            mock_response.content = json.dumps(expected)
            mock_llm.invoke.return_value = mock_response
            
            entities = agent.parser.extract_entities(message)
            assert entities == expected, f"Fallo en {message}: esperado {expected}, obtenido {entities}"