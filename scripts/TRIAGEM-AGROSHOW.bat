@echo off
chcp 65001 >nul
setlocal

rem Atalho de duplo clique para a triagem do footage de drone da AGROSHOW 2026.
rem Deixe este arquivo NA MESMA PASTA que extrair_quadros.py e clique duas vezes.
rem Da tambem para arrastar a pasta dos videos por cima deste arquivo.

title Triagem do footage - AGROSHOW 2026

set "SCRIPT=%~dp0extrair_quadros.py"
set "PASTA=%~1"
if "%PASTA%"=="" set "PASTA=E:\Projetos todos\Mapa - agroshow"

echo ==============================================================
echo   TRIAGEM DO FOOTAGE DE DRONE -- AGROSHOW 2026
echo ==============================================================
echo.
echo   script : %SCRIPT%
echo   videos : %PASTA%
echo.

if not exist "%SCRIPT%" (
    echo ERRO: extrair_quadros.py nao esta nesta pasta.
    echo Coloque os dois arquivos juntos e tente de novo.
    goto :fim
)
if not exist "%PASTA%" (
    echo ERRO: pasta de videos nao encontrada.
    echo Arraste a pasta dos videos por cima deste arquivo .bat.
    goto :fim
)

rem Alguns Windows so tem o lancador "py"; outros so tem "python".
set "PY="
where python >nul 2>&1 && set "PY=python"
if not defined PY where py >nul 2>&1 && set "PY=py -3"
if not defined PY (
    echo ERRO: Python nao encontrado.
    echo   winget install Python.Python.3.12
    goto :fim
)

where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo ERRO: ffmpeg nao encontrado no PATH.
    echo   winget install Gyan.FFmpeg
    echo Depois FECHE e reabra esta janela, para o PATH atualizar.
    goto :fim
)

echo [1 de 2] Metadados e telemetria...
echo.
%PY% "%SCRIPT%" --metadados --pasta "%PASTA%" --saida "%PASTA%\_triagem"

echo.
echo [2 de 2] Triagem, 10 quadros por video...
echo.
%PY% "%SCRIPT%" --triagem --pasta "%PASTA%" --saida "%PASTA%\_triagem"

echo.
echo ==============================================================
echo   Pronto. O resultado esta em:
echo   %PASTA%\_triagem
echo.
echo   Anexe no chat: as FOLHA_*.jpg e, se existirem, os .srt da
echo   pasta _triagem\metadados.
echo ==============================================================

:fim
echo.
pause
endlocal
