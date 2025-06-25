# Agente Conversacional con Memoria

Este proyecto implementa un chatbot multiusuario con memoria de conversación, utilizando [LangGraph](https://github.com/langchain-ai/langgraph), [LangChain](https://github.com/langchain-ai/langchain), [OpenAI](https://platform.openai.com/), y una interfaz web con [Gradio](https://gradio.app/).

---

## 🚀 Características

- **Memoria por usuario:** Cada usuario tiene su propio historial de conversación.
- **Multiusuario:** Soporta múltiples sesiones simultáneas.
- **Interfaz web amigable:** Basada en Gradio.
- **Fácil de extender:** Puedes agregar nuevas funcionalidades fácilmente.

---

## ⚙️ Instalación

### 1. Clona el repositorio

```bash
git clone https://github.com/lucasbneuman/ChatBot.git
cd tu_repositorio
```

### 2. Crea el entorno

```bash
conda create -n agents python=3.11 -y
conda activate agents
conda env update -f environment.yml
```

O con pip:

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configura las variables de entorno

Crea un archivo `.env` en la raíz del proyecto con tu clave de OpenAI:

```
OPENAI_API_KEY=tu_clave_de_openai
```

---

## 🖥️ Uso

Ejecuta la interfaz web con:

```bash
python app/interface.py
```

Esto abrirá una interfaz web donde puedes chatear con el agente.

---

## 📁 Estructura del proyecto

```
app/
  ├── agent.py        # Lógica del agente conversacional
  ├── interface.py    # Interfaz web con Gradio
  └── ...
environment.yml      # Dependencias Conda
requirements.txt     # Dependencias pip
README.md            # Este archivo
```

---

## 📝 Notas

- El agente utiliza memoria por sesión, por lo que cada usuario tiene su propio contexto.
- Puedes cambiar el modelo de OpenAI en `agent.py` según tus necesidades.
- Si tienes problemas con la memoria, revisa que el `thread_id` sea único por usuario.

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Abre un issue o un pull request.

---

## 📄 Licencia

MIT

---

## ✨ Créditos

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [LangChain](https://github.com/langchain-ai/langchain)
- [Gradio](https://gradio.app/)
- [OpenAI](https://platform.openai.com/)