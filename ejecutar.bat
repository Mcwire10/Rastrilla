@echo off
chcp 65001 >nul
title Intereses Moratorios RASTRILLA
powershell -ExecutionPolicy Bypass -Command "Set-Location '%~dp0'; python -m streamlit run app.py --server.headless false"
pause
