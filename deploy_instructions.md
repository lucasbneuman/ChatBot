# 🚀 Instrucciones de Deploy - Lucas Benites Multi-Channel

## 📋 **Opción 1: Railway (RECOMENDADO)**

### Paso 1: Preparar el código
```bash
git add .
git commit -m "Preparado para producción"
git push origin main
```

### Paso 2: Deploy en Railway
1. Ve a: https://railway.app/
2. Conecta tu cuenta GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Selecciona tu repositorio
5. Railway detectará automáticamente el Dockerfile

### Paso 3: Configurar variables de entorno
En Railway Dashboard → Variables:
```
OPENAI_API_KEY=sk-tu-clave-aqui
BREVO_API_KEY=xkeysib-tu-clave-aqui
WIDGET_BASE_URL=https://tu-proyecto.railway.app
ENABLE_GRADIO=true
```

### Paso 4: Obtener URL de producción
Railway te dará una URL como: `https://lucas-widget-production.railway.app`

---

## 📋 **Opción 2: Render**

### Paso 1: Preparar
- Mismo código que Railway
- Archivo `render.yaml` ya incluido

### Paso 2: Deploy en Render
1. Ve a: https://render.com/
2. "New" → "Web Service"
3. Conecta GitHub
4. Configurar:
   - Build Command: `pip install -r requirements_production.txt`
   - Start Command: `python server_production.py`

---

## 📋 **Opción 3: Heroku**

### Paso 1: Crear Procfile
```
web: python server_production.py
```

### Paso 2: Deploy
```bash
heroku create lucas-widget-app
heroku config:set OPENAI_API_KEY=tu-clave
heroku config:set BREVO_API_KEY=tu-clave
git push heroku main
```

---

## 🔧 **Configuración WordPress**

### Una vez deployado:

1. **Obtén el código embed:**
   - Ve a: `https://tu-dominio.railway.app/widget/embed`
   - Copia el código JavaScript

2. **Instala plugin en WordPress:**
   - "Insert Headers and Footers" o similar

3. **Pega el código:**
   - WordPress Admin → Settings → Insert Headers and Footers
   - Pegar en "Scripts in Footer"
   - Guardar

### El código se verá así:
```html
<!-- Lucas Benites Chat Widget -->
<script>
    window.LUCAS_WIDGET_CONFIG = {
        apiUrl: 'https://tu-dominio.railway.app/api',
        position: 'bottom-right',
        autoOpen: false,
        theme: 'blue'
    };
</script>
<script src="https://tu-dominio.railway.app/static/widget/lucas-chat-widget.js" 
        data-api-url="https://tu-dominio.railway.app/api"
        data-position="bottom-right"
        data-auto-open="false">
</script>
```

---

## 🎯 **URLs importantes tras el deploy:**

- **Widget API**: `https://tu-dominio/api/`
- **Código embed**: `https://tu-dominio/widget/embed`
- **Health check**: `https://tu-dominio/health`
- **Dashboard Admin**: `https://tu-dominio:7860` (si ENABLE_GRADIO=true)

---

## 🔍 **Testing después del deploy:**

1. **Probar API**: `curl https://tu-dominio/health`
2. **Probar widget**: Crear página HTML de prueba
3. **Probar WordPress**: Instalar código embed
4. **Monitorear logs**: En dashboard de Railway/Render

---

## ⚠️ **Notas importantes:**

- **CORS**: Las URLs de WordPress deben estar en ALLOWED_ORIGINS
- **HTTPS**: Solo funciona con HTTPS en producción
- **Variables de entorno**: Nunca subas claves al código
- **Base de datos**: Se reinicia en cada deploy (normal para SQLite)

## 🆘 **Troubleshooting:**

- **Widget no aparece**: Verificar CORS y URLs
- **API no responde**: Revisar variables de entorno
- **Errores 500**: Verificar logs en platform dashboard