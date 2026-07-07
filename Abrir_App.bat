@echo off
rem Arranca el servidor local de la app de Control de Calidad y abre el navegador.
rem No cierres esta ventana mientras uses la app.
cd /d "%~dp0"
py servidor.py
pause
