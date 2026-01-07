@echo off
chcp 65001 >nul
cls

echo.
echo ===============================================================
echo          SCAM AI - TOKEN TESTING TOOL
echo ===============================================================
echo.
echo This script will help you test the tool.
echo.
echo STEPS:
echo 1. Open https://pump.fun in your browser
echo 2. Click on any token
echo 3. Copy the token address (click "Copy CA" or from URL)
echo 4. Come back here and paste the address
echo.
echo ===============================================================
echo.
pause
echo.

:input
echo Paste the token address:
set /p token=

if "%token%"=="" (
    echo.
    echo Error: You must enter an address!
    echo.
    goto input
)

echo.
echo Analyzing: %token%
echo.
echo ===============================================================
echo.

python main.py %token%

echo.
echo ===============================================================
echo.
echo Analysis complete!
echo.
choice /C YN /M "Do you want to analyze another token"

if errorlevel 2 goto end
if errorlevel 1 (
    cls
    goto input
)

:end
echo.
echo Goodbye!
timeout /t 2 >nul
