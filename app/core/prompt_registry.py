"""
Registro centralizado de prompts para LangGraph Studio
"""
from typing import Dict, Any, List
from .prompt_manager import prompt_manager, get_runnable
from langchain_core.runnables import Runnable

class PromptRegistry:
    """
    Registro centralizado que expone todos los prompts para LangGraph Studio
    """
    
    def __init__(self):
        self.runnables: Dict[str, Runnable] = {}
        self._register_all_prompts()
    
    def _register_all_prompts(self):
        """
        Registra todos los prompts disponibles como runnables
        """
        # Intent Classifier
        self.runnables['intent_classifier'] = get_runnable('intent_classifier')
        
        # Entity Extractor
        self.runnables['entity_extractor'] = get_runnable('entity_extractor')
        
        # Response Generator - diferentes templates
        self.runnables['response_initial'] = get_runnable('response_generator', 'initial_conversation')
        self.runnables['response_exploration'] = get_runnable('response_generator', 'exploration_conversation')
        self.runnables['response_deepening'] = get_runnable('response_generator', 'deepening_conversation')
        self.runnables['response_advanced'] = get_runnable('response_generator', 'advanced_conversation')
        self.runnables['response_post_meeting'] = get_runnable('response_generator', 'post_meeting_conversation')
        
        # Meeting Link Message
        self.runnables['meeting_link_message'] = get_runnable('response_generator', 'meeting_link_message')
        
        # Notes Improvement
        self.runnables['notes_improvement'] = get_runnable('response_generator', 'notes_improvement')
    
    def get_runnable(self, name: str) -> Runnable:
        """
        Obtiene un runnable por nombre
        """
        return self.runnables.get(name)
    
    def list_runnables(self) -> List[str]:
        """
        Lista todos los runnables disponibles
        """
        return list(self.runnables.keys())
    
    def get_all_runnables(self) -> Dict[str, Runnable]:
        """
        Obtiene todos los runnables para exposición en LangGraph
        """
        return self.runnables
    
    def add_custom_runnable(self, name: str, runnable: Runnable):
        """
        Añade un runnable personalizado al registro
        """
        self.runnables[name] = runnable
    
    def get_prompt_info(self, name: str) -> Dict[str, Any]:
        """
        Obtiene información detallada de un prompt para debugging
        """
        runnable = self.get_runnable(name)
        if not runnable:
            return {}
        
        if hasattr(runnable, 'metadata'):
            return runnable.metadata
        
        return {'name': name, 'type': 'custom_runnable'}

# Instancia global del registro
prompt_registry = PromptRegistry()

# Funciones de conveniencia
def get_registered_runnable(name: str) -> Runnable:
    """Obtiene un runnable registrado"""
    return prompt_registry.get_runnable(name)

def list_all_prompts() -> List[str]:
    """Lista todos los prompts disponibles"""
    return prompt_registry.list_runnables()

def get_all_prompt_runnables() -> Dict[str, Runnable]:
    """Obtiene todos los runnables para LangGraph"""
    return prompt_registry.get_all_runnables()