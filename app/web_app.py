# agents/web_app.py
from flask import Flask, render_template, request, jsonify, session
import os
import sys
from datetime import datetime
import uuid

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

from app.agents.prospecting_agent import get_agent
from app.database.prospect_db import get_database

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Instancias globales
agent = get_agent()
db = get_database()

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/chat')
def chat_page():
    """Página de chat"""
    # Crear nuevo thread_id si no existe
    if 'thread_id' not in session:
        session['thread_id'] = f"web-{uuid.uuid4().hex[:8]}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """API endpoint para el chat"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Mensaje vacío'}), 400
        
        # Obtener thread_id de la sesión
        thread_id = session.get('thread_id')
        if not thread_id:
            thread_id = f"web-{uuid.uuid4().hex[:8]}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            session['thread_id'] = thread_id
        
        # Procesar mensaje
        response = agent.chat(message, thread_id)
        
        # Guardar en base de datos
        db.save_conversation_message(thread_id, 'user', message)
        db.save_conversation_message(thread_id, 'bot', response)
        
        # Obtener información del prospecto
        prospect_info = agent.get_prospect_info(thread_id)
        
        # Si está completo, guardar prospecto
        if prospect_info.get('completitud', 0) == 100:
            prospect_data = {
                'nombre': prospect_info.get('nombre'),
                'empresa': prospect_info.get('empresa'),
                'presupuesto': prospect_info.get('presupuesto'),
                'ubicacion': prospect_info.get('ubicacion'),
                'sector': prospect_info.get('sector'),
                'intencion': prospect_info.get('intencion')
            }
            db.save_prospect(prospect_data, thread_id)
        
        return jsonify({
            'response': response,
            'prospect_info': prospect_info,
            'thread_id': thread_id
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/prospect-info')
def get_prospect_info():
    """Obtiene información del prospecto actual"""
    thread_id = session.get('thread_id')
    if not thread_id:
        return jsonify({'error': 'No hay conversación activa'}), 400
    
    info = agent.get_prospect_info(thread_id)
    return jsonify(info)

@app.route('/api/new-conversation', methods=['POST'])
def new_conversation():
    """Inicia una nueva conversación"""
    new_thread_id = f"web-{uuid.uuid4().hex[:8]}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session['thread_id'] = new_thread_id
    return jsonify({'thread_id': new_thread_id})

@app.route('/dashboard')
def dashboard():
    """Panel de administración"""
    prospects = db.get_all_prospects(50)
    return render_template('dashboard.html', prospects=prospects)

@app.route('/api/prospects')
def get_prospects():
    """API para obtener lista de prospectos"""
    limit = request.args.get('limit', 50, type=int)
    prospects = db.get_all_prospects(limit)
    return jsonify(prospects)

@app.route('/api/prospects/search')
def search_prospects():
    """API para buscar prospectos"""
    criteria = {}
    for field in ['nombre', 'empresa', 'sector', 'ubicacion']:
        value = request.args.get(field)
        if value:
            criteria[field] = value
    
    prospects = db.get_prospects_by_criteria(**criteria)
    return jsonify(prospects)

@app.route('/api/export')
def export_prospects():
    """API para exportar prospectos"""
    filename = db.export_to_json()
    return jsonify({'filename': filename, 'message': 'Datos exportados exitosamente'})

@app.route('/prospect/<thread_id>')
def prospect_detail(thread_id):
    """Detalles de un prospecto específico"""
    prospect = db.get_prospect_by_thread(thread_id)
    if not prospect:
        return "Prospecto no encontrado", 404
    
    conversation = db.get_conversation_history(thread_id)
    return render_template('prospect_detail.html', prospect=prospect, conversation=conversation)

# Templates HTML (crear carpeta templates/)
def create_templates():
    """Crear templates HTML"""
    templates_dir = 'templates'
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # Template base
    base_template = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot de Prospección</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .chat-container { max-height: 500px; overflow-y: auto; }
        .message { margin-bottom: 10px; }
        .user-message { text-align: right; }
        .bot-message { text-align: left; }
        .prospect-info { background-color: #f8f9fa; padding: 15px; border-radius: 5px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">🤖 Bot de Prospección</a>
            <div class="navbar-nav">
                <a class="nav-link" href="/">Inicio</a>
                <a class="nav-link" href="/chat">Chat</a>
                <a class="nav-link" href="/dashboard">Dashboard</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>'''
    
    # Template index
    index_template = '''{% extends "base.html" %}
{% block content %}
<div class="row">
    <div class="col-md-8 mx-auto text-center">
        <h1>🤖 Bot de Prospección</h1>
        <p class="lead">Sistema inteligente para recopilar información de prospectos</p>
        
        <div class="row mt-4">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">💬 Chat</h5>
                        <p class="card-text">Conversa con el bot para recopilar información</p>
                        <a href="/chat" class="btn btn-primary">Iniciar Chat</a>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">📊 Dashboard</h5>
                        <p class="card-text">Ver y administrar prospectos</p>
                        <a href="/dashboard" class="btn btn-success">Ver Dashboard</a>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">📤 Exportar</h5>
                        <p class="card-text">Exportar datos de prospectos</p>
                        <button class="btn btn-info" onclick="exportData()">Exportar</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function exportData() {
    fetch('/api/export')
        .then(response => response.json())
        .then(data => {
            alert('Datos exportados: ' + data.filename);
        })
        .catch(error => {
            alert('Error al exportar: ' + error);
        });
}
</script>
{% endblock %}'''
    
    # Template chat
    chat_template = '''{% extends "base.html" %}
{% block content %}
<div class="row">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header d-flex justify-content-between">
                <h5>💬 Chat con el Bot</h5>
                <button class="btn btn-sm btn-outline-primary" onclick="newConversation()">Nueva Conversación</button>
            </div>
            <div class="card-body">
                <div id="chatContainer" class="chat-container border rounded p-3 mb-3" style="min-height: 400px;">
                    <div class="message bot-message">
                        <small class="text-muted">Bot:</small><br>
                        <span class="text-primary">¡Hola! Soy tu asistente de prospección. ¿Podrías contarme un poco sobre ti?</span>
                    </div>
                </div>
                
                <div class="input-group">
                    <input type="text" id="messageInput" class="form-control" placeholder="Escribe tu mensaje...">
                    <button class="btn btn-primary" onclick="sendMessage()">Enviar</button>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-4">
        <div class="card">
            <div class="card-header">
                <h6>📊 Información del Prospecto</h6>
            </div>
            <div class="card-body">
                <div id="prospectInfo" class="prospect-info">
                    <p><strong>Completitud:</strong> <span id="completitud">0%</span></p>
                    <hr>
                    <p><strong>Nombre:</strong> <span id="nombre">-</span></p>
                    <p><strong>Empresa:</strong> <span id="empresa">-</span></p>
                    <p><strong>Presupuesto:</strong> <span id="presupuesto">-</span></p>
                    <p><strong>Ubicación:</strong> <span id="ubicacion">-</span></p>
                    <p><strong>Sector:</strong> <span id="sector">-</span></p>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Mostrar mensaje del usuario
    addMessage('user', message);
    input.value = '';
    
    // Enviar al servidor
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({message: message})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            addMessage('bot', 'Error: ' + data.error);
        } else {
            addMessage('bot', data.response);
            updateProspectInfo(data.prospect_info);
        }
    })
    .catch(error => {
        addMessage('bot', 'Error de conexión');
    });
}

function addMessage(type, text) {
    const container = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const label = type === 'user' ? 'Tú' : 'Bot';
    const color = type === 'user' ? 'text-success' : 'text-primary';
    
    messageDiv.innerHTML = `
        <small class="text-muted">${label}:</small><br>
        <span class="${color}">${text}</span>
    `;
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

function updateProspectInfo(info) {
    document.getElementById('completitud').textContent = (info.completitud || 0).toFixed(1) + '%';
    document.getElementById('nombre').textContent = info.nombre || '-';
    document.getElementById('empresa').textContent = info.empresa || '-';
    document.getElementById('presupuesto').textContent = info.presupuesto || '-';
    document.getElementById('ubicacion').textContent = info.ubicacion || '-';
    document.getElementById('sector').textContent = info.sector || '-';
}

function newConversation() {
    fetch('/api/new-conversation', {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            document.getElementById('chatContainer').innerHTML = `
                <div class="message bot-message">
                    <small class="text-muted">Bot:</small><br>
                    <span class="text-primary">¡Hola! Soy tu asistente de prospección. ¿Podrías contarme un poco sobre ti?</span>
                </div>
            `;
            updateProspectInfo({});
        });
}

// Enviar mensaje con Enter
document.getElementById('messageInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
</script>
{% endblock %}'''
    
    # Guardar templates
    with open(os.path.join(templates_dir, 'base.html'), 'w', encoding='utf-8') as f:
        f.write(base_template)
    
    with open(os.path.join(templates_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_template)
    
    with open(os.path.join(templates_dir, 'chat.html'), 'w', encoding='utf-8') as f:
        f.write(chat_template)

if __name__ == '__main__':
    # Crear templates si no existen
    create_templates()
    
    # Ejecutar aplicación
    app.run(debug=True, host='0.0.0.0', port=5000)