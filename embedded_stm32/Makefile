# ==============================================================================
# Makefile for STM32G474RE HC1 M-4DCHS ECG Telemetry Firmware
# Target: NUCLEO-G474RE (ARM Cortex-M4 @ 170 MHz SYSCLK)
# ==============================================================================

TOOLCHAIN ?= C:/ST/STM32CubeIDE_2.2.0/STM32CubeIDE/plugins/com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.14.3.rel1.win32_1.0.100.202602081740/tools/bin
CC      := $(TOOLCHAIN)/arm-none-eabi-gcc
OBJCOPY := $(TOOLCHAIN)/arm-none-eabi-objcopy
SIZE    := $(TOOLCHAIN)/arm-none-eabi-size

PROGRAMMER ?= C:/ST/STM32CubeIDE_2.2.0/STM32CubeIDE/plugins/com.st.stm32cube.ide.mcu.externaltools.cubeprogrammer.win32_2.2.500.202603051304/tools/bin/STM32_Programmer_CLI.exe

TARGET := STM32G474_HC1_Telemetry
BUILD_DIR := build

SRCS := \
	src/main_stm32.c \
	src/ecg_dsp_filter.c \
	src/telemetry_protocol.c \
	src/wesad_test_samples.c \
	src/syscalls.c \
	src/sysmem.c \
	src/startup_stm32g474retx.s

INCLUDES := -Iinclude

MCU_FLAGS := -mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb
CFLAGS    := $(MCU_FLAGS) -O2 -ffp-contract=off -Wall -fdata-sections -ffunction-sections $(INCLUDES)
LDFLAGS   := $(MCU_FLAGS) -T STM32G474RETX_FLASH.ld -Wl,--gc-sections \
             -specs=nano.specs -specs=nosys.specs -lc -lm -lnosys \
             -Wl,-Map=$(TARGET).map

all: $(TARGET).bin

$(TARGET).elf: $(SRCS) STM32G474RETX_FLASH.ld
	$(CC) $(CFLAGS) $(SRCS) $(LDFLAGS) -o $@
	$(SIZE) $@

$(TARGET).bin: $(TARGET).elf
	$(OBJCOPY) -O binary $< $@

flash: $(TARGET).bin
	$(PROGRAMMER) -c port=SWD -w $(TARGET).bin 0x08000000 -v -rst

clean:
	@cmd /c "del /f /q $(TARGET).elf $(TARGET).bin $(TARGET).map 2>nul" || rm -f $(TARGET).elf $(TARGET).bin $(TARGET).map

.PHONY: all flash clean
