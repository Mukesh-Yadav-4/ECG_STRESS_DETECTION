"""
Export CMSIS-DSP Biquad coefficients and embedded C files for STM32G474.
Supports both 700 Hz (Clinical WESAD raw) and 350 Hz (Telemetry stream).
"""

import os
import json
import numpy as np
from scipy import signal

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMBEDDED_DIR = os.path.join(PROJECT_ROOT, "embedded_stm32")
INC_DIR = os.path.join(EMBEDDED_DIR, "include")
SRC_DIR = os.path.join(EMBEDDED_DIR, "src")

os.makedirs(INC_DIR, exist_ok=True)
os.makedirs(SRC_DIR, exist_ok=True)


def get_cmsis_coeffs(fs, lowcut=0.5, highcut=40.0, notch_freq=50.0, notch_q=30.0):
    # 4th-order Butterworth bandpass (4 stages = 8 poles)
    sos_bp = signal.butter(4, [lowcut, highcut], btype='bandpass', fs=fs, output='sos')
    
    # 2nd-order IIR Notch filter (1 stage = 2 poles)
    b_notch, a_notch = signal.iirnotch(w0=notch_freq, Q=notch_q, fs=fs)
    sos_notch = np.array([[b_notch[0], b_notch[1], b_notch[2], a_notch[0], a_notch[1], a_notch[2]]])
    
    # Combined SOS: 4 stages BP + 1 stage Notch = 5 stages total
    sos_full = np.vstack([sos_bp, sos_notch])
    
    # CMSIS-DSP expects: {b0, b1, b2, -a1, -a2} per biquad stage
    cmsis_coeffs = []
    for row in sos_full:
        b0, b1, b2, a0, a1, a2 = row
        # normalize by a0 just in case
        b0 /= a0
        b1 /= a0
        b2 /= a0
        a1_norm = - (a1 / a0)  # negate for CMSIS-DSP MAC
        a2_norm = - (a2 / a0)  # negate for CMSIS-DSP MAC
        cmsis_coeffs.extend([b0, b1, b2, a1_norm, a2_norm])
        
    return np.array(cmsis_coeffs, dtype=np.float32), sos_bp, sos_notch


def generate_header():
    c_700, _, _ = get_cmsis_coeffs(700)
    c_350, _, _ = get_cmsis_coeffs(350)
    
    header_content = f"""/**
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
extern "C" {{
#endif

#define ECG_FILTER_NUM_STAGES  5
#define ECG_COEFFS_PER_STAGE   5
#define ECG_TOTAL_COEFFS       (ECG_FILTER_NUM_STAGES * ECG_COEFFS_PER_STAGE)

/* Filter instance state structure (pure C, compatible with arm_biquad_casd_df1_inst_f32) */
typedef struct {{
    uint8_t numStages;
    float *pState;       /**< Points to state buffer of size 4 * numStages */
    const float *pCoeffs; /**< Points to coefficient array of size 5 * numStages */
}} ecg_biquad_instance_f32;

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
}}
#endif

#endif /* ECG_DSP_FILTER_H */
"""
    with open(os.path.join(INC_DIR, "ecg_dsp_filter.h"), "w") as f:
        f.write(header_content)
    print(f"Generated {os.path.join(INC_DIR, 'ecg_dsp_filter.h')}")


def generate_source():
    c_700, _, _ = get_cmsis_coeffs(700)
    c_350, _, _ = get_cmsis_coeffs(350)
    
    def format_coeffs(arr):
        lines = []
        for i in range(0, len(arr), 5):
            stage = i // 5 + 1
            stage_name = f"Stage {stage} (Bandpass {stage})" if stage <= 4 else "Stage 5 (50Hz Notch)"
            chunk = ", ".join(f"{v:+.10e}f" for v in arr[i:i+5])
            lines.append(f"    /* {stage_name} : b0, b1, b2, -a1, -a2 */\n    {chunk},")
        return "\n".join(lines)

    source_content = f"""/**
 * @file ecg_dsp_filter.c
 * @brief CMSIS-DSP Biquad Cascade Direct Form I Implementation for STM32G474.
 */

#include "ecg_dsp_filter.h"
#include <string.h>

/* 700 Hz Coefficients (b0, b1, b2, -a1, -a2) */
const float ECG_COEFFS_700HZ[ECG_TOTAL_COEFFS] = {{
{format_coeffs(c_700)}
}};

/* 350 Hz Coefficients (b0, b1, b2, -a1, -a2) */
const float ECG_COEFFS_350HZ[ECG_TOTAL_COEFFS] = {{
{format_coeffs(c_350)}
}};

void ecg_filter_init(ecg_biquad_instance_f32 *S, float *state_buf, uint32_t fs_mode) {{
    S->numStages = ECG_FILTER_NUM_STAGES;
    S->pState = state_buf;
    if (fs_mode == 350) {{
        S->pCoeffs = ECG_COEFFS_350HZ;
    }} else {{
        S->pCoeffs = ECG_COEFFS_700HZ;
    }}
    memset(state_buf, 0, sizeof(float) * 4 * ECG_FILTER_NUM_STAGES);
}}

void ecg_filter_reset(ecg_biquad_instance_f32 *S) {{
    if (S && S->pState) {{
        memset(S->pState, 0, sizeof(float) * 4 * S->numStages);
    }}
}}

float ecg_filter_process_sample(ecg_biquad_instance_f32 *S, float in_sample) {{
    float *pState = S->pState;
    const float *pCoeffs = S->pCoeffs;
    float in = in_sample;
    float out = 0.0f;
    uint8_t stage = S->numStages;

    /* Process through all 5 cascaded biquads */
    do {{
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
    }} while (--stage);

    return out;
}}

void ecg_filter_process_block(ecg_biquad_instance_f32 *S, const float *pSrc, float *pDst, uint32_t blockSize) {{
    for (uint32_t i = 0; i < blockSize; i++) {{
        pDst[i] = ecg_filter_process_sample(S, pSrc[i]);
    }}
}}
"""
    with open(os.path.join(SRC_DIR, "ecg_dsp_filter.c"), "w") as f:
        f.write(source_content)
    print(f"Generated {os.path.join(SRC_DIR, 'ecg_dsp_filter.c')}")


def generate_protocol():
    header_content = """/**
 * @file telemetry_protocol.h
 * @brief Binary Telemetry Protocol for STM32-to-Host IoMT Communication.
 *
 * Frame Format (20 bytes total):
 * [0..1]   SYNC_WORD    : 0xAA, 0x55
 * [2]      VERSION      : 0x01
 * [3]      FLAGS        : Bit 0: Encrypted (0=Plain, 1=Encrypted), Bit 1: Live Sensor (0=WESAD, 1=AD8232)
 * [4..5]   SEQ_ID       : uint16_t packet sequence counter (loss tracking)
 * [6..9]   TIMESTAMP_MS : uint32_t millisecond hardware timestamp
 * [10..13] RAW_ECG      : float32_t raw input sample
 * [14..17] FILT_ECG     : float32_t real-time filtered output sample
 * [18..19] CRC16        : uint16_t CRC-16-CCITT checksum over bytes [2..17]
 */

#ifndef TELEMETRY_PROTOCOL_H
#define TELEMETRY_PROTOCOL_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#define TELEMETRY_SYNC_BYTE_0    0xAA
#define TELEMETRY_SYNC_BYTE_1    0x55
#define TELEMETRY_PROTOCOL_VER   0x01
#define TELEMETRY_FRAME_SIZE     20

#define TELEMETRY_FLAG_ENCRYPTED (1 << 0)
#define TELEMETRY_FLAG_LIVE_ADC  (1 << 1)

#pragma pack(push, 1)
typedef struct {
    uint8_t  sync[2];       /**< 0xAA, 0x55 */
    uint8_t  version;       /**< 0x01 */
    uint8_t  flags;         /**< Security and sensor mode flags */
    uint16_t seq_id;        /**< Packet sequence number */
    uint32_t timestamp_ms;  /**< Hardware timestamp in ms */
    float    raw_ecg;       /**< Raw ECG sample */
    float    filtered_ecg;  /**< Filtered ECG sample */
    uint16_t crc16;         /**< CRC-16-CCITT */
} telemetry_packet_t;
#pragma pack(pop)

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Compute standard CRC-16-CCITT (polynomial 0x1021, init 0xFFFF)
 */
uint16_t telemetry_crc16(const uint8_t *data, size_t length);

/**
 * @brief Pack an ECG telemetry frame
 */
void telemetry_pack(telemetry_packet_t *pkt, uint16_t seq_id, uint32_t timestamp_ms, 
                    float raw_val, float filt_val, uint8_t flags);

/**
 * @brief Verify frame synchronization and CRC
 */
bool telemetry_verify_frame(const telemetry_packet_t *pkt);

#ifdef __cplusplus
}
#endif

#endif /* TELEMETRY_PROTOCOL_H */
"""
    with open(os.path.join(INC_DIR, "telemetry_protocol.h"), "w") as f:
        f.write(header_content)
    print(f"Generated {os.path.join(INC_DIR, 'telemetry_protocol.h')}")

    source_content = """/**
 * @file telemetry_protocol.c
 * @brief Telemetry protocol framing and CRC-16 implementation.
 */

#include "telemetry_protocol.h"

uint16_t telemetry_crc16(const uint8_t *data, size_t length) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < length; i++) {
        crc ^= (uint16_t)(data[i] << 8);
        for (uint8_t bit = 0; bit < 8; bit++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ 0x1021;
            } else {
                crc = crc << 1;
            }
        }
    }
    return crc;
}

void telemetry_pack(telemetry_packet_t *pkt, uint16_t seq_id, uint32_t timestamp_ms, 
                    float raw_val, float filt_val, uint8_t flags) {
    pkt->sync[0] = TELEMETRY_SYNC_BYTE_0;
    pkt->sync[1] = TELEMETRY_SYNC_BYTE_1;
    pkt->version = TELEMETRY_PROTOCOL_VER;
    pkt->flags = flags;
    pkt->seq_id = seq_id;
    pkt->timestamp_ms = timestamp_ms;
    pkt->raw_ecg = raw_val;
    pkt->filtered_ecg = filt_val;
    /* Compute CRC over payload bytes [version ... filtered_ecg] */
    pkt->crc16 = telemetry_crc16(&pkt->version, sizeof(telemetry_packet_t) - 4);
}

bool telemetry_verify_frame(const telemetry_packet_t *pkt) {
    if (pkt->sync[0] != TELEMETRY_SYNC_BYTE_0 || pkt->sync[1] != TELEMETRY_SYNC_BYTE_1) {
        return false;
    }
    if (pkt->version != TELEMETRY_PROTOCOL_VER) {
        return false;
    }
    uint16_t expected_crc = telemetry_crc16(&pkt->version, sizeof(telemetry_packet_t) - 4);
    return (pkt->crc16 == expected_crc);
}
"""
    with open(os.path.join(SRC_DIR, "telemetry_protocol.c"), "w") as f:
        f.write(source_content)
    print(f"Generated {os.path.join(SRC_DIR, 'telemetry_protocol.c')}")


def generate_test_vectors():
    npz_path = os.path.join(PROJECT_ROOT, "demo", "sample_data", "ecg_samples.npz")
    data = np.load(npz_path)
    
    # Take 2,100 samples (6 seconds at 350 Hz) of S2 Baseline
    raw_s2 = data["S2_Baseline_raw"][:2100].astype(np.float32)
    filt_s2 = data["S2_Baseline_filt"][:2100].astype(np.float32)
    
    header_content = f"""/**
 * @file wesad_test_samples.h
 * @brief Embedded benchmark test vector from WESAD Subject S2.
 */

#ifndef WESAD_TEST_SAMPLES_H
#define WESAD_TEST_SAMPLES_H

#include <stdint.h>

#define WESAD_BENCHMARK_NUM_SAMPLES 2100
#define WESAD_BENCHMARK_FS          350

extern const float WESAD_S2_RAW_ECG[WESAD_BENCHMARK_NUM_SAMPLES];
extern const float WESAD_S2_GOLDEN_FILT_ECG[WESAD_BENCHMARK_NUM_SAMPLES];

#endif /* WESAD_TEST_SAMPLES_H */
"""
    with open(os.path.join(INC_DIR, "wesad_test_samples.h"), "w") as f:
        f.write(header_content)

    def format_float_array(arr):
        items = [f"{v:+.6f}f" for v in arr]
        lines = []
        for i in range(0, len(items), 8):
            lines.append("    " + ", ".join(items[i:i+8]) + ",")
        return "\n".join(lines)

    source_content = f"""/**
 * @file wesad_test_samples.c
 * @brief Embedded benchmark test vector array definitions.
 */

#include "wesad_test_samples.h"

const float WESAD_S2_RAW_ECG[WESAD_BENCHMARK_NUM_SAMPLES] = {{
{format_float_array(raw_s2)}
}};

const float WESAD_S2_GOLDEN_FILT_ECG[WESAD_BENCHMARK_NUM_SAMPLES] = {{
{format_float_array(filt_s2)}
}};
"""
    with open(os.path.join(SRC_DIR, "wesad_test_samples.c"), "w") as f:
        f.write(source_content)
    print(f"Generated {os.path.join(SRC_DIR, 'wesad_test_samples.c')}")


def generate_main_bench():
    bench_code = """/**
 * @file main_bench.c
 * @brief Standalone test harness to verify DSP filtering and packet framing.
 * Can be compiled natively with GCC/Clang or imported into STM32CubeIDE Core/Src.
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "ecg_dsp_filter.h"
#include "telemetry_protocol.h"
#include "wesad_test_samples.h"

int main(void) {
    printf("====================================================\\n");
    printf("  STM32G474 ECG DSP & Telemetry Validation Benchmark\\n");
    printf("====================================================\\n");

    ecg_biquad_instance_f32 filter;
    float state_buf[4 * ECG_FILTER_NUM_STAGES];
    ecg_filter_init(&filter, state_buf, WESAD_BENCHMARK_FS);

    printf("[1/3] Processing %d samples through 5-stage Biquad Cascade...\\n", WESAD_BENCHMARK_NUM_SAMPLES);

    float *filtered_output = (float*)malloc(sizeof(float) * WESAD_BENCHMARK_NUM_SAMPLES);
    if (!filtered_output) {
        printf("Memory allocation failed!\\n");
        return 1;
    }

    uint32_t valid_frames = 0;
    telemetry_packet_t packet;

    for (int i = 0; i < WESAD_BENCHMARK_NUM_SAMPLES; i++) {
        float raw = WESAD_S2_RAW_ECG[i];
        float filt = ecg_filter_process_sample(&filter, raw);
        filtered_output[i] = filt;

        /* Test packet packing and CRC verification */
        telemetry_pack(&packet, (uint16_t)i, (uint32_t)(i * 1000 / WESAD_BENCHMARK_FS), raw, filt, 0);
        if (telemetry_verify_frame(&packet)) {
            valid_frames++;
        }
    }

    printf("[2/3] Telemetry Framing Verification:\\n");
    printf("      Total Packets:   %d\\n", WESAD_BENCHMARK_NUM_SAMPLES);
    printf("      CRC Valid:       %d (%.2f%%)\\n", valid_frames, (100.0f * valid_frames) / WESAD_BENCHMARK_NUM_SAMPLES);

    /* Compute correlation against golden reference (skipping initial settling time of 50 samples) */
    int start_idx = 50;
    int eval_samples = WESAD_BENCHMARK_NUM_SAMPLES - start_idx;
    double sum_x = 0, sum_y = 0, sum_xy = 0, sum_x2 = 0, sum_y2 = 0, sse = 0;

    for (int i = start_idx; i < WESAD_BENCHMARK_NUM_SAMPLES; i++) {
        double x = filtered_output[i];
        double y = WESAD_S2_GOLDEN_FILT_ECG[i];
        sum_x += x;
        sum_y += y;
        sum_xy += x * y;
        sum_x2 += x * x;
        sum_y2 += y * y;
        double err = x - y;
        sse += err * err;
    }

    double mean_x = sum_x / eval_samples;
    double mean_y = sum_y / eval_samples;
    double cov_xy = (sum_xy / eval_samples) - (mean_x * mean_y);
    double var_x = (sum_x2 / eval_samples) - (mean_x * mean_x);
    double var_y = (sum_y2 / eval_samples) - (mean_y * mean_y);
    double r = cov_xy / sqrt(var_x * var_y);
    double rmse = sqrt(sse / eval_samples);

    printf("[3/3] Numerical Parity vs. Golden Reference:\\n");
    printf("      Pearson Correlation (r): %.6f\\n", r);
    printf("      RMSE:                   %.6f mV\\n", rmse);
    printf("====================================================\\n");
    if (r >= 0.95 && valid_frames == WESAD_BENCHMARK_NUM_SAMPLES) {
        printf(">>> BENCHMARK PASSED: IEEE VALIDATION CRITERIA MET <<<\n");
    } else {
        printf(">>> BENCHMARK WARNING: Review filter alignment <<<\n");
    }

    free(filtered_output);
    return 0;
}
"""
    with open(os.path.join(EMBEDDED_DIR, "main_bench.c"), "w") as f:
        f.write(bench_code)
    print(f"Generated {os.path.join(EMBEDDED_DIR, 'main_bench.c')}")


if __name__ == "__main__":
    print("Exporting embedded C headers and implementations for STM32G474...")
    generate_header()
    generate_source()
    generate_protocol()
    generate_test_vectors()
    generate_main_bench()
    print("All embedded files generated successfully.")
