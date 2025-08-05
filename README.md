# 🤖 Agente Inteligente de Lucas Benites

**Asistente IA especializado en tecnología para PyMEs con arquitectura unificada multi-canal**

## ✨ Características Principales

- **🧠 Agente Único Inteligente**: Detecta automáticamente intenciones (información vs prospección)
- **📚 RAG Integrado**: Acceso a información actualizada de la empresa
- **🎯 Calificación Automática**: Sistema de scoring para prospectos
- **🔗 Integración Brevo**: Sincronización automática con CRM
- **📱 Multi-Canal**: Web, Widget WordPress, Facebook Messenger (WhatsApp en desarrollo)
- **⚡ Alto Rendimiento**: Arquitectura optimizada y rápida

## 🏗️ Arquitectura

```
📱 CANALES
├── 🌐 Web (Gradio Dashboard)
├── 🌐 Widget WordPress
├── 💬 Facebook Messenger  
└── 📱 WhatsApp (futuro)
     ↓
🧠 UNIFIED AGENT
     ↓
💾 SQLite Database ←→ 🔗 Brevo CRM
```

## 🚀 Instalación Rápida

### 1. **Clonar repositorio**:
```bash
git clone [url-del-repo]
cd agents
```

### 2. **Crear entorno virtual**:
```bash
python -m venv venv

# Activar (Windows)
venv\Scripts\activate

# Activar (Linux/Mac)
source venv/bin/activate
```

### 3. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

### 4. **Configurar variables de entorno**:
```bash
# Crear archivo .env en la raíz del proyecto
OPENAI_API_KEY=tu-openai-api-key
BREVO_API_KEY=tu-brevo-api-key
```

### 5. **Ejecutar aplicación**:
```bash
# Para desarrollo con Gradio Dashboard
python main.py

# Para producción (solo Widget API)
python server_production.py
```

## ⚙️ Scripts de Desarrollo

### **Para Widget WordPress**:
```bash
python server_widget.py
# Widget disponible en: http://localhost:8002
# Dashboard: http://localhost:7864
```

### **Testing**:
```bash
# Test completo del sistema
cd test
python test_supervisor_flow.py

# Test conexión Brevo
python test_brevo_connection.py
```

### **Deploy**:
```bash
python deploy.py  # Verificar antes de desplegar
```

## 📁 Estructura del Proyecto

```
agents/
├── app/
│   ├── agents/
│   │   └── unified_agent.py        # Agente principal unificado
│   ├── core/
│   │   ├── rag_system.py          # Sistema RAG
│   │   └── prompt_manager.py      # Gestión de prompts
│   ├── database/
│   │   └── prospect_db_fixed.py   # Base de datos SQLite
│   ├── nodes/
│   │   ├── data_extractor.py      # Extracción de datos
│   │   ├── response_generator.py  # Generación de respuestas
│   │   └── brevo_sync_node.py     # Sincronización Brevo
│   ├── interfaces/
│   │   └── widget_api.py          # API del Widget WordPress
│   └── config/
│       └── brevo_config.py        # Configuración Brevo
├── resources/
│   └── company_docs/              # Documentos para RAG (PDF/TXT)
├── static/
│   └── widget/
│       └── lucas-chat-widget.js   # Widget JavaScript
├── venv/                          # Entorno virtual Python
├── main.py                        # Aplicación Gradio principal
├── server_widget.py               # Servidor desarrollo widget
├── server_production.py           # Servidor producción
└── prospects_production.db        # Base de datos de producción
```

## 🎯 Funcionalidades

### **Sistema de Calificación Inteligente**
- **Score automático** basado en datos del prospecto (0-100 puntos)
- **Umbral de 65 puntos** para envío automático de meeting links
- **Factores de scoring**: 
  - Nombre proporcionado (+15 pts)
  - Empresa mencionada (+20 pts)
  - Presupuesto indicado (+25 pts)
  - Industria identificada (+15 pts)
  - Problemas específicos (+25 pts)

### **Detección de Intenciones**
- **Información**: Preguntas sobre servicios, precios, contacto
- **Prospección**: Conversación sobre el negocio del usuario
- **Mixta**: Combinación de ambas intenciones

### **Sistema RAG (Retrieval-Augmented Generation)**
- **Procesamiento automático** de PDFs y archivos TXT en `resources/company_docs/`
- **Búsqueda inteligente** de información relevante
- **Integración natural** en las respuestas del agente

### **Integración Brevo CRM**
- **Contactos automáticos** cuando se programa reunión
- **Oportunidades** creadas con datos del prospecto
- **Tareas** de seguimiento asignadas
- **Notas** completas de la conversación

## 🌐 Widget WordPress

### **Integración Rápida**
1. **Ejecutar servidor**: `python server_widget.py`
2. **Obtener código**: Visita `http://localhost:8002/widget/embed`
3. **Pegar en WordPress**: Antes del `</body>` en tu tema

### **Código de Embed Básico**:
```html
<!-- Lucas Benites Chat Widget -->
<script>
    window.LUCAS_WIDGET_CONFIG = {
        apiUrl: 'https://tu-servidor.com/api',
        position: 'bottom-right',
        autoOpen: false,
        theme: 'blue'
    };
</script>
<script src="https://tu-servidor.com/static/widget/lucas-chat-widget.js" 
        data-api-url="https://tu-servidor.com/api"
        data-position="bottom-right"
        data-auto-open="false">
</script>
```

### **Configuraciones del Widget**:
```javascript
window.LUCAS_WIDGET_CONFIG = {
    apiUrl: 'https://tu-servidor.com/api',     // URL de tu API
    position: 'bottom-right',                  // 'bottom-right' | 'bottom-left'
    autoOpen: false,                           // Abrir automáticamente
    theme: 'blue',                             // 'blue' | 'green' | 'red'
    welcomeMessage: "¡Hola! ¿En qué puedo ayudarte?",
    placeholder: "Escribe tu mensaje...",
    showPoweredBy: true,
    enableTypingIndicator: true,
    maxMessages: 50
};
```

## 🚀 Deploy en Producción

### **Variables de Entorno para Producción**:
```env
OPENAI_API_KEY=tu-openai-key
BREVO_API_KEY=tu-brevo-key
RENDER=true                    # Desactiva Gradio en Render
ENABLE_GRADIO=false           # Para producción
```

### **Deploy en Render/Railway**:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python server_production.py`

### **Endpoints Disponibles**:
- **API Principal**: `/api/`
- **Widget Embed**: `/widget/embed`
- **Health Check**: `/health`
- **Admin Dashboard**: Solo en desarrollo local

### **CORS en Producción**:
Actualizar `widget_api.py` con tus dominios:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tu-sitio-wordpress.com",
        "https://www.tu-sitio-wordpress.com",
        "https://lucasbenites.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

## 📊 Testing y Monitoreo

### **Tests Automatizados**:
```bash
# Test completo del flujo
python test/test_supervisor_flow.py

# Test conexión Brevo
python test_brevo_connection.py
```

### **Métricas Automáticas**:
- ✅ Conversaciones por canal y sesión
- ✅ Score de calificación de prospectos  
- ✅ Tasa de conversión a meeting links
- ✅ Sincronización exitosa con Brevo
- ✅ Tiempo de respuesta del agente

### **Logs y Debugging**:
- Logs detallados en consola durante desarrollo
- Tracking de errores y excepciones
- Métricas de rendimiento del RAG

## 🛠️ Troubleshooting

### **Problemas Comunes**:

**1. Widget no aparece**:
- Verificar que `server_widget.py` esté corriendo
- Revisar consola del navegador por errores CORS
- Confirmar que las URLs en el embed sean correctas

**2. Error de conexión Brevo**:
- Verificar `BREVO_API_KEY` en variables de entorno
- Comprobar permisos de API (debe tener acceso a Contacts y CRM)
- Ejecutar `python test_brevo_connection.py` para diagnóstico

**3. RAG no encuentra información**:
- Verificar que hay archivos PDF/TXT en `resources/company_docs/`
- Reiniciar aplicación para reprocessar documentos
- Comprobar que los archivos no estén corruptos

**4. Base de datos bloqueada**:
- Cerrar todas las instancias de la aplicación
- Verificar permisos de escritura en `prospects_production.db`
- Si persiste, respaldar y recrear la base de datos

## 📈 Estado del Proyecto

### ✅ **Completado**:
- [x] Agente único inteligente funcional
- [x] Sistema RAG integrado y optimizado
- [x] Calificación automática de prospectos
- [x] Integración completa con Brevo CRM
- [x] Widget WordPress completamente funcional
- [x] Dashboard Gradio para administración
- [x] Meeting links automáticos con scoring
- [x] Base de datos SQLite robusta
- [x] Deploy automatizado en Railway/Render

### 🚧 **En Desarrollo**:
- [ ] Facebook Messenger webhook
- [ ] Dashboard admin multi-canal avanzado
- [ ] Analytics detallados por canal

### 🔮 **Próximas Funcionalidades**:
- [ ] WhatsApp Business API
- [ ] Integración con más CRMs (HubSpot, Salesforce)
- [ ] A/B testing de mensajes
- [ ] Analytics avanzados con métricas de conversión

## 📞 Contacto y Soporte

**Lucas Benites** - Especialista en IA para PyMEs
- 📧 **Email**: lucas@lucasbenites.com
- 💬 **WhatsApp**: +54 3517554495
- 📅 **Agendar reunión**: https://meet.brevo.com/lucas-benites
- 🌐 **Web**: https://lucasbenites.com

---

## 🔧 Notas Técnicas

### **Dependencias Principales**:
- **FastAPI**: API REST del widget
- **Gradio**: Dashboard de administración
- **OpenAI**: Modelo de lenguaje principal
- **LangChain**: Framework para IA y RAG
- **FAISS**: Vector store para RAG
- **SQLite**: Base de datos local
- **Requests**: Integración con APIs externas

### **Arquitectura de Seguridad**:
- Variables de entorno para API keys sensibles
- CORS configurado específicamente por dominio
- Validación de entrada en todos los endpoints
- Rate limiting implícito por sesión

### **Performance**:
- RAG optimizado con cache vectorial
- Base de datos SQLite con índices optimizados
- Respuestas streaming para mejor UX
- Lazy loading de componentes pesados

---

🤖 **Versión**: 3.0 - Migración completa a venv  
📅 **Última actualización**: Agosto 2025  
🛠️ **Python**: 3.12.1 con venv