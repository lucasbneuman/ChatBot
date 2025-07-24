# 🚀 Deploy en Render - Guía Paso a Paso

## 📋 **Preparación del Código**

### Paso 1: Commit y Push
```bash
git add .
git commit -m "Preparado para deploy en Render"
git push origin main
```

## 🌐 **Deploy en Render**

### Paso 2: Crear Web Service
1. Ve a: **https://render.com/**
2. Inicia sesión / Créate una cuenta
3. Click **"New"** → **"Web Service"**
4. Conecta tu repositorio de GitHub
5. Selecciona el repositorio `agents`

### Paso 3: Configuración del Servicio
```
Name: lucas-benites-widget
Runtime: Python 3
Build Command: pip install -r requirements_production.txt
Start Command: python server_production.py
```

### Paso 4: Variables de Entorno
En la sección **"Environment Variables"**, añade:

```
OPENAI_API_KEY=sk-tu-clave-openai-aqui
BREVO_API_KEY=xkeysib-tu-clave-brevo-aqui
ENABLE_GRADIO=false
RENDER=true
PORT=10000
HOST=0.0.0.0
```

**⚠️ IMPORTANTE**: 
- Reemplaza `sk-tu-clave-openai-aqui` con tu clave real de OpenAI
- Reemplaza `xkeysib-tu-clave-brevo-aqui` con tu clave real de Brevo
- `ENABLE_GRADIO=false` porque el plan gratuito tiene poca memoria

### Paso 5: Deploy
1. Click **"Create Web Service"**
2. Render comenzará el build automáticamente
3. Espera 5-10 minutos para que termine

## 🎯 **Después del Deploy**

### Tu URL será algo como:
```
https://lucas-benites-widget.onrender.com
```

### Paso 6: Probar la API
Ve a tu URL + `/health`:
```
https://tu-app.onrender.com/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "version": "2.0.0"
}
```

### Paso 7: Obtener código para WordPress
Ve a tu URL + `/widget/embed`:
```
https://tu-app.onrender.com/widget/embed
```

Esto te dará el código JavaScript listo para WordPress.

## 🔧 **Configurar WordPress**

### Paso 8: Instalar Plugin
1. Ve a tu WordPress Admin
2. **Plugins** → **Añadir nuevo**
3. Busca **"Insert Headers and Footers"**
4. Instala y activa

### Paso 9: Añadir Widget
1. **Ajustes** → **Insert Headers and Footers**
2. En **"Scripts in Footer"**, pega el código de `/widget/embed`
3. **Guardar cambios**

### El código se verá así:
```html
<!-- Lucas Benites Chat Widget -->
<script>
    window.LUCAS_WIDGET_CONFIG = {
        apiUrl: 'https://tu-app.onrender.com/api',
        position: 'bottom-right',
        autoOpen: false,
        theme: 'blue'
    };
</script>
<script src="https://tu-app.onrender.com/static/widget/lucas-chat-widget.js" 
        data-api-url="https://tu-app.onrender.com/api"
        data-position="bottom-right"
        data-auto-open="false">
</script>
```

## ✅ **Verificar que Funciona**

### Paso 10: Testing
1. **Prueba la API**: `https://tu-app.onrender.com/api/`
2. **Ve tu WordPress**: Busca el botón azul flotante
3. **Haz clic y chatea**: Prueba enviar mensajes
4. **Revisa logs**: En Render Dashboard → Logs

## ⚠️ **Limitaciones del Plan Gratuito**

- **750 horas/mes** (suficiente para pruebas)
- **Se duerme tras 15 min sin uso** (primer request tarda ~30 seg)
- **No Gradio Dashboard** (por memoria limitada)
- **Solo HTTPS** (HTTP no funciona)

## 🆘 **Troubleshooting**

### Si el widget no aparece:
1. **Revisar CORS**: Las URLs de WordPress deben estar permitidas
2. **Verificar HTTPS**: Solo funciona con HTTPS
3. **Revisar consola**: F12 → Console para errores JavaScript

### Si la API no responde:
1. **Verificar variables**: En Render Dashboard → Environment
2. **Revisar logs**: Deploy logs y Application logs
3. **Verificar build**: Que todas las dependencias se instalaron

### URLs importantes:
- **API Health**: `https://tu-app.onrender.com/health`
- **Widget API**: `https://tu-app.onrender.com/api/`
- **Código embed**: `https://tu-app.onrender.com/widget/embed`
- **Render Dashboard**: https://dashboard.render.com/

## 🎉 **¡Listo!**

Una vez completados estos pasos, tendrás:
- ✅ API funcionando en la nube
- ✅ Widget integrado en WordPress  
- ✅ Chat inteligente con RAG y Brevo
- ✅ Sistema de prospección automático