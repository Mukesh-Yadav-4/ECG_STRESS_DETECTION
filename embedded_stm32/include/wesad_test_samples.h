/**
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
