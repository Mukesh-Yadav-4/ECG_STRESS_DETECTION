/**
 * @file main.h
 * @brief Self-contained hardware abstraction and definitions for STM32G474RE NUCLEO.
 * Provides register-level implementation of HAL interfaces so firmware compiles
 * cleanly with standard arm-none-eabi-gcc without external vendor driver bloat.
 */

#ifndef MAIN_H
#define MAIN_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ARM Cortex-M4 Core Peripherals */
#define SCB_CPACR           (*(volatile uint32_t *)0xE000ED88)
#define NVIC_ISER0          (*(volatile uint32_t *)0xE000E100)
#define SYSTICK_CTRL        (*(volatile uint32_t *)0xE000E010)
#define SYSTICK_LOAD        (*(volatile uint32_t *)0xE000E014)
#define SYSTICK_VAL         (*(volatile uint32_t *)0xE000E018)

/* STM32G4 Peripheral Base Addresses */
#define TIM2_BASE           0x40000000UL
#define USART2_BASE         0x40004400UL
#define PWR_BASE            0x40007000UL
#define RCC_BASE            0x40021000UL
#define FLASH_BASE          0x40022000UL
#define GPIOA_BASE          0x48000000UL
#define GPIOC_BASE          0x48000800UL

/* RCC Registers */
#define RCC_CR              (*(volatile uint32_t *)(RCC_BASE + 0x00))
#define RCC_CFGR            (*(volatile uint32_t *)(RCC_BASE + 0x08))
#define RCC_PLLCFGR         (*(volatile uint32_t *)(RCC_BASE + 0x0C))
#define RCC_AHB2ENR         (*(volatile uint32_t *)(RCC_BASE + 0x4C))
#define RCC_APB1ENR1        (*(volatile uint32_t *)(RCC_BASE + 0x58))
#define RCC_APB2ENR         (*(volatile uint32_t *)(RCC_BASE + 0x60))

/* Flash Registers */
#define FLASH_ACR           (*(volatile uint32_t *)(FLASH_BASE + 0x00))

/* Power Registers */
#define PWR_CR1             (*(volatile uint32_t *)(PWR_BASE + 0x00))
#define PWR_CR5             (*(volatile uint32_t *)(PWR_BASE + 0x80))

/* GPIOA Registers */
#define GPIOA_MODER         (*(volatile uint32_t *)(GPIOA_BASE + 0x00))
#define GPIOA_OTYPER        (*(volatile uint32_t *)(GPIOA_BASE + 0x04))
#define GPIOA_OSPEEDR       (*(volatile uint32_t *)(GPIOA_BASE + 0x08))
#define GPIOA_PUPDR         (*(volatile uint32_t *)(GPIOA_BASE + 0x0C))
#define GPIOA_IDR           (*(volatile uint32_t *)(GPIOA_BASE + 0x10))
#define GPIOA_ODR           (*(volatile uint32_t *)(GPIOA_BASE + 0x14))
#define GPIOA_BSRR          (*(volatile uint32_t *)(GPIOA_BASE + 0x18))
#define GPIOA_AFRL          (*(volatile uint32_t *)(GPIOA_BASE + 0x20))
#define GPIOA_AFRH          (*(volatile uint32_t *)(GPIOA_BASE + 0x24))

/* USART2 Registers */
#define USART2_CR1          (*(volatile uint32_t *)(USART2_BASE + 0x00))
#define USART2_CR2          (*(volatile uint32_t *)(USART2_BASE + 0x04))
#define USART2_CR3          (*(volatile uint32_t *)(USART2_BASE + 0x08))
#define USART2_BRR          (*(volatile uint32_t *)(USART2_BASE + 0x0C))
#define USART2_ISR          (*(volatile uint32_t *)(USART2_BASE + 0x1C))
#define USART2_ICR          (*(volatile uint32_t *)(USART2_BASE + 0x20))
#define USART2_RDR          (*(volatile uint32_t *)(USART2_BASE + 0x24))
#define USART2_TDR          (*(volatile uint32_t *)(USART2_BASE + 0x28))

/* TIM2 Registers */
#define TIM2_CR1            (*(volatile uint32_t *)(TIM2_BASE + 0x00))
#define TIM2_DIER           (*(volatile uint32_t *)(TIM2_BASE + 0x0C))
#define TIM2_SR             (*(volatile uint32_t *)(TIM2_BASE + 0x10))
#define TIM2_EGR            (*(volatile uint32_t *)(TIM2_BASE + 0x14))
#define TIM2_PSC            (*(volatile uint32_t *)(TIM2_BASE + 0x28))
#define TIM2_ARR            (*(volatile uint32_t *)(TIM2_BASE + 0x2C))

/* Compatibility Constants */
#define GPIOA               ((void *)GPIOA_BASE)
#define GPIOC               ((void *)GPIOC_BASE)
#define USART2              ((void *)USART2_BASE)
#define TIM2                ((void *)TIM2_BASE)

#define GPIO_PIN_0          (1U << 0)
#define GPIO_PIN_2          (1U << 2)
#define GPIO_PIN_3          (1U << 3)
#define GPIO_PIN_5          (1U << 5)

#define GPIO_PIN_RESET      0
#define GPIO_PIN_SET        1

#define GPIO_MODE_OUTPUT_PP 0x01
#define GPIO_NOPULL         0x00
#define GPIO_SPEED_FREQ_LOW 0x00

#define TIM2_IRQn           28

#define FLASH_LATENCY_4     4
#define PWR_REGULATOR_VOLTAGE_SCALE1_BOOST 0

#define RCC_OSCILLATORTYPE_HSI      0x02
#define RCC_HSI_ON                  0x01
#define RCC_HSICALIBRATION_DEFAULT  0x40
#define RCC_PLL_ON                  0x02
#define RCC_PLLSOURCE_HSI           0x02
#define RCC_PLLM_DIV4               4
#define RCC_PLLP_DIV2               2
#define RCC_PLLQ_DIV2               2
#define RCC_PLLR_DIV2               2

#define RCC_CLOCKTYPE_HCLK          0x01
#define RCC_CLOCKTYPE_SYSCLK        0x02
#define RCC_CLOCKTYPE_PCLK1         0x04
#define RCC_CLOCKTYPE_PCLK2         0x08
#define RCC_SYSCLKSOURCE_PLLCLK     0x03
#define RCC_SYSCLK_DIV1             0x00
#define RCC_HCLK_DIV1               0x00

#define UART_WORDLENGTH_8B          0
#define UART_STOPBITS_1             0
#define UART_PARITY_NONE            0
#define UART_MODE_TX_RX             0
#define UART_HWCONTROL_NONE         0
#define UART_OVERSAMPLING_16        0
#define UART_ONE_BIT_SAMPLE_DISABLE 0
#define UART_PRESCALER_DIV1         0
#define UART_ADVFEATURE_NO_INIT     0

#define TIM_COUNTERMODE_UP          0
#define TIM_CLOCKDIVISION_DIV1      0
#define TIM_AUTORELOAD_PRELOAD_ENABLE 0
#define TIM_CLOCKSOURCE_INTERNAL    0
#define TIM_TRGO_UPDATE             0
#define TIM_MASTERSLAVEMODE_DISABLE 0

#define HAL_OK       0
#define HAL_ERROR    1
#define HAL_BUSY     2
#define HAL_TIMEOUT  3

/* HAL Type Definitions */
typedef struct {
    uint32_t BaudRate;
    uint32_t WordLength;
    uint32_t StopBits;
    uint32_t Parity;
    uint32_t Mode;
    uint32_t HwFlowCtl;
    uint32_t OverSampling;
    uint32_t OneBitSampling;
    uint32_t ClockPrescaler;
    uint32_t AdvFeatureInit;
} UART_InitTypeDef;

typedef struct {
    void *Instance;
    UART_InitTypeDef Init;
    struct { uint32_t AdvFeatureInit; } AdvancedInit;
} UART_HandleTypeDef;

typedef struct {
    uint32_t Prescaler;
    uint32_t CounterMode;
    uint32_t Period;
    uint32_t ClockDivision;
    uint32_t AutoReloadPreload;
} TIM_Base_InitTypeDef;

typedef struct {
    void *Instance;
    TIM_Base_InitTypeDef Init;
} TIM_HandleTypeDef;

typedef struct {
    void *Instance;
} ADC_HandleTypeDef;

typedef struct {
    uint32_t Pin;
    uint32_t Mode;
    uint32_t Pull;
    uint32_t Speed;
} GPIO_InitTypeDef;

typedef struct {
    uint32_t PLLState;
    uint32_t PLLSource;
    uint32_t PLLM;
    uint32_t PLLN;
    uint32_t PLLP;
    uint32_t PLLQ;
    uint32_t PLLR;
} RCC_PLLInitTypeDef;

typedef struct {
    uint32_t OscillatorType;
    uint32_t HSIState;
    uint32_t HSICalibrationValue;
    RCC_PLLInitTypeDef PLL;
} RCC_OscInitTypeDef;

typedef struct {
    uint32_t ClockType;
    uint32_t SYSCLKSource;
    uint32_t AHBCLKDivider;
    uint32_t APB1CLKDivider;
    uint32_t APB2CLKDivider;
} RCC_ClkInitTypeDef;

typedef struct {
    uint32_t ClockSource;
} TIM_ClockConfigTypeDef;

typedef struct {
    uint32_t MasterOutputTrigger;
    uint32_t MasterSlaveMode;
} TIM_MasterConfigTypeDef;

/* Global Tick and Timing State */
extern volatile uint32_t g_millis;
extern volatile uint32_t g_tick_count;
extern TIM_HandleTypeDef htim2;

static inline int HAL_Init(void) {
    /* Enable CP10 and CP11 Full Access for ARM Cortex-M4 Hardware FPU */
    SCB_CPACR |= ((3UL << 20) | (3UL << 22));

    /* Standard 1ms SysTick (16 MHz HSI default) */
    SYSTICK_LOAD = 16000UL - 1UL;
    SYSTICK_VAL  = 0UL;
    SYSTICK_CTRL = (1UL << 2) | (1UL << 1) | (1UL << 0);
    return HAL_OK;
}

static inline void __HAL_RCC_GPIOA_CLK_ENABLE(void) {
    RCC_AHB2ENR |= (1UL << 0);
    volatile uint32_t dummy = RCC_AHB2ENR;
    (void)dummy;
}

static inline void __HAL_RCC_GPIOC_CLK_ENABLE(void) {
    RCC_AHB2ENR |= (1UL << 2);
    volatile uint32_t dummy = RCC_AHB2ENR;
    (void)dummy;
}

static inline int HAL_PWREx_ControlVoltageScaling(uint32_t scale) {
    (void)scale;
    RCC_APB1ENR1 |= (1UL << 28);
    (void)RCC_APB1ENR1;
    PWR_CR5 &= ~(1UL << 8); /* Clear R1MODE -> Boost mode active up to 170 MHz */
    return HAL_OK;
}

static inline int HAL_RCC_OscConfig(RCC_OscInitTypeDef *cfg) {
    (void)cfg;
    /* 4 WS + prefetch for 170 MHz SYSCLK */
    FLASH_ACR = (FLASH_ACR & ~0x0FUL) | 0x04UL | (1UL << 8);

    /* Configure PLL: HSI16 (16MHz) / 4 * 85 / 2 = 170 MHz SYSCLK */
    RCC_PLLCFGR = (2UL << 0) | ((4UL - 1UL) << 4) | (85UL << 8) | (1UL << 24);

    /* Enable PLL */
    RCC_CR |= (1UL << 24);
    while (!(RCC_CR & (1UL << 25))); /* Wait for PLLRDY */
    return HAL_OK;
}

static inline int HAL_RCC_ClockConfig(RCC_ClkInitTypeDef *cfg, uint32_t latency) {
    (void)cfg;
    (void)latency;
    /* Select PLL as system clock */
    RCC_CFGR = (RCC_CFGR & ~0x03UL) | 0x03UL;
    while (((RCC_CFGR >> 2) & 0x03UL) != 0x03UL); /* Wait for switch */

    /* Update SysTick for 170 MHz SYSCLK (170,000 counts = 1 ms) */
    SYSTICK_LOAD = 170000UL - 1UL;
    SYSTICK_VAL  = 0UL;
    return HAL_OK;
}

static inline void HAL_GPIO_Init(void *port, GPIO_InitTypeDef *cfg) {
    if (port == GPIOA) {
        if (cfg->Pin & GPIO_PIN_5) {
            /* PA5 (User Green LED LD2): Output push-pull, low speed */
            GPIOA_MODER &= ~(3UL << (5 * 2));
            GPIOA_MODER |= (1UL << (5 * 2));
            GPIOA_OTYPER &= ~(1UL << 5);
            GPIOA_OSPEEDR &= ~(3UL << (5 * 2));
            GPIOA_PUPDR &= ~(3UL << (5 * 2));
        }
    }
}

static inline void HAL_GPIO_WritePin(void *port, uint16_t pin, uint8_t state) {
    if (port == GPIOA) {
        if (state) {
            GPIOA_BSRR = (uint32_t)pin;
        } else {
            GPIOA_BSRR = ((uint32_t)pin << 16);
        }
    }
}

static inline int HAL_UART_Init(UART_HandleTypeDef *huart) {
    (void)huart;
    /* Configure PA2 as USART2_TX (AF7) */
    GPIOA_MODER &= ~(3UL << (2 * 2));
    GPIOA_MODER |= (2UL << (2 * 2));
    GPIOA_AFRL &= ~(0xFUL << (2 * 4));
    GPIOA_AFRL |= (7UL << (2 * 4));
    GPIOA_OSPEEDR |= (3UL << (2 * 2));
    GPIOA_PUPDR &= ~(3UL << (2 * 2));
    GPIOA_PUPDR |= (1UL << (2 * 2));

    /* Enable USART2 Clock */
    RCC_APB1ENR1 |= (1UL << 17);
    (void)RCC_APB1ENR1;

    /* 115200 Baud @ 170 MHz SYSCLK: 170,000,000 / 115,200 = 1475.69 => 1476 */
    USART2_CR1 = 0;
    USART2_BRR = 1476;
    USART2_CR1 = (1UL << 3) | (1UL << 0); /* TE | UE */
    return HAL_OK;
}

static inline int HAL_UART_Transmit(UART_HandleTypeDef *huart, const uint8_t *pData, uint16_t Size, uint32_t Timeout) {
    (void)huart;
    (void)Timeout;
    for (uint16_t i = 0; i < Size; i++) {
        while (!(USART2_ISR & (1UL << 7))); /* TXE / TXFNF */
        USART2_TDR = pData[i];
    }
    return HAL_OK;
}

static inline int HAL_TIM_Base_Init(TIM_HandleTypeDef *htim) {
    (void)htim;
    /* Enable TIM2 clock */
    RCC_APB1ENR1 |= (1UL << 0);
    (void)RCC_APB1ENR1;

    /* Prescaler = 170 - 1 -> Timer clock = 1 MHz (1 us per count) */
    TIM2_PSC = 170 - 1;
    /* Period = 2857 us -> exactly 350.017 Hz periodic interrupt */
    TIM2_ARR = 2857 - 1;
    TIM2_EGR = (1UL << 0); /* Generate update event to reload prescaler */
    TIM2_SR  = 0;          /* Clear flags */
    return HAL_OK;
}

static inline int HAL_TIM_ConfigClockSource(TIM_HandleTypeDef *htim, TIM_ClockConfigTypeDef *sClockSourceConfig) {
    (void)htim;
    (void)sClockSourceConfig;
    return HAL_OK;
}

static inline int HAL_TIMEx_MasterConfigSynchronization(TIM_HandleTypeDef *htim, TIM_MasterConfigTypeDef *sMasterConfig) {
    (void)htim;
    (void)sMasterConfig;
    return HAL_OK;
}

static inline void HAL_NVIC_SetPriority(uint32_t irq, uint32_t preempt, uint32_t sub) {
    (void)irq;
    (void)preempt;
    (void)sub;
}

static inline void HAL_NVIC_EnableIRQ(uint32_t irq) {
    if (irq == TIM2_IRQn) {
        NVIC_ISER0 |= (1UL << 28);
    }
}

static inline int HAL_TIM_Base_Start_IT(TIM_HandleTypeDef *htim) {
    (void)htim;
    /* TIM2 Periodic Interrupt (350 Hz) */
    TIM2_DIER |= (1UL << 0); /* Enable Update Interrupt (UIE) */
    TIM2_CR1  |= (1UL << 0); /* Enable Counter (CEN) */
    NVIC_ISER0 |= (1UL << 28);
    return HAL_OK;
}

static inline uint32_t HAL_GetTick(void) {
    return g_millis;
}

/* TIM2 Interrupt Service Routine & Callback */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim);

#ifdef __cplusplus
}
#endif

#endif /* MAIN_H */
