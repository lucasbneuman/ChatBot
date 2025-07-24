# Tests

## test_supervisor_flow.py

Test completo de la nueva arquitectura con supervisor.

### Qué prueba:
- **test_supervisor_complete_flow()**: Flujo completo de prospección con supervisor
- **test_info_request()**: Consultas de información específicas (RAG)
- **test_prospecting_flow()**: Flujo puro de prospección con validación de datos

### Para ejecutar:
```bash
cd test
python test_supervisor_flow.py
```

### Qué debe pasar:
- ✓ Supervisor inicializado correctamente
- ✓ RAG system activo
- ✓ Intent detection funcionando (info_request vs prospecting)
- ✓ Datos extraídos sin corrupción
- ✓ Base de datos robusta
- ✓ Validación de responses activa

Si todos los tests pasan, la nueva arquitectura está funcionando correctamente.