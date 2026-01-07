@echo off
chcp 65001 >nul
color 0A
cls

echo ===============================================================
echo          INSTALLATION - SCAM AI SCANNER
echo ===============================================================
echo.
echo This script will install all necessary dependencies.
echo.
pause

echo.
echo [1/3] Checking Python...
python --version
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Install Python from: https://www.python.org/downloads/
    echo Do not forget to check Add Python to PATH!
    echo.
    pause
    exit /b 1
)

echo.
echo [2/3] Updating pip...
python -m pip install --upgrade pip

echo.
echo [3/3] Installing dependencies...
pip install -r requirements.txt

echo.
echo Installation completed successfully!
echo.
echo To use the tool:
echo 1. Double-click on analyser.bat
echo 2. Or use: python main.py token_address
echo.
echo ===============================================================
echo.
pause
