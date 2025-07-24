# 🤖 Agente Inteligente de Lucas Benites

**Asistente IA especializado en tecnología para PyMEs con arquitectura unificada multi-canal**

## ✨ Características Principales

- **🧠 Agente Único Inteligente**: Detecta automáticamente intenciones (información vs prospección)
- **📚 RAG Integrado**: Acceso a información actualizada de la empresa
- **🎯 Calificación Automática**: Sistema de scoring para prospectos
- **🔗 Integración Brevo**: Sincronización automática con CRM
- **📱 Multi-Canal**: Web, Facebook Messenger (WhatsApp en desarrollo)
- **⚡ Alto Rendimiento**: Arquitectura optimizada y rápida

## 🏗️ Arquitectura

```
📱 CANALES
├── 🌐 Web (Gradio)
├── 💬 Facebook Messenger  
└── 📱 WhatsApp (futuro)
     ↓
🧠 UNIFIED AGENT
     ↓
💾 SQLite Database
```

## 🚀 Instalación

1. **Clona el repositorio**:
```bash
git clone [url-del-repo]
cd agents
```

2. **Instala dependencias**:
```bash
pip install -r requirements.txt
```

3. **Configura variables de entorno**:
```bash
cp .env.production.example .env
# Edita .env con tus API keys
```

4. **Ejecuta la aplicación**:
```bash
python main.py
```

## ⚙️ Configuración

### Variables de Entorno Requeridas

```env
OPENAI_API_KEY=tu-openai-api-key
BREVO_API_KEY=tu-brevo-api-key
```

## 📁 Estructura del Proyecto

```
agents/
├── app/
│   ├── agents/
│   │   └── unified_agent.py        # Agente principal
│   ├── core/
│   │   ├── rag_system.py          # Sistema RAG
│   │   └── prompt_manager.py      # Gestión de prompts
│   ├── database/
│   │   └── prospect_db_fixed.py   # Base de datos
│   ├── nodes/
│   │   ├── data_extractor.py      # Extracción de datos
│   │   ├── response_generator.py  # Generación de respuestas
│   │   └── brevo_sync_node.py     # Sincronización Brevo
│   └── interfaces/               # Interfaces multi-canal (próximamente)
├── resources/
│   └── company_docs/             # Documentos para RAG
├── main.py                       # Aplicación principal
└── prospects_production.db       # Base de datos de producción
```

## 🎯 Funcionalidades

### Sistema de Calificación
- **Score automático** basado en datos del prospecto
- **Umbral de 65 puntos** para envío de meeting links
- **Factores**: nombre, empresa, presupuesto, industria, problemas identificados

### Detección de Intenciones
- **Información**: Preguntas sobre servicios, precios, contacto
- **Prospección**: Conversación sobre el negocio del usuario
- **Mixta**: Combinación de ambas

### Integración Brevo
- **Contactos automáticos** cuando se programa reunión
- **Oportunidades** con datos del prospecto
- **Tareas** para seguimiento
- **Notas** de la conversación

## 🔧 Desarrollo

### Testing
```bash
python test_meeting_link.py  # Test funcionalidad completa
```

### Deploy
```bash
python deploy.py  # Verificar antes de desplegar
```

## 📊 Métricas

El sistema rastrea automáticamente:
- Número de conversaciones por canal
- Score de calificación de prospectos
- Tasa de conversión a meeting links
- Sincronización con Brevo

## 🌟 Estado Actual

### ✅ Completado
- [x] Agente único inteligente funcional
- [x] Sistema RAG integrado
- [x] Calificación automática de prospectos
- [x] Integración completa con Brevo
- [x] Interfaz web Gradio optimizada
- [x] Meeting links automáticos
- [x] Base de datos robusta

### 🚧 En Desarrollo
- [ ] Facebook Messenger webhook
- [ ] Widget flotante para web
- [ ] Dashboard admin multi-canal

### 🔮 Próximas Funcionalidades
- [ ] WhatsApp Business API
- [ ] Analytics avanzados
- [ ] Integración con más CRMs

## 📞 Contacto

**Lucas Benites**
- Email: lucas@lucasbenites.com
- WhatsApp: +54 3517554495
- Calendario: https://meet.brevo.com/lucas-benites

---

🤖 **Versión**: 2.0 - Arquitectura Unificada  
📅 **Última actualización**: Enero 2025