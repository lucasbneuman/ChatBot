# 🌐 Configuración de Túnel para Probar Widget en WordPress

## Problema:
Tu servidor está en `localhost:8002` pero WordPress está en Hostinger (internet).
WordPress no puede acceder a localhost desde la web.

## Solución: Túnel ngrok (GRATIS)

### Paso 1: Descargar ngrok
1. Ve a: https://ngrok.com/
2. Créate una cuenta gratuita
3. Descarga ngrok para Windows
4. Descomprime el archivo .exe

### Paso 2: Configurar ngrok
1. En tu terminal, ve donde descargaste ngrok.exe
2. Ejecuta: `ngrok authtoken TU_TOKEN_DE_NGROK`
3. Ejecuta: `ngrok http 8002`

### Paso 3: Obtendrás una URL pública como:
```
https://abc123.ngrok.io -> http://localhost:8002
```

### Paso 4: Actualizar URLs del widget
Cambia en el código embed:
- `http://localhost:8002` por `https://abc123.ngrok.io`

### Paso 5: Código para WordPress
```html
<!-- Lucas Benites Chat Widget -->
<script>
    window.LUCAS_WIDGET_CONFIG = {
        apiUrl: 'https://TU-URL-NGROK.ngrok.io/api',
        position: 'bottom-right',
        autoOpen: false
    };
</script>
<script src="https://TU-URL-NGROK.ngrok.io/static/widget/lucas-chat-widget.js" 
        data-api-url="https://TU-URL-NGROK.ngrok.io/api"
        data-position="bottom-right"
        data-auto-open="false">
</script>
```

## Alternativa: Localtunnel (Más Simple)
```bash
npm install -g localtunnel
lt --port 8002 --subdomain lucaswidget
```