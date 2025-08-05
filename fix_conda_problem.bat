@echo off
echo ==========================================
echo ELIMINANDO CONDA DEL SISTEMA
echo ==========================================

echo.
echo 1. Removiendo conda del PATH del usuario...
setx PATH "%PATH:C:/Users/avali/anaconda3/Scripts;=%"
setx PATH "%PATH:C:\Users\avali\anaconda3\Scripts;=%"
setx PATH "%PATH:C:/Users/avali/anaconda3;=%"
setx PATH "%PATH:C:\Users\avali\anaconda3;=%"
setx PATH "%PATH:C:/Users/avali/anaconda3/condabin;=%"
setx PATH "%PATH:C:\Users\avali\anaconda3\condabin;=%"

echo.
echo 2. Removiendo variables conda...
setx CONDA_DEFAULT_ENV ""
setx CONDA_EXE ""
setx CONDA_PREFIX ""
setx CONDA_PYTHON_EXE ""
setx CONDA_SHLVL ""

echo.
echo 3. Eliminando archivos de configuracion conda...
if exist "%USERPROFILE%\.condarc" del "%USERPROFILE%\.condarc"
if exist "%USERPROFILE%\.conda" rmdir /s /q "%USERPROFILE%\.conda"

echo.
echo 4. Verificando que venv funciona...
cd /d "C:\Users\avali\Desktop\Proyectos\agents"
if exist "venv\Scripts\python.exe" (
    echo ✓ venv encontrado correctamente
    venv\Scripts\python.exe --version
) else (
    echo ✗ ERROR: venv no encontrado
)

echo.
echo ==========================================
echo REINICIA VSCode y PowerShell para aplicar cambios
echo ==========================================
pause