# Script para activar venv sin conda
Write-Host "Activando entorno virtual venv..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"
Write-Host "Entorno venv activado correctamente!" -ForegroundColor Green
Write-Host ""
Write-Host "Para ejecutar la aplicacion:" -ForegroundColor Yellow
Write-Host "  python main.py                 (Dashboard Gradio)" -ForegroundColor Cyan
Write-Host "  python server_widget.py        (Widget WordPress)" -ForegroundColor Cyan  
Write-Host "  python server_production.py    (Solo API)" -ForegroundColor Cyan