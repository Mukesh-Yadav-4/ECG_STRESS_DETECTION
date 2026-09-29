@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo  Compiling and Flashing HC1 Firmware to STM32G474RE
echo =======================================================

set "TOOLCHAIN=C:\ST\STM32CubeIDE_2.2.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.14.3.rel1.win32_1.0.100.202602081740\tools\bin"
set "PROG=C:\ST\STM32CubeIDE_2.2.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.cubeprogrammer.win32_2.2.500.202603051304\tools\bin\STM32_Programmer_CLI.exe"

set CC="%TOOLCHAIN%\arm-none-eabi-gcc.exe"
set OBJCOPY="%TOOLCHAIN%\arm-none-eabi-objcopy.exe"
set SIZE="%TOOLCHAIN%\arm-none-eabi-size.exe"

set CFLAGS=-mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -O2 -ffp-contract=off -Wall -fdata-sections -ffunction-sections -Iinclude
set LDFLAGS=-mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -T STM32G474RETX_FLASH.ld -Wl,--gc-sections -specs=nano.specs -specs=nosys.specs -lc -lm -lnosys -Wl,-Map=STM32G474_HC1_Telemetry.map

echo [1/3] Compiling firmware sources...
%CC% %CFLAGS% src/main_stm32.c src/ecg_dsp_filter.c src/telemetry_protocol.c src/wesad_test_samples.c src/syscalls.c src/sysmem.c src/startup_stm32g474retx.s %LDFLAGS% -o STM32G474_HC1_Telemetry.elf
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Compilation failed!
    exit /b 1
)

echo [2/3] Extracting raw binary image...
%OBJCOPY% -O binary STM32G474_HC1_Telemetry.elf STM32G474_HC1_Telemetry.bin
%SIZE% STM32G474_HC1_Telemetry.elf

echo [3/3] Flashing to STM32G474RE via SWD...
%PROG% -c port=SWD -w STM32G474_HC1_Telemetry.bin 0x08000000 -v -rst
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Flashing failed!
    exit /b 1
)

echo.
echo =======================================================
echo  SUCCESS: HC1 Firmware Flashed ^& Streaming on COM10!
echo =======================================================
