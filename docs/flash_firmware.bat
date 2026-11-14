@echo off
echo =======================================================
echo  Flashing ECG Stress Telemetry Firmware to STM32G474RE
echo =======================================================

set PROG="C:\ST\STM32CubeIDE_2.2.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.cubeprogrammer.win32_2.2.500.202603051304\tools\bin\STM32_Programmer_CLI.exe"
set BIN="%~dp0embedded_stm32\STM32G474_HC1_Telemetry.bin"

if not exist %BIN% (
    set BIN="%~dp0STM32G474_ECG_Telemetry\STM32G474_ECG_Telemetry.bin"
)

if not exist %BIN% (
    echo [ERROR] Binary file not found: %BIN%
    pause
    exit /b 1
)

echo [1/2] Connecting to STM32G474RE via ST-LINK SWD...
%PROG% -c port=SWD -w %BIN% 0x08000000 -v -rst
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Flashing failed! Ensure board is plugged in via USB.
    pause
    exit /b 1
)

echo.
echo =======================================================
echo  Flash complete! ECG Telemetry is running on COM10.
echo =======================================================
pause
