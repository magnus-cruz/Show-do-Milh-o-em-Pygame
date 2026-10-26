@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0.."
set "PYTHON_CMD="

call :selecionar_python
if not defined PYTHON_CMD (
    echo [ERRO] Python 3.8 ou superior nao foi encontrado.
    echo.
    where winget >nul 2>&1
    if errorlevel 1 (
        echo Instale o Python pelo site oficial:
        echo https://www.python.org/downloads/windows/
    ) else (
        echo Instalando Python com o winget...
        winget install --id Python.Python.3.12 --exact --source winget
        if errorlevel 1 (
            echo [ERRO] Nao foi possivel instalar o Python com o winget.
            echo Baixe-o manualmente em: https://www.python.org/downloads/windows/
            exit /b 1
        )
        echo.
        echo Feche e reabra este terminal para atualizar o PATH e execute este script novamente.
    )
    exit /b 1
)

echo Python compativel encontrado: %PYTHON_CMD%
if not exist ".venv\Scripts\python.exe" (
    echo Criando o ambiente virtual em .venv...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo [ERRO] Nao foi possivel criar o ambiente virtual.
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERRO] Nao foi possivel ativar o ambiente virtual.
    exit /b 1
)

> requirements.txt echo pygame

echo Atualizando o pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERRO] Falha ao atualizar o pip.
    exit /b 1
)

echo Instalando as dependencias...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar as dependencias.
    exit /b 1
)

echo.
where powershell >nul 2>&1
if not errorlevel 1 (
    powershell -NoProfile -Command "Write-Host '========================================' -ForegroundColor Green; Write-Host ' Ambiente configurado com sucesso!' -ForegroundColor Green; Write-Host '========================================' -ForegroundColor Green"
) else (
    echo ========================================
    echo  Ambiente configurado com sucesso!
    echo ========================================
)
echo.
echo Execute o jogo neste terminal com:
echo     python main.py
echo.
exit /b 0

:selecionar_python
where py >nul 2>&1
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=py -3"
        exit /b 0
    )
)

where python >nul 2>&1
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)
exit /b 0
