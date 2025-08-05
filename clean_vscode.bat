@echo off
echo ==========================================
echo LIMPIANDO CONFIGURACION VSCODE
echo ==========================================

echo.
echo 1. Cerrando VSCode si esta abierto...
taskkill /f /im code.exe 2>nul

echo.
echo 2. Eliminando cache de Python en VSCode...
if exist "%APPDATA%\Code\User\workspaceStorage" (
    echo Limpiando workspace storage...
    for /d %%i in ("%APPDATA%\Code\User\workspaceStorage\*") do (
        if exist "%%i\state.vscdb" del "%%i\state.vscdb" 2>nul
    )
)

echo.
echo 3. Eliminando configuracion de interprete Python...
if exist "%APPDATA%\Code\User\settings.json" (
    echo Backup de settings.json creado
    copy "%APPDATA%\Code\User\settings.json" "%APPDATA%\Code\User\settings.json.backup"
)

echo.
echo 4. Creando nueva configuracion limpia...
cd /d "C:\Users\avali\Desktop\Proyectos\agents"

echo.
echo 5. Forzando uso de venv...
if exist ".vscode\settings.json" (
    echo Configuracion .vscode ya existe, actualizando...
) else (
    mkdir .vscode 2>nul
)

echo.
echo ==========================================
echo CONFIGURACION LIMPIADA
echo AHORA REINICIA VSCODE COMPLETAMENTE
echo ==========================================
pause