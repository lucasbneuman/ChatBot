# agents/README.md
# 🤖 Chatbot de Prospección Inteligente

Sistema automatizado de calificación de leads usando **LangGraph**, **Gradio** y **OpenAI GPT-4**.

## 🚀 Características Principales

- **Prospección Automatizada**: Contacta y califica leads automáticamente
- **Extracción de Datos IA**: Identifica información clave (nombre, empresa, presupuesto, etc.)
- **Sistema de Scoring**: Califica prospectos en base a criterios configurables
- **Memory Management**: Mantiene contexto de conversaciones con LangGraph
- **Interfaz Web**: UI amigable con Gradio para testing y demostración
- **Base de Datos**: Persistencia de datos con SQLite
- **Integración Brevo**: Ready para WhatsApp y email marketing

## 🛠️ Instalación

```bash
# Clonar repositorio
git clone <repository-url>
cd agents

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys
```

## ⚙️ Configuración

Edita el archivo `.env`:

```bash
OPENAI_API_KEY=tu_openai_api_key_aqui
BREVO_API_KEY=tu_brevo_api_key_aqui  
DATABASE_URL=sqlite:///./prospects.db
```

## 🏃‍♂️ Uso Rápido

### Prueba Rápida (Terminal)
```bash
python quick_start.py
```

### Interfaz Web
```bash
python main.py
```
Abre http://localhost:7860 en tu navegador.

### Ejemplo de Conversación

```
👤 Usuario: Hola, me interesa conocer sus servicios
🤖 Bot: ¡Hola! Me da mucho gusto saludarte. Me especializo en ayudar empresas como la tuya a encontrar soluciones que realmente impacten su crecimiento.

Para poder ofrecerte la mejor recomendación, me gustaría conocerte un poco mejor. ¿Podrías contarme tu nombre y el nombre de tu empresa?

👤 Usuario: Soy María González de TechStartup
🤖 Bot: Perfecto, María. Es un placer conocerte, y TechStartup suena muy interesante.

¿En qué sector o industria se enfoca TechStartup? Me gustaría entender mejor el contexto de tu negocio para poder ayudarte de la manera más efectiva.
```

## 📊 Sistema de Calificación

### Criterios de Scoring (Total: 100 puntos)

**Información Básica (30 puntos):**
- Nombre (10 puntos)
- Empresa (10 puntos)  
- Industria (10 puntos)

**Presupuesto (25 puntos):**
- Cifras específicas (25 puntos)
- Interés general (15 puntos)

**Ubicación (15 puntos):**
- Datos geográficos (15 puntos)

**Engagement (30 puntos):**
- Pain points (5 puntos c/u)
- Tomador de decisiones (15 puntos)

### Estados del Lead

- **🔴 No Calificado**: <40 puntos
- **🟠 Parcialmente Calificado**: 40-59 puntos  
- **🟡 Calificado**: 60-79 puntos
- **🟢 Altamente Calificado**: 80+ puntos

## 🏗️ Arquitectura

### Flujo de LangGraph

```
Mensaje → Clasificación → Extracción → Calificación → Respuesta
                                           ↓
                                    Base de Datos
                                           ↓  
                                    Brevo (Futuro)
```

### Estructura de Archivos

```
agents/
├── app/
│   ├── agents/           # Agente principal con LangGraph
│   ├── nodes/            # Nodos de procesamiento  
│   ├── database/         # Gestión de base de datos
│   └── brevo_integration.py
├── test/                 # Pruebas unitarias
├── main.py              # Interfaz Gradio
├── quick_start.py       # Script de prueba
└── requirements.txt
```

## 🧪 Testing

```bash
# Ejecutar todas las pruebas
pytest

# Prueba específica
pytest test/test_prospecting_agent.py -v

# Cobertura
pytest --cov=app
```

## 🔌 Integraciones

### Brevo API
- Sincronización de contactos
- Envío de emails transaccionales
- Links de agendamiento automático
- WhatsApp (futuro via webhooks)

### Base de Datos
- SQLite por defecto
- Fácil migración a PostgreSQL
- Esquema optimizado para prospección

## 🚀 Roadmap

### Fase 1 (Actual) ✅
- [x] Agente básico con LangGraph
- [x] Interfaz Gradio
- [x] Base de datos SQLite
- [x] Sistema de scoring

### Fase 2 🔄
- [ ] Integración completa Brevo
- [ ] Webhooks WhatsApp
- [ ] RAG para conocimiento empresarial
- [ ] Dashboard de métricas

### Fase 3 📋
- [ ] Multi-tenant (múltiples empresas)
- [ ] A/B testing de mensajes
- [ ] Analytics avanzados
- [ ] Integración CRM

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

MIT License - ver archivo `LICENSE` para detalles.

## 📞 Soporte

¿Tienes preguntas? Abre un issue o contacta al equipo de desarrollo.

---

**Desarrollado con ❤️ usando LangGraph + Gradio**