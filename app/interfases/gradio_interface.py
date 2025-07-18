import gradio as gr
import uuid
from app.agents.prospecting_agent import ChatAgent




class ChatInterface:
    def __init__(self):
        self.agent = ChatAgent()
        self._setup_interface()
    
    def _chat_wrapper(self, message, history, session_id):
        """Wrapper que conecta Gradio con el agente, usando memoria por sesión"""
        if session_id is None:
            session_id = str(uuid.uuid4())  # genera nuevo id único
        response = self.agent.chat(message, thread_id=session_id)
        history.append((message, response))  # formato tipo tuple (user, assistant)
        return "", history, session_id
    
    def _setup_interface(self):
        """Configura la interfaz de Gradio"""
        with gr.Blocks() as ui:
            session_id = gr.State(None)
            chatbot = gr.Chatbot(label="Asistente IA", height=500)
            msg_input = gr.Textbox(label="Escribe tu mensaje aquí...", placeholder="¿Qué puedo hacer por ti?", scale=7)
            
            msg_input.submit(
                fn=self._chat_wrapper,
                inputs=[msg_input, chatbot, session_id],
                outputs=[msg_input, chatbot, session_id],
            )
            
            self.chat_ui = ui
    
    def launch(self, share=True, debug=False):
        """Lanza la interfaz"""
        print("🚀 Iniciando interfaz de chat...")
        self.chat_ui.launch(share=share, debug=debug)


