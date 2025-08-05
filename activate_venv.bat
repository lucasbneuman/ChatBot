@echo off
echo Activando entorno virtual venv...
call venv\Scripts\activate.bat
echo Entorno virtual activado!
echo.
echo Para ejecutar la aplicacion:
echo   python main.py                 (Dashboard Gradio)
echo   python server_widget.py        (Widget WordPress)  
echo   python server_production.py    (Solo API)
echo.
cmd /k