"""
Sistema de gestión de prompts con anotaciones LangGraph
"""
import os
import yaml
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from langchain.prompts import PromptTemplate
from langchain.schema import BaseMessage, SystemMessage, HumanMessage
from langchain_core.runnables import Runnable
from langchain_core.runnables.utils import Input, Output
import logging

logger = logging.getLogger(__name__)

class PromptManager:
    """
    Gestor centralizado de prompts con soporte para LangGraph Studio
    """
    
    def __init__(self, prompts_dir: str = None):
        self.prompts_dir = Path(prompts_dir) if prompts_dir else Path(__file__).parent.parent / "prompts"
        self.config_file = self.prompts_dir / "config.yaml"
        self.prompts_cache = {}
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración principal"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_file}")
            return {}
    
    def _load_prompt_file(self, filename: str) -> Dict[str, Any]:
        """Carga un archivo de prompt específico"""
        file_path = self.prompts_dir / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {file_path}")
            return {}
    
    def get_prompt(self, prompt_name: str, template_name: str = None) -> Dict[str, Any]:
        """
        Obtiene un prompt específico con cache
        """
        cache_key = f"{prompt_name}_{template_name or 'default'}"
        
        if cache_key in self.prompts_cache:
            return self.prompts_cache[cache_key]
        
        # Obtener configuración del prompt
        prompt_config = self.config.get('prompts', {}).get(prompt_name, {})
        if not prompt_config:
            logger.error(f"Prompt {prompt_name} not found in config")
            return {}
        
        # Cargar archivo del prompt
        prompt_file = prompt_config.get('file')
        if not prompt_file:
            logger.error(f"No file specified for prompt {prompt_name}")
            return {}
        
        prompt_data = self._load_prompt_file(prompt_file)
        
        # Cache del resultado
        self.prompts_cache[cache_key] = prompt_data
        return prompt_data
    
    def render_template(self, prompt_name: str, template_name: str = None, **kwargs) -> str:
        """
        Renderiza un template de prompt con variables
        """
        prompt_data = self.get_prompt(prompt_name, template_name)
        
        if not prompt_data:
            return ""
        
        # Para prompts simples (como intent_classifier, entity_extractor)
        if 'template' in prompt_data:
            template = prompt_data['template']
            # Renderizar con variables del prompt + kwargs
            variables = prompt_data.get('variables', {})
            all_vars = {**variables, **kwargs}
            return self._render_handlebars(template, all_vars)
        
        # Para prompts complejos con múltiples templates (como response_generator)
        if 'templates' in prompt_data:
            templates = prompt_data['templates']
            if template_name and template_name in templates:
                template_data = templates[template_name]
                template = template_data.get('template', '')
                variables = template_data.get('variables', {})
                all_vars = {**variables, **kwargs}
                return self._render_handlebars(template, all_vars)
        
        logger.error(f"Template {template_name} not found in prompt {prompt_name}")
        return ""
    
    def _render_handlebars(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Renderizador básico para templates estilo Handlebars
        """
        import re
        
        # Renderizar variables simples: {{variable}}
        def replace_simple(match):
            var_name = match.group(1)
            return str(variables.get(var_name, f"{{{{ {var_name} }}}}"))
        
        template = re.sub(r'\{\{\s*([^}]+)\s*\}\}', replace_simple, template)
        
        # Renderizar loops: {{#each array}}
        def replace_each(match):
            array_name = match.group(1)
            content = match.group(2)
            array_data = variables.get(array_name, [])
            
            if not isinstance(array_data, list):
                return ""
            
            result = ""
            for item in array_data:
                item_content = content
                if isinstance(item, dict):
                    for key, value in item.items():
                        item_content = item_content.replace(f"{{{{{key}}}}}", str(value))
                result += item_content
            
            return result
        
        template = re.sub(r'\{\{#each\s+([^}]+)\}\}(.*?)\{\{/each\}\}', replace_each, template, flags=re.DOTALL)
        
        # Renderizar condicionales: {{#if condition}}
        def replace_if(match):
            condition = match.group(1)
            content = match.group(2)
            
            if variables.get(condition.strip()):
                return content
            return ""
        
        template = re.sub(r'\{\{#if\s+([^}]+)\}\}(.*?)\{\{/if\}\}', replace_if, template, flags=re.DOTALL)
        
        return template
    
    def get_langraph_runnable(self, prompt_name: str, template_name: str = None) -> 'LangGraphPromptRunnable':
        """
        Crea un Runnable compatible con LangGraph Studio
        """
        return LangGraphPromptRunnable(
            prompt_manager=self,
            prompt_name=prompt_name,
            template_name=template_name
        )
    
    def get_prompt_metadata(self, prompt_name: str) -> Dict[str, Any]:
        """
        Obtiene metadatos del prompt para LangGraph Studio
        """
        prompt_data = self.get_prompt(prompt_name)
        return {
            'name': prompt_data.get('name', prompt_name),
            'version': prompt_data.get('version', '1.0'),
            'description': prompt_data.get('description', ''),
            'annotations': prompt_data.get('langraph_annotations', {}),
            'variables': prompt_data.get('variables', {}),
            'metadata': prompt_data.get('metadata', {})
        }
    
    def list_prompts(self) -> List[str]:
        """
        Lista todos los prompts disponibles
        """
        return list(self.config.get('prompts', {}).keys())
    
    def reload_cache(self):
        """
        Recarga el cache de prompts (útil para desarrollo)
        """
        self.prompts_cache.clear()
        self.config = self._load_config()
        logger.info("Prompt cache reloaded")


class LangGraphPromptRunnable(Runnable):
    """
    Runnable wrapper para prompts que es compatible con LangGraph Studio
    """
    
    def __init__(self, prompt_manager: PromptManager, prompt_name: str, template_name: str = None):
        self.prompt_manager = prompt_manager
        self.prompt_name = prompt_name
        self.template_name = template_name
        self.metadata = prompt_manager.get_prompt_metadata(prompt_name)
    
    def invoke(self, input: Input, config: Optional[Dict[str, Any]] = None) -> Output:
        """
        Ejecuta el prompt con las variables proporcionadas
        """
        # Extraer variables del input
        if isinstance(input, dict):
            variables = input
        else:
            variables = {'input': input}
        
        # Renderizar el template
        rendered = self.prompt_manager.render_template(
            self.prompt_name,
            self.template_name,
            **variables
        )
        
        return rendered
    
    def get_name(self) -> str:
        """Nombre del prompt para LangGraph Studio"""
        return self.metadata.get('name', self.prompt_name)
    
    def get_description(self) -> str:
        """Descripción del prompt para LangGraph Studio"""
        return self.metadata.get('description', '')
    
    def get_tags(self) -> List[str]:
        """Tags del prompt para LangGraph Studio"""
        annotations = self.metadata.get('annotations', {})
        return [annotations.get('tag', 'prompt')]
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Schema de entrada para LangGraph Studio"""
        variables = self.metadata.get('variables', {})
        return {
            'type': 'object',
            'properties': {
                key: {'type': 'string', 'description': f'Variable {key}'}
                for key in variables.keys()
            }
        }
    
    async def ainvoke(self, input: Input, config: Optional[Dict[str, Any]] = None) -> Output:
        """Versión async del invoke"""
        return self.invoke(input, config)


# Instancia global del gestor de prompts
prompt_manager = PromptManager()

# Funciones de conveniencia para uso fácil
def get_prompt(prompt_name: str, template_name: str = None, **kwargs) -> str:
    """Función de conveniencia para obtener un prompt renderizado"""
    return prompt_manager.render_template(prompt_name, template_name, **kwargs)

def get_runnable(prompt_name: str, template_name: str = None) -> LangGraphPromptRunnable:
    """Función de conveniencia para obtener un runnable"""
    return prompt_manager.get_langraph_runnable(prompt_name, template_name)

def reload_prompts():
    """Función de conveniencia para recargar prompts"""
    prompt_manager.reload_cache()