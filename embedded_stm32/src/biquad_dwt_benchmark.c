/**
 * @file biquad_dwt_benchmark.c
 * @brief Standalone hardware DWT->CYCCNT benchmark for the 5-stage Biquad IIR Filter.
 * Target: STMicroelectronics NUCLEO-G474RE (ARM Cortex-M4 @ 170 MHz).
 * 
 * Measures exact execution cycle counts for 1,000 trials of ecg_filter_process_sample()
 * and reports min, mean, max cycles and microseconds at 170 MHz over USART2 (115200 baud).
 */

#include "main.h"
#include "ecg_dsp_filter.h"
#include "wesad_test_samples.h"
#include <stdio.h>
#include <string.h>

#define NUM_BENCH_TRIALS 1000

/* CoreDebug and DWT Register Definitions for Cortex-M4 */
#define CoreDebug_DEMCR         (*(volatile uint32_t *)0xE000EDFC)
#define CoreDebug_DEMCR_TRCENA  (1UL << 24)

#define DWT_CTRL                (*(volatile uint32_t *)0xE0001000)
#define DWT_CTRL_CYCCNTENA      (1UL << 0)
#define DWT_CYCCNT              (*(volatile uint32_t *)0xE0001004)

UART_HandleTypeDef huart2;

void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART2_UART_Init(void);
static void uart_print(const char *str);

volatile uint32_t g_millis = 0;

void SysTick_Handler(void)
{
    g_millis++;
}

void SystemInit(void)
{
    /* Enable CP10 and CP11 Full Access for ARM Cortex-M4 Hardware FPU */
    SCB_CPACR |= ((3UL << 20) | (3UL << 22));
}

static void delay_ms(uint32_t ms)
{
    /* at 170 MHz, ~170,000 cycles per ms */
    for (volatile uint32_t i = 0; i < ms; i++) {
        for (volatile uint32_t j = 0; j < 25000; j++) {
            __asm volatile ("nop");
        }
    }
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    MX_GPIO_Init();
    MX_USART2_UART_Init();

    /* Enable DWT Cycle Counter */
    CoreDebug_DEMCR |= CoreDebug_DEMCR_TRCENA;
    DWT_CYCCNT = 0;
    DWT_CTRL |= DWT_CTRL_CYCCNTENA;

    /* Initialize 5-stage Biquad Filter */
    ecg_biquad_instance_f32 filter;
    float filter_state[4 * ECG_FILTER_NUM_STAGES];
    ecg_filter_init(&filter, filter_state, 350);

    /* Turn on User Green LED (LD2, PA5) */
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);

    /* Give UART terminal time to attach */
    delay_ms(500);

    uart_print("\r\n=======================================================\r\n");
    uart_print("STM32G474RE 5-STAGE BIQUAD CASCADE DWT->CYCCNT BENCHMARK\r\n");
    uart_print("Core: ARM Cortex-M4 @ 170 MHz (Hardware FPU Enabled)\r\n");
    uart_print("Trials: 1000\r\n");
    uart_print("=======================================================\r\n");

    /* Warm-up run */
    volatile float warm_dummy = ecg_filter_process_sample(&filter, 0.5f);
    (void)warm_dummy;

    uint32_t min_cycles = 0xFFFFFFFF;
    uint32_t max_cycles = 0;
    uint64_t total_cycles = 0;

    for (int i = 0; i < NUM_BENCH_TRIALS; i++)
    {
        float input_sample = WESAD_S2_RAW_ECG[i % WESAD_BENCHMARK_NUM_SAMPLES];

        uint32_t t_start = DWT_CYCCNT;
        volatile float out_sample = ecg_filter_process_sample(&filter, input_sample);
        uint32_t t_end = DWT_CYCCNT;
        (void)out_sample;

        uint32_t elapsed = t_end - t_start;
        if (elapsed < min_cycles) min_cycles = elapsed;
        if (elapsed > max_cycles) max_cycles = elapsed;
        total_cycles += elapsed;
    }

    uint32_t mean_cycles = (uint32_t)(total_cycles / NUM_BENCH_TRIALS);

    /* Microseconds at 170 MHz (clock period = 5.882 ns) */
    float min_us = (float)min_cycles / 170.0f;
    float mean_us = (float)mean_cycles / 170.0f;
    float max_us = (float)max_cycles / 170.0f;

    char buf[128];

    /* Repeat report every 1 second over UART so host capture never misses it */
    while (1)
    {
        uart_print("\r\n=======================================================\r\n");
        uart_print("STM32G474RE 5-STAGE BIQUAD CASCADE DWT->CYCCNT BENCHMARK\r\n");
        uart_print("Core: ARM Cortex-M4 @ 170 MHz (Hardware FPU Enabled)\r\n");
        uart_print("Trials: 1000\r\n");
        uart_print("=======================================================\r\n");
        snprintf(buf, sizeof(buf), "5-Stage Biquad Cascade (1000 trials):\r\n");
        uart_print(buf);
        snprintf(buf, sizeof(buf), "Min  Cycles: %lu (%lu.%03lu us @ 170 MHz)\r\n",
                 min_cycles, min_cycles / 170, (uint32_t)(((uint64_t)min_cycles * 1000 / 170) % 1000));
        uart_print(buf);
        snprintf(buf, sizeof(buf), "Mean Cycles: %lu (%lu.%03lu us @ 170 MHz)\r\n",
                 mean_cycles, mean_cycles / 170, (uint32_t)(((uint64_t)mean_cycles * 1000 / 170) % 1000));
        uart_print(buf);
        snprintf(buf, sizeof(buf), "Max  Cycles: %lu (%lu.%03lu us @ 170 MHz)\r\n",
                 max_cycles, max_cycles / 170, (uint32_t)(((uint64_t)max_cycles * 1000 / 170) % 1000));
        uart_print(buf);
        uart_print("=======================================================\r\n");
        uart_print("BIQUAD_DWT_BENCHMARK_DONE\r\n");

        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);
        delay_ms(500);
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_RESET);
        delay_ms(500);
    }
}

static void uart_print(const char *str)
{
    HAL_UART_Transmit(&huart2, (uint8_t *)str, strlen(str), 100);
}

void SystemClock_Config(void)
{
    RCC_OscInitTypeDef RCC_OscInitStruct = {0};
    RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

    HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1_BOOST);

    RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
    RCC_OscInitStruct.HSIState = RCC_HSI_ON;
    RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
    RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI;
    RCC_OscInitStruct.PLL.PLLM = RCC_PLLM_DIV4;     /* 16 / 4 = 4 MHz */
    RCC_OscInitStruct.PLL.PLLN = 85;               /* 4 * 85 = 340 MHz VCO */
    RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
    RCC_OscInitStruct.PLL.PLLQ = RCC_PLLQ_DIV2;
    RCC_OscInitStruct.PLL.PLLR = RCC_PLLR_DIV2;     /* 340 / 2 = 170 MHz SYSCLK */
    HAL_RCC_OscConfig(&RCC_OscInitStruct);

    RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK
                                | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
    RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
    RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;
    HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_4);
}

static void MX_USART2_UART_Init(void)
{
    huart2.Instance = USART2;
    huart2.Init.BaudRate = 115200;
    huart2.Init.WordLength = UART_WORDLENGTH_8B;
    huart2.Init.StopBits = UART_STOPBITS_1;
    huart2.Init.Parity = UART_PARITY_NONE;
    huart2.Init.Mode = UART_MODE_TX_RX;
    huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart2.Init.OverSampling = UART_OVERSAMPLING_16;
    huart2.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
    huart2.Init.ClockPrescaler = UART_PRESCALER_DIV1;
    huart2.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
    HAL_UART_Init(&huart2);
}

static void MX_GPIO_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();

    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_RESET);
    GPIO_InitStruct.Pin = GPIO_PIN_5;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
}
