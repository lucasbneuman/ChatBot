# 🌐 Integración WordPress - Lucas Chat Widget

## 📋 **Instrucciones de Instalación**

### **Opción 1: Código Directo (Recomendado)**

1. **Ve a tu WordPress Admin**
2. **Appearance → Theme Editor** (o usa un plugin como "Insert Headers and Footers")
3. **Agrega este código antes del `</body>`**:

```html
<!-- Lucas Benites Chat Widget -->
<script>
    window.LUCAS_WIDGET_CONFIG = {
        apiUrl: 'https://tu-servidor.com/api',  // Cambiar por tu URL
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

### **Opción 2: Plugin Personalizado**

Crear un plugin WordPress básico:

```php
<?php
/**
 * Plugin Name: Lucas Chat Widget
 * Description: Widget de chat inteligente para Lucas Benites
 * Version: 2.0.0
 * Author: Lucas Benites
 */

// Evitar acceso directo
if (!defined('ABSPATH')) {
    exit;
}

class LucasChatWidget {
    
    private $api_url = 'https://tu-servidor.com/api';  // CAMBIAR AQUÍ
    private $widget_url = 'https://tu-servidor.com/static/widget/lucas-chat-widget.js';
    
    public function __construct() {
        add_action('wp_footer', array($this, 'add_chat_widget'));
        add_action('admin_menu', array($this, 'admin_menu'));
    }
    
    public function add_chat_widget() {
        if (is_admin()) return; // No mostrar en admin
        
        $config = get_option('lucas_widget_config', array(
            'position' => 'bottom-right',
            'auto_open' => false,
            'theme' => 'blue'
        ));
        
        ?>
        <script>
            window.LUCAS_WIDGET_CONFIG = {
                apiUrl: '<?php echo $this->api_url; ?>',
                position: '<?php echo $config['position']; ?>',
                autoOpen: <?php echo $config['auto_open'] ? 'true' : 'false'; ?>,
                theme: '<?php echo $config['theme']; ?>'
            };
        </script>
        <script src="<?php echo $this->widget_url; ?>" 
                data-api-url="<?php echo $this->api_url; ?>"
                data-position="<?php echo $config['position']; ?>"
                data-auto-open="<?php echo $config['auto_open'] ? 'true' : 'false'; ?>">
        </script>
        <?php
    }
    
    public function admin_menu() {
        add_options_page(
            'Lucas Chat Widget', 
            'Chat Widget', 
            'manage_options', 
            'lucas-chat-widget', 
            array($this, 'admin_page')
        );
    }
    
    public function admin_page() {
        if (isset($_POST['submit'])) {
            $config = array(
                'position' => sanitize_text_field($_POST['position']),
                'auto_open' => isset($_POST['auto_open']),
                'theme' => sanitize_text_field($_POST['theme'])
            );
            update_option('lucas_widget_config', $config);
            echo '<div class="notice notice-success"><p>Configuración guardada!</p></div>';
        }
        
        $config = get_option('lucas_widget_config', array(
            'position' => 'bottom-right',
            'auto_open' => false,
            'theme' => 'blue'
        ));
        
        ?>
        <div class="wrap">
            <h1>Lucas Chat Widget</h1>
            <form method="post">
                <table class="form-table">
                    <tr>
                        <th>Posición</th>
                        <td>
                            <select name="position">
                                <option value="bottom-right" <?php selected($config['position'], 'bottom-right'); ?>>Abajo Derecha</option>
                                <option value="bottom-left" <?php selected($config['position'], 'bottom-left'); ?>>Abajo Izquierda</option>
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <th>Abrir Automáticamente</th>
                        <td>
                            <input type="checkbox" name="auto_open" <?php checked($config['auto_open']); ?> />
                            <label>Abrir el chat automáticamente después de 2 segundos</label>
                        </td>
                    </tr>
                    <tr>
                        <th>Tema</th>
                        <td>
                            <select name="theme">
                                <option value="blue" <?php selected($config['theme'], 'blue'); ?>>Azul</option>
                                <option value="green" <?php selected($config['theme'], 'green'); ?>>Verde</option>
                                <option value="red" <?php selected($config['theme'], 'red'); ?>>Rojo</option>
                            </select>
                        </td>
                    </tr>
                </table>
                <?php submit_button(); ?>
            </form>
            
            <h2>Estado del Servidor</h2>
            <p>API URL: <code><?php echo $this->api_url; ?></code></p>
            <p>Widget URL: <code><?php echo $this->widget_url; ?></code></p>
            
            <div id="server-status">Verificando conexión...</div>
            
            <script>
                fetch('<?php echo $this->api_url; ?>/')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('server-status').innerHTML = 
                            '<span style="color: green;">✅ Servidor conectado</span><br>' +
                            '<strong>Versión:</strong> ' + data.version + '<br>' +
                            '<strong>Agent:</strong> ' + (data.agent_active ? 'Activo' : 'Inactivo');
                    })
                    .catch(error => {
                        document.getElementById('server-status').innerHTML = 
                            '<span style="color: red;">❌ Error de conexión: ' + error.message + '</span>';
                    });
            </script>
        </div>
        <?php
    }
}

// Inicializar plugin
new LucasChatWidget();
?>
```

## 🎨 **Personalización**

### **Colores y Estilos**

Puedes personalizar el widget modificando las variables CSS:

```javascript
// En el archivo JavaScript del widget
const customTheme = {
    primary_color: "#YOUR_COLOR",     // Color principal
    secondary_color: "#F3F4F6",       // Color secundario  
    text_color: "#1F2937",            // Color de texto
    border_radius: "12px"             // Radio de bordes
};
```

### **Configuraciones Disponibles**

```javascript
window.LUCAS_WIDGET_CONFIG = {
    apiUrl: 'https://tu-servidor.com/api',  // URL de tu API
    position: 'bottom-right',               // 'bottom-right' | 'bottom-left'
    autoOpen: false,                        // true para abrir automáticamente
    theme: 'blue',                          // 'blue' | 'green' | 'red'
    
    // Configuraciones avanzadas
    welcomeMessage: "¡Hola! ¿En qué puedo ayudarte?",
    placeholder: "Escribe tu mensaje...",
    showPoweredBy: true,
    enableTypingIndicator: true,
    maxMessages: 50,  // Límite de mensajes en memoria
};
```

## 🚀 **Deploy en Producción**

### **1. Servidor en la Nube**

```bash
# 1. Deploy del servidor API
# (Usar Railway, Heroku, DigitalOcean, etc.)

# 2. Actualizar URLs en WordPress
# Cambiar localhost por tu dominio real:
apiUrl: 'https://tu-dominio.com/api'
widgetUrl: 'https://tu-dominio.com/static/widget/lucas-chat-widget.js'
```

### **2. Variables de Entorno en Producción**

```env
OPENAI_API_KEY=tu-openai-key
BREVO_API_KEY=tu-brevo-key
WIDGET_API_URL=https://tu-dominio.com/api
WIDGET_STATIC_URL=https://tu-dominio.com
```

### **3. CORS en Producción**

Actualizar la configuración CORS en `widget_api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tu-sitio-wordpress.com",
        "https://www.tu-sitio-wordpress.com",
        "https://lucasbenites.com",  # Tu dominio
        # Remover "*" en producción
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

## 📊 **Monitoreo y Analytics**

El widget automáticamente rastrea:

- ✅ Conversaciones por sesión
- ✅ Páginas donde se inicia el chat  
- ✅ Referrers y user agents
- ✅ Tiempo de respuesta del agente
- ✅ Tasa de conversión a meeting links

## 🔧 **Troubleshooting**

### **Problemas Comunes**

1. **Widget no aparece**
   - Verificar que el servidor esté corriendo
   - Revisar consola del navegador por errores
   - Confirmar que las URLs sean correctas

2. **CORS Error**
   - Agregar tu dominio WordPress a la lista de allow_origins
   - Verificar que HTTPS esté configurado correctamente

3. **Mensajes no se envían**
   - Verificar conexión a OpenAI API
   - Revisar logs del servidor
   - Confirmar que la base de datos esté accesible

### **Testing Local**

```bash
# 1. Ejecutar servidor
python server_widget.py

# 2. Probar endpoints
curl http://localhost:8000/
curl http://localhost:8000/api/widget/config

# 3. Probar widget en HTML local
# Crear archivo test.html con el código de embed
```

## 📞 **Soporte**

Para ayuda con la integración:
- 📧 Email: lucas@lucasbenites.com
- 💬 WhatsApp: +54 3517554495
- 🔗 Calendario: https://meet.brevo.com/lucas-benites