/**
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

/* ================= 32-BIT CHAOTIC STREAM CIPHER IMPLEMENTATION ================= */
static uint32_t s_chaos_state = CHAOS_SECRET_KEY;
static uint8_t  s_prev_cipher = CHAOS_INIT_IV;

void telemetry_cipher_reset(uint32_t key, uint8_t iv) {
    s_chaos_state = key;
    s_prev_cipher = iv;
}

static inline uint8_t get_next_keystream(void) {
    s_chaos_state ^= s_chaos_state << 13;
    s_chaos_state ^= s_chaos_state >> 17;
    s_chaos_state ^= s_chaos_state << 5;
    s_chaos_state += CHAOS_WEYL_CONST;
    return (uint8_t)(s_chaos_state & 0xFF);
}

void telemetry_encrypt_packet(telemetry_packet_t *pkt) {
    /* Per-packet Nonce seeding: mixes SECRET_KEY with seq_id and timestamp_ms */
    uint32_t state = (CHAOS_SECRET_KEY ^ ((uint32_t)pkt->seq_id * 0x45D9F3BU) ^ pkt->timestamp_ms);
    uint8_t prev_cipher = (CHAOS_INIT_IV ^ (uint8_t)(pkt->seq_id & 0xFF));

    /* Encrypt raw_ecg (4B) and filtered_ecg (4B) = 8 bytes in-place */
    uint8_t *payload = (uint8_t *)&pkt->raw_ecg;
    for (int i = 0; i < 8; i++) {
        state ^= state << 13;
        state ^= state >> 17;
        state ^= state << 5;
        state += CHAOS_WEYL_CONST;
        uint8_t s = (uint8_t)(state & 0xFF);
        uint8_t c = payload[i] ^ s ^ prev_cipher;
        prev_cipher = c;
        payload[i] = c;
    }
}

void telemetry_decrypt_packet(telemetry_packet_t *pkt) {
    uint32_t state = (CHAOS_SECRET_KEY ^ ((uint32_t)pkt->seq_id * 0x45D9F3BU) ^ pkt->timestamp_ms);
    uint8_t prev_cipher = (CHAOS_INIT_IV ^ (uint8_t)(pkt->seq_id & 0xFF));

    uint8_t *payload = (uint8_t *)&pkt->raw_ecg;
    for (int i = 0; i < 8; i++) {
        state ^= state << 13;
        state ^= state >> 17;
        state ^= state << 5;
        state += CHAOS_WEYL_CONST;
        uint8_t s = (uint8_t)(state & 0xFF);
        uint8_t c = payload[i];
        uint8_t p = c ^ s ^ prev_cipher;
        prev_cipher = c;
        payload[i] = p;
    }
}

