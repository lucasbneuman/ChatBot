import gradio as gr
from agent import ChatAgent

class ChatInterface:
    def __init__(self):
        self.agent = ChatAgent()
        self._setup_interface()
    
    def _chat_wrapper(self, message, history, thread_id: str = "user-1"):
        """Wrapper para conectar Gradio con el agente"""
        return self.agent.chat(message, thread_id)
    
    def _setup_interface(self):
        """Configura la interfaz de Gradio"""
        self.chat_ui = gr.ChatInterface(
            fn=self._chat_wrapper,
            chatbot=gr.Chatbot(height=500),
            title="🤖 Chat",
            description="Un asistente útil.",
            submit_btn="Enviar"
        )
    
    def launch(self, share=True, debug=False):
        """Lanza la interfaz"""
        print("🚀 Iniciando interfaz de chat...")
        self.chat_ui.launch(share=share, debug=debug)