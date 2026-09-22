/**
 * @file ecg_dsp_filter.h
 * @brief Real-time Biquad IIR Bandpass & Notch Filter for STM32G474.
 * 
 * Generated for IEEE-level research publication.
 * Bandpass: 0.5 - 40.0 Hz (4th-order Butterworth, 4 Biquad Stages)
 * Notch:    50.0 Hz (2nd-order IIR Notch, Q=30, 1 Biquad Stage)
 * Total:    5 Biquad Stages (25 CMSIS-DSP coefficients)
 */

#ifndef ECG_DSP_FILTER_H
#define ECG_DSP_FILTER_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

#define ECG_FILTER_NUM_STAGES  5
#define ECG_COEFFS_PER_STAGE   5
#define ECG_TOTAL_COEFFS       (ECG_FILTER_NUM_STAGES * ECG_COEFFS_PER_STAGE)

/* Filter instance state structure (pure C, compatible with arm_biquad_casd_df1_inst_f32) */
typedef struct {
    uint8_t numStages;
    float *pState;       /**< Points to state buffer of size 4 * numStages */
    const float *pCoeffs; /**< Points to coefficient array of size 5 * numStages */
} ecg_biquad_instance_f32;

/* Exported Coefficient Arrays */
extern const float ECG_COEFFS_700HZ[ECG_TOTAL_COEFFS];
extern const float ECG_COEFFS_350HZ[ECG_TOTAL_COEFFS];

/**
 * @brief Initialize the ECG filter instance
 * @param S Pointer to filter instance
 * @param state_buf Buffer of at least (4 * ECG_FILTER_NUM_STAGES) floats
 * @param fs_mode 700 for 700Hz, 350 for 350Hz
 */
void ecg_filter_init(ecg_biquad_instance_f32 *S, float *state_buf, uint32_t fs_mode);

/**
 * @brief Process a single ECG sample in real-time (O(1) time complexity)
 * @param S Pointer to filter instance
 * @param in_sample Raw analog or digital sample (in mV or raw ADC counts)
 * @return Filtered ECG sample
 */
float ecg_filter_process_sample(ecg_biquad_instance_f32 *S, float in_sample);

/**
 * @brief Process a block of ECG samples
 * @param S Pointer to filter instance
 * @param pSrc Pointer to input buffer
 * @param pDst Pointer to output buffer
 * @param blockSize Number of samples in block
 */
void ecg_filter_process_block(ecg_biquad_instance_f32 *S, const float *pSrc, float *pDst, uint32_t blockSize);

/**
 * @brief Reset internal filter states (e.g., between subjects or on lead disconnect)
 */
void ecg_filter_reset(ecg_biquad_instance_f32 *S);

#ifdef __cplusplus
}
#endif

#endif /* ECG_DSP_FILTER_H */
