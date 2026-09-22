/**
 * @file ecg_dsp_filter.c
 * @brief CMSIS-DSP Biquad Cascade Direct Form I Implementation for STM32G474.
 */

#include "ecg_dsp_filter.h"
#include <string.h>

/* 700 Hz Coefficients (b0, b1, b2, -a1, -a2) */
const float ECG_COEFFS_700HZ[ECG_TOTAL_COEFFS] = {
    /* Stage 1 (Bandpass 1) : b0, b1, b2, -a1, -a2 */
    +6.4638943877e-04f, +1.2927788775e-03f, +6.4638943877e-04f, +1.4257540703e+00f, -5.1865816116e-01f,
    /* Stage 2 (Bandpass 2) : b0, b1, b2, -a1, -a2 */
    +1.0000000000e+00f, +2.0000000000e+00f, +1.0000000000e+00f, +1.6560553312e+00f, -7.6803654432e-01f,
    /* Stage 3 (Bandpass 3) : b0, b1, b2, -a1, -a2 */
    +1.0000000000e+00f, -2.0000000000e+00f, +1.0000000000e+00f, +1.9915751219e+00f, -9.9159604311e-01f,
    /* Stage 4 (Bandpass 4) : b0, b1, b2, -a1, -a2 */
    +1.0000000000e+00f, -2.0000000000e+00f, +1.0000000000e+00f, +1.9966112375e+00f, -9.9663150311e-01f,
    /* Stage 5 (50Hz Notch) : b0, b1, b2, -a1, -a2 */
    +9.9257540703e-01f, -1.7885590792e+00f, +9.9257540703e-01f, +1.7885590792e+00f, -9.8515081406e-01f,
};

/* 350 Hz Coefficients (b0, b1, b2, -a1, -a2) */
const float ECG_COEFFS_350HZ[ECG_TOTAL_COEFFS] = {
    /* Stage 1 (Bandpass 1) : b0, b1, b2, -a1, -a2 */
    +7.2608729824e-03f, +1.4521745965e-02f, +7.2608729824e-03f, +9.5464098454e-01f, -2.5299364328e-01f,
    /* Stage 2 (Bandpass 2) : b0, b1, b2, -a1, -a2 */
    +1.0000000000e+00f, +2.0000000000e+00f, +1.0000000000e+00f, +1.2111042738e+00f, -6.0511559248e-01f,
    /* Stage 3 (Bandpass 3) : b0, b1, b2, -a1, -a2 */
    +1.0000000000e+00f, -2.0000000000e+00f, +1.0000000000e+00f, +1.9831889868e+00f, -9.8327219486e-01f,
    /* Stage 4 (Bandpass 4) : b0, b1, b2, -a1, -a2 */
    +1.0000000000e+00f, -2.0000000000e+00f, +1.0000000000e+00f, +1.9931895733e+00f, -9.9327039719e-01f,
    /* Stage 5 (50Hz Notch) : b0, b1, b2, -a1, -a2 */
    +9.8525947332e-01f, -1.2285984755e+00f, +9.8525947332e-01f, +1.2285984755e+00f, -9.7051888704e-01f,
};

void ecg_filter_init(ecg_biquad_instance_f32 *S, float *state_buf, uint32_t fs_mode) {
    S->numStages = ECG_FILTER_NUM_STAGES;
    S->pState = state_buf;
    if (fs_mode == 350) {
        S->pCoeffs = ECG_COEFFS_350HZ;
    } else {
        S->pCoeffs = ECG_COEFFS_700HZ;
    }
    memset(state_buf, 0, sizeof(float) * 4 * ECG_FILTER_NUM_STAGES);
}

void ecg_filter_reset(ecg_biquad_instance_f32 *S) {
    if (S && S->pState) {
        memset(S->pState, 0, sizeof(float) * 4 * S->numStages);
    }
}

float ecg_filter_process_sample(ecg_biquad_instance_f32 *S, float in_sample) {
    float *pState = S->pState;
    const float *pCoeffs = S->pCoeffs;
    float in = in_sample;
    float out = 0.0f;
    uint8_t stage = S->numStages;

    /* Process through all 5 cascaded biquads */
    do {
        /* Reading coefficients: b0, b1, b2, -a1, -a2 */
        float b0 = *pCoeffs++;
        float b1 = *pCoeffs++;
        float b2 = *pCoeffs++;
        float a1 = *pCoeffs++; /* Already negated (-a1 in standard notation) */
        float a2 = *pCoeffs++; /* Already negated (-a2 in standard notation) */

        /* Reading state variables: Xn1, Xn2, Yn1, Yn2 */
        float Xn1 = pState[0];
        float Xn2 = pState[1];
        float Yn1 = pState[2];
        float Yn2 = pState[3];

        /* Direct Form I difference equation:
         * y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2] + a1*y[n-1] + a2*y[n-2] */
        out = (b0 * in) + (b1 * Xn1) + (b2 * Xn2) + (a1 * Yn1) + (a2 * Yn2);

        /* Update state */
        pState[0] = in;
        pState[1] = Xn1;
        pState[2] = out;
        pState[3] = Yn1;

        pState += 4;
        in = out;
    } while (--stage);

    return out;
}

void ecg_filter_process_block(ecg_biquad_instance_f32 *S, const float *pSrc, float *pDst, uint32_t blockSize) {
    for (uint32_t i = 0; i < blockSize; i++) {
        pDst[i] = ecg_filter_process_sample(S, pSrc[i]);
    }
}
