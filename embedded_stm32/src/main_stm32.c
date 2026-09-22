/**
 * @file main_stm32.c
 * @brief Production firmware for STM32G474 (NUCLEO-G474RE).
 * 
 * Functions:
 * 1. Timer TIM2 periodic interrupt @ 350 Hz (or 700 Hz).
 * 2. Ingestion: Replays real WESAD dataset ECG (default) or samples live ADC (PA0).
 * 3. On-Chip DSP: 5-stage CMSIS-DSP Biquad IIR filtering in real-time.
 * 4. Framing: Packages samples into 20-byte binary packets with CRC-16-CCITT.
 * 5. Telemetry: Streams packets over USART2 (ST-LINK Virtual COM Port COM10) @ 115200 baud.
 */

#include "main.h"
#include "ecg_dsp_filter.h"
#include "telemetry_protocol.h"
#include "wesad_test_samples.h"

/* Set to 0 for WESAD memory replay, or 1 for live AD8232 ADC input on PA0 */
#define USE_LIVE_AD8232_ADC  0

#define ECG_SAMPLE_RATE_HZ   350

/* Peripheral Handles */
UART_HandleTypeDef huart2;
TIM_HandleTypeDef  htim2;
ADC_HandleTypeDef  hadc1;

/* DSP and Telemetry Instances */
static ecg_biquad_instance_f32 g_ecg_filter;
static float g_filter_state[4 * ECG_FILTER_NUM_STAGES];
static telemetry_packet_t g_tx_packet;
static volatile uint16_t g_seq_counter = 0;
static volatile uint32_t g_sample_idx = 0;
static volatile uint8_t  g_timer_tick_flag = 0;

/* Private Function Prototypes */
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART2_UART_Init(void);
static void MX_TIM2_Init(void);
#if USE_LIVE_AD8232_ADC
static void MX_ADC1_Init(void);
#endif

/**
 * @brief  The application entry point.
 */
int main(void)
{
    /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
    HAL_Init();

    /* Configure the system clock to 170 MHz */
    SystemClock_Config();

    /* Initialize all configured peripherals */
    MX_GPIO_Init();
    MX_USART2_UART_Init();
    MX_TIM2_Init();
#if USE_LIVE_AD8232_ADC
    MX_ADC1_Init();
#endif

    /* Initialize CMSIS-DSP Biquad Filter (0.5–40 Hz BP + 50 Hz Notch) */
    ecg_filter_init(&g_ecg_filter, g_filter_state, ECG_SAMPLE_RATE_HZ);

    /* Turn on User Green LED (LD2) to indicate system active */
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);

    /* Start the periodic sampling timer */
    HAL_TIM_Base_Start_IT(&htim2);

    /* Infinite Main Loop */
    while (1)
    {
        /* Wait for periodic timer tick (every 2.85 ms for 350 Hz) */
        if (g_timer_tick_flag)
        {
            g_timer_tick_flag = 0;

            float raw_ecg_val = 0.0f;

#if USE_LIVE_AD8232_ADC
            /* Live analog acquisition from AD8232 on PA0 */
            HAL_ADC_Start(&hadc1);
            if (HAL_ADC_PollForConversion(&hadc1, 1) == HAL_OK)
            {
                uint32_t adc_val = HAL_ADC_GetValue(&hadc1);
                /* Convert 12-bit ADC (0..4095) to mV (0..3300 mV), centered around 1.65V */
                raw_ecg_val = (((float)adc_val * 3300.0f) / 4095.0f) - 1650.0f;
            }
#else
            /* WESAD dataset replay from internal Flash memory */
            raw_ecg_val = WESAD_S2_RAW_ECG[g_sample_idx];
            g_sample_idx = (g_sample_idx + 1) % WESAD_BENCHMARK_NUM_SAMPLES;
#endif

            /* 1. Real-time On-Chip DSP Filtering */
            float filtered_ecg_val = ecg_filter_process_sample(&g_ecg_filter, raw_ecg_val);

            /* 2. Package into 20-byte Telemetry Packet with CRC-16 */
            uint32_t ts_ms = HAL_GetTick();
            uint8_t flags = USE_LIVE_AD8232_ADC ? TELEMETRY_FLAG_LIVE_ADC : 0;
            telemetry_pack(&g_tx_packet, g_seq_counter++, ts_ms, raw_ecg_val, filtered_ecg_val, flags);

            /* 3. Transmit binary packet over ST-LINK Virtual COM Port (USART2) */
            HAL_UART_Transmit(&huart2, (uint8_t *)&g_tx_packet, sizeof(telemetry_packet_t), 10);
        }
    }
}

/**
 * @brief TIM2 Period Elapsed Callback (Fires at 350 Hz / 700 Hz)
 */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == TIM2)
    {
        g_timer_tick_flag = 1;
    }
}

/**
 * @brief System Clock Configuration: 170 MHz SYSCLK via PLL
 */
void SystemClock_Config(void)
{
    RCC_OscInitTypeDef RCC_OscInitStruct = {0};
    RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

    /* Configure the main internal regulator output voltage */
    HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1_BOOST);

    /* Initializes the RCC Oscillators: HSI = 16 MHz -> PLL = 170 MHz */
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

    /* Initializes the CPU, AHB and APB buses clocks */
    RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK
                                | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
    RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
    RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;
    HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_4);
}

/**
 * @brief USART2 Initialization (PA2: TX, PA3: RX connected to ST-LINK VCP @ 115200)
 */
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

/**
 * @brief TIM2 Initialization: 170 MHz / 1700 / 286 ≈ 350 Hz
 */
static void MX_TIM2_Init(void)
{
    TIM_ClockConfigTypeDef sClockSourceConfig = {0};
    TIM_MasterConfigTypeDef sMasterConfig = {0};

    htim2.Instance = TIM2;
    /* Prescaler = 170 - 1 -> Timer clock = 1 MHz (1 us per count) */
    htim2.Init.Prescaler = 170 - 1;
    htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
    /* Period = 2857 us -> 350.017 Hz (or use 1428 for 700.28 Hz) */
    htim2.Init.Period = 2857 - 1;
    htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    HAL_TIM_Base_Init(&htim2);

    sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
    HAL_TIM_ConfigClockSource(&htim2, &sClockSourceConfig);

    sMasterConfig.MasterOutputTrigger = TIM_TRGO_UPDATE;
    sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
    HAL_TIMEx_MasterConfigSynchronization(&htim2, &sMasterConfig);

    /* Enable NVIC for TIM2 Interrupt */
    HAL_NVIC_SetPriority(TIM2_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(TIM2_IRQn);
}

/**
 * @brief GPIO Initialization (PA5 for User Green LED)
 */
static void MX_GPIO_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};

    /* GPIO Ports Clock Enable */
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();

    /* Configure PA5 (LD2 Green LED on Nucleo) */
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_RESET);
    GPIO_InitStruct.Pin = GPIO_PIN_5;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
}
