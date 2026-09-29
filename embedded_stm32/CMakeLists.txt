cmake_minimum_required(VERSION 3.20)
project(STM32G474_HC1_Telemetry C ASM)

set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)

set(MCU_FLAGS "-mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb")
set(CMAKE_C_FLAGS "${MCU_FLAGS} -O2 -Wall -fdata-sections -ffunction-sections")
set(CMAKE_ASM_FLAGS "${MCU_FLAGS}")

include_directories(include)

set(SOURCES
    src/main_stm32.c
    src/ecg_dsp_filter.c
    src/telemetry_protocol.c
    src/wesad_test_samples.c
    src/syscalls.c
    src/sysmem.c
    src/startup_stm32g474retx.s
)

add_executable(${PROJECT_NAME}.elf ${SOURCES})

set_target_properties(${PROJECT_NAME}.elf PROPERTIES
    LINK_FLAGS "${MCU_FLAGS} -T ${CMAKE_CURRENT_SOURCE_DIR}/STM32G474RETX_FLASH.ld -Wl,--gc-sections -specs=nano.specs -specs=nosys.specs -lc -lm -lnosys -Wl,-Map=${PROJECT_NAME}.map"
)

add_custom_command(TARGET ${PROJECT_NAME}.elf POST_BUILD
    COMMAND arm-none-eabi-objcopy -O binary ${PROJECT_NAME}.elf ${PROJECT_NAME}.bin
    COMMAND arm-none-eabi-size ${PROJECT_NAME}.elf
    COMMENT "Building raw binary image..."
)
