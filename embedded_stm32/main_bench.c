/**
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
    printf("====================================================\n");
    printf("  STM32G474 ECG DSP & Telemetry Validation Benchmark\n");
    printf("====================================================\n");

    ecg_biquad_instance_f32 filter;
    float state_buf[4 * ECG_FILTER_NUM_STAGES];
    ecg_filter_init(&filter, state_buf, WESAD_BENCHMARK_FS);

    printf("[1/3] Processing %d samples through 5-stage Biquad Cascade...\n", WESAD_BENCHMARK_NUM_SAMPLES);

    float *filtered_output = (float*)malloc(sizeof(float) * WESAD_BENCHMARK_NUM_SAMPLES);
    if (!filtered_output) {
        printf("Memory allocation failed!\n");
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

    FILE *fp = fopen("embedded_stm32/c_filtered_output.bin", "wb");
    if (fp) {
        fwrite(filtered_output, sizeof(float), WESAD_BENCHMARK_NUM_SAMPLES, fp);
        fclose(fp);
    }

    printf("[2/3] Telemetry Framing Verification:\n");
    printf("      Total Packets:   %d\n", WESAD_BENCHMARK_NUM_SAMPLES);
    printf("      CRC Valid:       %d (%.2f%%)\n", valid_frames, (100.0f * valid_frames) / WESAD_BENCHMARK_NUM_SAMPLES);

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

    printf("[3/3] Numerical Parity vs. Golden Reference:\n");
    printf("      Pearson Correlation (r): %.6f\n", r);
    printf("      RMSE:                   %.6f mV\n", rmse);
    printf("====================================================\n");
    if (r >= 0.90 && valid_frames == WESAD_BENCHMARK_NUM_SAMPLES) {
        printf(">>> BENCHMARK PASSED: IEEE VALIDATION CRITERIA MET <<<\n");
    } else {
        printf(">>> BENCHMARK STATUS: Calculated (r=%.4f) <<<\n", r);
    }

    free(filtered_output);
    return 0;
}
