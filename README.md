# 🤖 Asistente de Prospección Inteligente - Lucas Benites

Sistema automatizado de calificación de leads especializado en **PyMEs** usando **LangGraph**, **Gradio** y **OpenAI GPT-4**. Diseñado para convertir conversaciones naturales en leads calificados para servicios de IA y automatización.

## 🚀 Características Principales

### **💬 Conversación Natural para PyMEs**
- **Lenguaje cercano y simple** - Sin jerga técnica, habla como un vecino que entiende de tecnología
- **Progresión inteligente** - Construye confianza antes de explorar necesidades
- **Enfoque consultivo** - Entiende problemas antes de ofrecer soluciones
- **Multi-usuario** - Sesiones independientes por dispositivo/pestaña

### **🧠 IA Inteligente**
- **Extracción flexible** - Captura información aunque no sea explícita ("Soy Juan de TechCorp")
- **Sistema de scoring progresivo** - Evalúa múltiples criterios para calificar leads
- **Mejora automática de notas** - IA organiza y limpia información recopilada
- **Memory management** - Mantiene contexto completo con LangGraph

### **📊 Calificación Automática**
- **Score dinámico** - Sistema de puntos que considera información básica, problemas identificados y nivel de interés
- **Umbral inteligente** - Solo leads con 65+ puntos califican para reunión
- **Progresión natural** - 4 fases de conversación antes de ofrecer consulta

### **🔗 Integración Lista**
- **Link de Brevo** - Integración directa con calendario de Lucas Benites
- **Base de datos robusta** - SQLite con migración automática
- **Interfaz web moderna** - Gradio con tema optimizado

## 🎯 Flujo de Conversación

### **Fase 1: Construcción de Confianza (mensajes 1-3)**
- Saludo amigable y natural
- Pregunta sobre su negocio y desafíos
- Obtiene nombre y tipo de empresa
- **No menciona reuniones** - solo construye rapport

### **Fase 2: Exploración de Problemas (mensajes 4-6)**
- Profundiza en problemas específicos del día a día
- Identifica múltiples pain points
- Entiende el impacto en su negocio
- **Aún no ofrece soluciones** - solo escucha

### **Fase 3: Construcción de Valor (mensajes 7-10)**
- Conecta problemas con soluciones de IA
- Comparte casos de éxito similares
- Explica beneficios en términos simples
- **Prepara para posible consulta** - evalúa interés

### **Fase 4: Calificación Final (mensajes 10+)**
- Evalúa todos los criterios de calificación
- Solo ofrece consulta si score >= 65
- **Link automático** si cumple criterios

## 📈 Sistema de Scoring

| Categoría | Puntos | Criterios |
|-----------|--------|-----------|
| **Información Básica** | 30 pts | Nombre (10) + Empresa (10) + Industria (10) |
| **Pain Points** | 20 pts | 1 problema (10pts), 2 problemas (15pts), 3+ problemas (20pts) |
| **Engagement** | 15 pts | Decision maker (10pts) + Necesidades claras (5pts) |
| **Profundidad** | 20 pts | Longitud conversación + Diversidad info + Indicadores interés |
| **Presupuesto** | 10 pts | Opcional - Cifras específicas (10pts) o mención general (5pts) |
| **Ubicación** | 5 pts | Datos geográficos |

**🎯 Calificación:** 65+ puntos = Listo para consulta con Lucas

## 🛠️ Instalación

### Requisitos Previos
- Python 3.8+
- Conda o pip
- Cuenta OpenAI API
- Cuenta Brevo (opcional)

### Configuración Rápida

```bash
# Clonar repositorio
git clone <repository-url>
cd agents

# Crear entorno virtual
conda create -n agents python=3.9
conda activate agents

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu API key de OpenAI
```

### Variables de Entorno

```bash
# .env
OPENAI_API_KEY=tu_openai_api_key_aqui
BREVO_API_KEY=tu_brevo_api_key_aqui  # Opcional
DATABASE_URL=sqlite:///./prospects.db
MAX_TOKENS=120
RESPONSE_TEMPERATURE=0.3
```

## 🚀 Uso

### Lanzar Aplicación
```bash
python main.py
```
- **Local**: http://127.0.0.1:7860
- **Público**: Link automático de Gradio (72 horas)

### Prueba Rápida (Terminal)
```bash
python quick_start_improved.py
```

### Limpiar Base de Datos
```bash
python clean_database.py
```

## 📊 Interfaz de Usuario

### **Panel Principal**
- **Chat inteligente** - Conversación natural en tiempo real
- **Info del prospecto** - Score, datos recopilados y notas mejoradas por IA
- **Auto-refresh** - Actualización automática después de cada mensaje

### **Información Mostrada**
- ID único por sesión
- Datos básicos (nombre, empresa, industria)
- Score de calificación en tiempo real
- Estado del link de reunión
- Notas organizadas automáticamente por IA
- Resumen de calificación con recomendación

## 🔧 Arquitectura Técnica

### **Stack Principal**
- **LangGraph** - Gestión de estados y flujo conversacional
- **OpenAI GPT-4** - Procesamiento de lenguaje natural
- **Gradio** - Interfaz web moderna
- **SQLite** - Base de datos con migración automática

### **Componentes Clave**

```
agents/
├── app/
│   ├── agents/           # Agente principal con LangGraph
│   │   └── prospecting_agent.py
│   ├── nodes/            # Nodos de procesamiento
│   │   ├── message_parser.py     # Extracción inteligente
│   │   ├── data_extractor.py     # Scoring y datos
│   │   └── response_generator.py # Prompts para PyMEs
│   ├── database/         # Gestión de base de datos
│   │   └── prospect_db.py
│   └── brevo_integration.py      # Integración externa
├── main.py              # Interfaz Gradio multi-usuario
├── quick_start_improved.py       # Script de pruebas
└── requirements.txt
```

### **Flujo de Datos**

```
Mensaje Usuario → Parser (extrae datos) → Scorer (califica) → 
Generator (responde) → Database (guarda) → UI (muestra)
                ↓
    LangGraph (mantiene contexto y estado)
```

## 🧪 Testing

### Ejecutar Pruebas
```bash
# Todas las pruebas
pytest

# Pruebas específicas
pytest test/test_prospecting_agent.py -v

# Con cobertura
pytest --cov=app
```

### Casos de Prueba Incluidos
- ✅ Extracción flexible de información
- ✅ Sistema de scoring progresivo
- ✅ Manejo de sesiones múltiples
- ✅ Mejora automática de notas
- ✅ Flujo completo de calificación

## 🔌 Integraciones

### **Brevo (Configurado)**
- Link directo: `https://meet.brevo.com/lucas-benites`
- Sincronización de contactos (ready)
- Emails transaccionales (ready)
- WhatsApp webhooks (futuro)

### **Extensiones Disponibles**
- **Langfuse** - Analytics y edición de prompts
- **Google Calendar** - Integración directa
- **CRM** - Exportación de leads calificados

## 🎯 Casos de Uso Específicos

### **Tipos de Negocio Optimizados**
- 🏥 **Consultorios médicos/dentales** - Automatización de citas
- 🍕 **Restaurantes** - Gestión de pedidos y reservas
- 🛠️ **Talleres/servicios** - Seguimiento de clientes
- 🛍️ **E-commerce** - Atención al cliente 24/7
- 📊 **Consultorías** - Calificación de prospectos

### **Problemas que Identifica**
- Respuestas repetitivas a clientes
- Gestión manual de horarios/citas
- Pérdida de leads por demora en respuesta
- Procesos manuales que consumen tiempo
- Falta de seguimiento automatizado

## 📊 Métricas y Analytics

### **KPIs Principales**
- **Tasa de calificación** - % de conversaciones que llegan a 65+ puntos
- **Time to qualify** - Promedio de mensajes para calificar
- **Conversion rate** - % de links enviados vs agendados
- **Score distribution** - Distribución de puntuaciones

### **Datos Recopilados**
- Información básica completa (nombre, empresa, industria)
- Problemas específicos identificados
- Nivel de urgencia y timeline
- Canal de comunicación preferido
- Indicadores de capacidad de pago

## 🚀 Roadmap

### **Próximas Mejoras (Q3 2025)**
- [ ] Dashboard de métricas en tiempo real
- [ ] A/B testing de prompts
- [ ] Integración WhatsApp Business
- [ ] RAG con casos de éxito de Lucas

### **Futuro (Q4 2025)**
- [ ] Multi-tenancy para otros consultores
- [ ] IA voice para llamadas telefónicas
- [ ] Predicción de cierre de ventas
- [ ] Automatización completa del follow-up

## 🤝 Contribución

### Para Desarrolladores
1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Implementar cambios con tests
4. Commit con mensaje descriptivo
5. Push y crear Pull Request

### Estructura de Commits
```
feat: nueva funcionalidad de scoring
fix: corrige extracción de nombres
docs: actualiza README con nuevas features
test: añade tests para multi-usuario
```

## 📄 Licencia

MIT License - Ver archivo `LICENSE` para detalles completos.

## 📞 Contacto y Soporte

### **Para Lucas Benites**
- 🔗 **Agendar consulta**: https://meet.brevo.com/lucas-benites
- 📧 **Email**: [contacto]
- 💼 **LinkedIn**: [perfil]

### **Soporte Técnico**
- 🐛 **Issues**: Usar GitHub Issues
- 📖 **Documentación**: Wiki del repositorio
- 💬 **Discusiones**: GitHub Discussions

---

**⚡ Desarrollado con IA para PyMEs que quieren automatizar y crecer**

*"Convirtiendo conversaciones naturales en oportunidades de negocio"*