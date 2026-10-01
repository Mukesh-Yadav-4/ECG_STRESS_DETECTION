#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <math.h>
#include "telemetry_protocol.h"

#pragma pack(push, 1)
typedef struct {
    uint16_t seq_id;
    uint32_t timestamp_ms;
    float raw_ecg;
    float filtered_ecg;
} sample_input_t;

typedef struct {
    float raw_ecg;
    float filtered_ecg;
    uint8_t crc_valid;
} decrypt_result_t;
#pragma pack(pop)

int main(int argc, char *argv[]) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <mode> <input.bin> <output.bin>\n", argv[0]);
        return 1;
    }
    FILE *fin = fopen(argv[2], "rb");
    if (!fin) {
        perror("Failed to open input file");
        return 2;
    }
    FILE *fout = fopen(argv[3], "wb");
    if (!fout) {
        perror("Failed to open output file");
        fclose(fin);
        return 3;
    }

    if (strcmp(argv[1], "--encrypt-samples") == 0) {
        sample_input_t sample;
        telemetry_packet_t pkt;
        uint8_t flags = TELEMETRY_FLAG_ENCRYPTED | TELEMETRY_FLAG_CHAOS_4D;
        while (fread(&sample, sizeof(sample_input_t), 1, fin) == 1) {
            telemetry_pack(&pkt, sample.seq_id, sample.timestamp_ms, sample.raw_ecg, sample.filtered_ecg, flags);
            if (fwrite(&pkt, sizeof(telemetry_packet_t), 1, fout) != 1) {
                fclose(fin);
                fclose(fout);
                return 4;
            }
        }
        fclose(fin);
        fclose(fout);
        return 0;
    } else if (strcmp(argv[1], "--decrypt-packets") == 0) {
        telemetry_packet_t pkt;
        decrypt_result_t res;
        while (fread(&pkt, sizeof(telemetry_packet_t), 1, fin) == 1) {
            bool valid = telemetry_verify_frame(&pkt);
            res.crc_valid = valid ? 1 : 0;
            if (pkt.flags & TELEMETRY_FLAG_ENCRYPTED) {
                if (pkt.flags & TELEMETRY_FLAG_CHAOS_4D) {
                    telemetry_m4d_decrypt_packet(&pkt);
                } else {
                    telemetry_decrypt_packet(&pkt);
                }
            }
            res.raw_ecg = pkt.raw_ecg;
            res.filtered_ecg = pkt.filtered_ecg;
            if (fwrite(&res, sizeof(decrypt_result_t), 1, fout) != 1) {
                fclose(fin);
                fclose(fout);
                return 5;
            }
        }
        fclose(fin);
        fclose(fout);
        return 0;
    }

    fprintf(stderr, "Unknown mode: %s\n", argv[1]);
    fclose(fin);
    fclose(fout);
    return 1;
}
