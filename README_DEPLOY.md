# Deploy Lucas Widget con Gradio Dashboard

## Render Deploy:
1. Build Command: `pip install -r requirements.txt`
2. Start Command: `python server_production.py`

## Variables de entorno necesarias:
- OPENAI_API_KEY=tu-clave
- BREVO_API_KEY=tu-clave
- ENABLE_GRADIO=true (para desarrollo local)
- RENDER=true (en Render - desactiva Gradio por memoria)

## Endpoints:
- API: /api/
- Widget embed: /widget/embed
- Health: /health
- Admin Dashboard: puerto dinámico (7863+) - solo local

## Notas:
- Gradio se desactiva automáticamente en Render por limitaciones de memoria
- En desarrollo local tendrás ambos: Widget API + Dashboard
- En producción solo Widget API funciona