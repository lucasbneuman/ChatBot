/**
 * Lucas Benites - Chat Widget Flotante
 * Widget moderno y responsive para WordPress
 * Version: 2.0.0
 */

class LucasChatWidget {
    constructor(config = {}) {
        this.config = {
            apiUrl: config.apiUrl || 'http://localhost:8000',
            position: config.position || 'bottom-right',
            theme: config.theme || 'blue',
            autoOpen: config.autoOpen || false,
            ...config
        };
        
        this.isOpen = false;
        this.isMinimized = false;
        this.sessionId = this.generateSessionId();
        this.messages = [];
        this.isTyping = false;
        
        this.init();
    }
    
    generateSessionId() {
        return 'widget_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    init() {
        this.loadConfig().then(() => {
            this.createWidget();
            this.attachEventListeners();
            this.loadWelcomeMessage();
            
            if (this.config.autoOpen) {
                setTimeout(() => this.openWidget(), 2000);
            }
        });
    }
    
    async loadConfig() {
        try {
            const response = await fetch(`${this.config.apiUrl}/widget/config`);
            const data = await response.json();
            
            if (data.success) {
                this.widgetConfig = data.config;
            }
        } catch (error) {
            console.warn('Could not load widget config:', error);
            this.widgetConfig = this.getDefaultConfig();
        }
    }
    
    getDefaultConfig() {
        return {
            title: "¡Hola! Soy el asistente de Lucas",
            subtitle: "¿En qué puedo ayudarte hoy?",
            placeholder: "Escribe tu mensaje aquí...",
            theme: {
                primary_color: "#2563EB",
                secondary_color: "#F3F4F6",
                text_color: "#1F2937",
                border_radius: "12px"
            },
            contact_info: {
                name: "Lucas Benites",
                title: "Especialista en IA para PyMEs"
            }
        };
    }
    
    createWidget() {
        // Container principal
        this.widget = document.createElement('div');
        this.widget.id = 'lucas-chat-widget';
        this.widget.className = `lucas-widget ${this.config.position}`;
        
        // CSS inline para evitar conflictos con WordPress
        this.widget.innerHTML = `
            <style>
                .lucas-widget {
                    position: fixed;
                    z-index: 10000;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }
                
                .lucas-widget.bottom-right {
                    bottom: 20px;
                    right: 20px;
                }
                
                .lucas-widget.bottom-left {
                    bottom: 20px;
                    left: 20px;
                }
                
                .chat-bubble {
                    width: 60px;
                    height: 60px;
                    background: ${this.widgetConfig.theme.primary_color};
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    transition: all 0.3s ease;
                    animation: pulse 2s infinite;
                }
                
                .chat-bubble:hover {
                    transform: scale(1.1);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.25);
                }
                
                .chat-bubble svg {
                    width: 24px;
                    height: 24px;
                    fill: white;
                }
                
                @keyframes pulse {
                    0% { box-shadow: 0 0 0 0 ${this.widgetConfig.theme.primary_color}40; }
                    70% { box-shadow: 0 0 0 10px transparent; }
                    100% { box-shadow: 0 0 0 0 transparent; }
                }
                
                .chat-window {
                    position: absolute;
                    bottom: 80px;
                    right: 0;
                    width: 350px;
                    max-width: calc(100vw - 40px);
                    height: 500px;
                    max-height: calc(100vh - 120px);
                    background: white;
                    border-radius: ${this.widgetConfig.theme.border_radius};
                    box-shadow: 0 8px 32px rgba(0,0,0,0.12);
                    display: none;
                    flex-direction: column;
                    overflow: hidden;
                }
                
                .chat-window.open {
                    display: flex;
                    animation: slideUp 0.3s ease-out;
                }
                
                @keyframes slideUp {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                
                .chat-header {
                    background: ${this.widgetConfig.theme.primary_color};
                    color: white;
                    padding: 16px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .chat-header-info h3 {
                    margin: 0;
                    font-size: 16px;
                    font-weight: 600;
                }
                
                .chat-header-info p {
                    margin: 4px 0 0 0;
                    font-size: 12px;
                    opacity: 0.9;
                }
                
                .chat-controls {
                    display: flex;
                    gap: 8px;
                }
                
                .chat-controls button {
                    background: none;
                    border: none;
                    color: white;
                    cursor: pointer;
                    padding: 4px;
                    border-radius: 4px;
                    transition: background 0.2s;
                }
                
                .chat-controls button:hover {
                    background: rgba(255,255,255,0.2);
                }
                
                .chat-messages {
                    flex: 1;
                    overflow-y: auto;
                    padding: 16px;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }
                
                .message {
                    display: flex;
                    max-width: 80%;
                    animation: fadeIn 0.3s ease-out;
                }
                
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                
                .message.user {
                    align-self: flex-end;
                }
                
                .message.assistant {
                    align-self: flex-start;
                }
                
                .message-content {
                    padding: 12px 16px;
                    border-radius: 18px;
                    word-wrap: break-word;
                    font-size: 14px;
                    line-height: 1.4;
                }
                
                .message.user .message-content {
                    background: ${this.widgetConfig.theme.primary_color};
                    color: white;
                    border-bottom-right-radius: 4px;
                }
                
                .message.assistant .message-content {
                    background: ${this.widgetConfig.theme.secondary_color};
                    color: ${this.widgetConfig.theme.text_color};
                    border-bottom-left-radius: 4px;
                }
                
                .typing-indicator {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    padding: 12px 16px;
                    background: ${this.widgetConfig.theme.secondary_color};
                    border-radius: 18px;
                    border-bottom-left-radius: 4px;
                    max-width: 80px;
                }
                
                .typing-dot {
                    width: 6px;
                    height: 6px;
                    background: #999;
                    border-radius: 50%;
                    animation: typing 1.4s infinite;
                }
                
                .typing-dot:nth-child(2) { animation-delay: 0.2s; }
                .typing-dot:nth-child(3) { animation-delay: 0.4s; }
                
                @keyframes typing {
                    0%, 60%, 100% { opacity: 0.3; }
                    30% { opacity: 1; }
                }
                
                .chat-input {
                    padding: 16px;
                    border-top: 1px solid #E5E7EB;
                    display: flex;
                    gap: 12px;
                    align-items: flex-end;
                }
                
                .chat-input textarea {
                    flex: 1;
                    border: 1px solid #D1D5DB;
                    border-radius: 20px;
                    padding: 12px 16px;
                    font-size: 14px;
                    font-family: inherit;
                    resize: none;
                    max-height: 100px;
                    min-height: 40px;
                    outline: none;
                    transition: border-color 0.2s;
                }
                
                .chat-input textarea:focus {
                    border-color: ${this.widgetConfig.theme.primary_color};
                }
                
                .send-button {
                    background: ${this.widgetConfig.theme.primary_color};
                    border: none;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: background 0.2s;
                }
                
                .send-button:hover:not(:disabled) {
                    background: ${this.widgetConfig.theme.primary_color}DD;
                }
                
                .send-button:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                
                .send-button svg {
                    width: 16px;
                    height: 16px;
                    fill: white;
                }
                
                .powered-by {
                    padding: 8px 16px;
                    text-align: center;
                    font-size: 11px;
                    color: #9CA3AF;
                    border-top: 1px solid #F3F4F6;
                }
                
                .powered-by a {
                    color: ${this.widgetConfig.theme.primary_color};
                    text-decoration: none;
                }
                
                /* Responsive */
                @media (max-width: 480px) {
                    .lucas-widget.bottom-right,
                    .lucas-widget.bottom-left {
                        bottom: 10px;
                        right: 10px;
                        left: 10px;
                    }
                    
                    .chat-window {
                        width: 100%;
                        height: 80vh;
                        bottom: 80px;
                        right: 0;
                        left: 0;
                        margin: 0 10px;
                        width: calc(100% - 20px);
                    }
                }
            </style>
            
            <!-- Chat Bubble -->
            <div class="chat-bubble" id="chat-bubble">
                <svg viewBox="0 0 24 24">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                    <path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/>
                </svg>
            </div>
            
            <!-- Chat Window -->
            <div class="chat-window" id="chat-window">
                <div class="chat-header">
                    <div class="chat-header-info">
                        <h3>${this.widgetConfig.title}</h3>
                        <p>${this.widgetConfig.contact_info.title}</p>
                    </div>
                    <div class="chat-controls">
                        <button id="minimize-btn" title="Minimizar">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M19 13H5v-2h14v2z"/>
                            </svg>
                        </button>
                        <button id="close-btn" title="Cerrar">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                            </svg>
                        </button>
                    </div>
                </div>
                
                <div class="chat-messages" id="chat-messages">
                    <!-- Messages will be added here -->
                </div>
                
                <div class="chat-input">
                    <textarea 
                        id="message-input" 
                        placeholder="${this.widgetConfig.placeholder}"
                        rows="1"
                    ></textarea>
                    <button class="send-button" id="send-btn">
                        <svg viewBox="0 0 24 24">
                            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                    </button>
                </div>
                
                <div class="powered-by">
                    Powered by <a href="https://lucasbenites.com" target="_blank">Lucas Benites IA</a>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.widget);
    }
    
    attachEventListeners() {
        const bubble = this.widget.querySelector('#chat-bubble');
        const closeBtn = this.widget.querySelector('#close-btn');
        const minimizeBtn = this.widget.querySelector('#minimize-btn');
        const sendBtn = this.widget.querySelector('#send-btn');
        const messageInput = this.widget.querySelector('#message-input');
        
        bubble.addEventListener('click', () => this.toggleWidget());
        closeBtn.addEventListener('click', () => this.closeWidget());
        minimizeBtn.addEventListener('click', () => this.minimizeWidget());
        sendBtn.addEventListener('click', () => this.sendMessage());
        
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        messageInput.addEventListener('input', this.autoResize.bind(this));
    }
    
    autoResize() {
        const textarea = this.widget.querySelector('#message-input');
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 100) + 'px';
    }
    
    loadWelcomeMessage() {
        this.addMessage('assistant', this.widgetConfig.subtitle);
    }
    
    toggleWidget() {
        if (this.isOpen) {
            this.closeWidget();
        } else {
            this.openWidget();
        }
    }
    
    openWidget() {
        const chatWindow = this.widget.querySelector('#chat-window');
        chatWindow.classList.add('open');
        this.isOpen = true;
        this.isMinimized = false;
        
        setTimeout(() => {
            this.widget.querySelector('#message-input').focus();
        }, 300);
    }
    
    closeWidget() {
        const chatWindow = this.widget.querySelector('#chat-window');
        chatWindow.classList.remove('open');
        this.isOpen = false;
        this.isMinimized = false;
    }
    
    minimizeWidget() {
        this.closeWidget();
        this.isMinimized = true;
    }
    
    async sendMessage() {
        const messageInput = this.widget.querySelector('#message-input');
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        // Limpiar input
        messageInput.value = '';
        this.autoResize();
        
        // Mostrar mensaje del usuario
        this.addMessage('user', message);
        
        // Mostrar indicador de escritura
        this.showTypingIndicator();
        
        try {
            const response = await fetch(`${this.config.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId,
                    user_info: {
                        url: window.location.href,
                        referrer: document.referrer,
                        user_agent: navigator.userAgent
                    }
                })
            });
            
            const data = await response.json();
            
            // Ocultar indicador de escritura
            this.hideTypingIndicator();
            
            if (data.success) {
                this.addMessage('assistant', data.response);
                
                // Actualizar session_id si es nuevo
                if (data.session_id) {
                    this.sessionId = data.session_id;
                }
            } else {
                this.addMessage('assistant', data.response || 'Lo siento, hubo un error. ¿Podrías intentar de nuevo?');
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage('assistant', 'Lo siento, no pude conectar con el servidor. ¿Podrías intentar de nuevo?');
        }
    }
    
    addMessage(sender, content) {
        const messagesContainer = this.widget.querySelector('#chat-messages');
        
        const messageEl = document.createElement('div');
        messageEl.className = `message ${sender}`;
        messageEl.innerHTML = `
            <div class="message-content">${this.formatMessage(content)}</div>
        `;
        
        messagesContainer.appendChild(messageEl);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        this.messages.push({ sender, content, timestamp: new Date() });
    }
    
    formatMessage(content) {
        // Convertir URLs en enlaces
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        content = content.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener">$1</a>');
        
        // Convertir saltos de línea
        content = content.replace(/\n/g, '<br>');
        
        return content;
    }
    
    showTypingIndicator() {
        if (this.isTyping) return;
        
        this.isTyping = true;
        const messagesContainer = this.widget.querySelector('#chat-messages');
        
        const typingEl = document.createElement('div');
        typingEl.className = 'message assistant';
        typingEl.id = 'typing-indicator';
        typingEl.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        
        messagesContainer.appendChild(typingEl);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    hideTypingIndicator() {
        if (!this.isTyping) return;
        
        const typingEl = this.widget.querySelector('#typing-indicator');
        if (typingEl) {
            typingEl.remove();
        }
        this.isTyping = false;
    }
}

// Auto-inicializar si se especifica en el script tag
document.addEventListener('DOMContentLoaded', () => {
    const scriptTag = document.querySelector('script[src*="lucas-chat-widget.js"]');
    if (scriptTag) {
        const config = {};
        
        // Leer configuración del script tag
        if (scriptTag.dataset.apiUrl) config.apiUrl = scriptTag.dataset.apiUrl;
        if (scriptTag.dataset.position) config.position = scriptTag.dataset.position;
        if (scriptTag.dataset.autoOpen) config.autoOpen = scriptTag.dataset.autoOpen === 'true';
        
        // Inicializar widget
        window.lucasChatWidget = new LucasChatWidget(config);
    }
});

// Exportar para uso manual
window.LucasChatWidget = LucasChatWidget;