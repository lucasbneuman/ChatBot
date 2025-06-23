import os
from typing import TypedDict
from typing_extensions import Annotated
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI


# Cargar variables de entorno
load_dotenv()

class ChatAgent:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self._validate_api_key()
        self._setup_agent()
    
    def _validate_api_key(self):
        """Valida que la API key esté configurada"""
        if self.openai_api_key:
            print(f"✅ OpenAI API Key detectada: {self.openai_api_key[:8]}********")
        else:
            raise EnvironmentError("❌ OPENAI_API_KEY no está configurada en el archivo .env")
    
    def _setup_agent(self):
        """Configura el agente de LangGraph"""
        # Mensaje de sistema
        self.system_message = {"role": "system", "content": "Eres un asistente útil."}
        
        # Tipo de estado LangGraph
        class State(TypedDict):
            messages: Annotated[list, add_messages]
        
        self.State = State
        
        # Inicializar modelo
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, max_tokens=100)
        
        # Construcción del grafo
        builder = StateGraph(State)
        builder.add_node("chatbot", self._chatbot_node)
        builder.set_entry_point("chatbot")
        builder.set_finish_point("chatbot")
        
        self.graph = builder.compile()

    
    def _chatbot_node(self, state):
        """Nodo principal del grafo"""
        full_messages = [self.system_message] + state["messages"]
        response = self.llm.invoke(full_messages)
        return {"messages": [response]}
    
    def chat(self, user_input: str, thread_id: str = "user-1") -> str:
        """Función principal para chatear con memoria"""
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            result = self.graph.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config
            )
            return result["messages"][-1].content
        except Exception as e:
            print(f"Error en chat: {e}")
            return f"Error: {str(e)}"
        
# Crear una instancia del agente y obtener el grafo
agent_instance = ChatAgent()
graph = agent_instance.graph


""" Si ANDA
import os
from typing import TypedDict
from typing_extensions import Annotated
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
import gradio as gr

# Cargar variables de entorno
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if openai_api_key:
    print(f"✅ OpenAI API Key detectada: {openai_api_key[:8]}********")
else:
    raise EnvironmentError("❌ OPENAI_API_KEY no está configurada en el archivo .env")

# Mensaje de sistema
system_message = {"role": "system", "content": "Eres un asistente útil."}

# Tipo de estado LangGraph
class State(TypedDict):
    messages: Annotated[list, add_messages]

# Inicializar modelo
llm = ChatOpenAI(model="gpt-4o", temperature=0.7, max_tokens=200)

# Nodo principal del grafo
def chatbot(state: State) -> dict:
    full_messages = [system_message] + state["messages"]
    response = llm.invoke(full_messages)
    return {"messages": [response]}

# Construcción del grafo
builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.set_entry_point("chatbot")
builder.set_finish_point("chatbot")

# Persistencia de memoria
memory = MemorySaver()

# Compilar el grafo
graph = builder.compile(checkpointer=memory)

# Función principal con memoria - CORREGIDA
def chat_with_memory(message, history, thread_id: str = "user-1"):
    # Configuración corregida - thread_id debe ser string, no lista
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        result = graph.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config=config
        )
        return result["messages"][-1].content
    except Exception as e:
        print(f"Error en chat_with_memory: {e}")
        return f"Error: {str(e)}"

# Interfaz Gradio - CORREGIDA
chat_ui = gr.ChatInterface(
    fn=chat_with_memory,
    chatbot=gr.Chatbot(height=500),  # Removido type="messages" que puede causar conflictos
    title="🤖 Chat",
    description="Un asistente útil.",
    submit_btn="Enviar"
)

if __name__ == "__main__":
    chat_ui.launch(share=True)
    """