/**
 * @file telemetry_protocol.c
 * @brief Telemetry protocol framing and CRC-16 implementation.
 */

#include "telemetry_protocol.h"
#include <math.h>
#include <string.h>

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

    if (flags & TELEMETRY_FLAG_ENCRYPTED) {
        if (flags & TELEMETRY_FLAG_CHAOS_4D) {
            telemetry_m4d_encrypt_packet(pkt);
        } else {
            telemetry_encrypt_packet(pkt);
        }
    }

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

/* ================= NOVEL 4D MEMRISTIVE-JERK HYPERCHAOTIC CIPHER (M-4DJHS) ================= */
static m4d_state_t s_m4d_state = {
    .x = 0.12345678f,
    .y = 0.23456789f,
    .z = 0.34567890f,
    .w = 0.45678901f,
    .prev_cipher = 0x5A
};

void telemetry_m4d_reset(float x0, float y0, float z0, float w0, uint8_t iv) {
    s_m4d_state.x = x0;
    s_m4d_state.y = y0;
    s_m4d_state.z = z0;
    s_m4d_state.w = w0;
    s_m4d_state.prev_cipher = iv;
}

void telemetry_m4d_seed_nonce(uint16_t seq_id, uint32_t timestamp_ms) {
    uint32_t h_seq = (((uint32_t)seq_id * 2654435761U) ^ 0x9E3779B1U);
    uint32_t h_ts = ((timestamp_ms * 2246822519U) ^ 0x85EBCA6BU);
    uint32_t h_bio = 750000U; /* Default 750ms resting RR interval */

    float delta_x = (float)(((h_seq & 0xFFFFU) ^ (h_bio & 0xFFFFU)) % 1000U) * 1.0e-5f;
    float delta_y = (float)((((h_seq >> 16) & 0xFFFFU) ^ (h_ts & 0xFFFFU)) % 1000U) * 1.0e-5f;
    float delta_z = (float)(((h_ts >> 16) & 0xFFFFU) % 1000U) * 1.0e-5f;
    float delta_w = (float)((((h_bio >> 16) & 0xFFFFU) ^ (h_ts & 0xFFFFU)) % 1000U) * 1.0e-5f;

    s_m4d_state.x = 1.0f + delta_x;
    s_m4d_state.y = 1.0f + delta_y;
    s_m4d_state.z = 1.0f + delta_z;
    s_m4d_state.w = 1.0f + delta_w;
    s_m4d_state.prev_cipher = (uint8_t)(0x5AU ^ (uint8_t)(seq_id & 0xFFU));
}

static inline void m4d_rk4_step(m4d_state_t *st) {
    const float dt = M4D_DT;
    const float dt_half = 0.5f * dt;
    const float dt_sixth = dt / 6.0f;
    const float a = M4D_PARAM_A;
    const float b = M4D_PARAM_B;
    const float c = M4D_PARAM_C;
    const float d = M4D_PARAM_D;
    const float r = M4D_PARAM_R;

    float sx = st->x, sy = st->y, sz = st->z, sw = st->w;

    /* k1 */
    float k1_x = a * (sy - sx) + sw;
    float k1_y = c * sx - sx * sz + d * sy;
    float k1_z = sx * sy - b * sz;
    float k1_w = -r * sx;

    /* k2 */
    float x2 = sx + dt_half * k1_x;
    float y2 = sy + dt_half * k1_y;
    float z2 = sz + dt_half * k1_z;
    float w2 = sw + dt_half * k1_w;
    float k2_x = a * (y2 - x2) + w2;
    float k2_y = c * x2 - x2 * z2 + d * y2;
    float k2_z = x2 * y2 - b * z2;
    float k2_w = -r * x2;

    /* k3 */
    float x3 = sx + dt_half * k2_x;
    float y3 = sy + dt_half * k2_y;
    float z3 = sz + dt_half * k2_z;
    float w3 = sw + dt_half * k2_w;
    float k3_x = a * (y3 - x3) + w3;
    float k3_y = c * x3 - x3 * z3 + d * y3;
    float k3_z = x3 * y3 - b * z3;
    float k3_w = -r * x3;

    /* k4 */
    float x4 = sx + dt * k3_x;
    float y4 = sy + dt * k3_y;
    float z4 = sz + dt * k3_z;
    float w4 = sw + dt * k3_w;
    float k4_x = a * (y4 - x4) + w4;
    float k4_y = c * x4 - x4 * z4 + d * y4;
    float k4_z = x4 * y4 - b * z4;
    float k4_w = -r * x4;

    st->x += dt_sixth * (k1_x + 2.0f*k2_x + 2.0f*k3_x + k4_x);
    st->y += dt_sixth * (k1_y + 2.0f*k2_y + 2.0f*k3_y + k4_y);
    st->z += dt_sixth * (k1_z + 2.0f*k2_z + 2.0f*k3_z + k4_z);
    st->w += dt_sixth * (k1_w + 2.0f*k2_w + 2.0f*k3_w + k4_w);
}

uint8_t telemetry_m4d_get_keystream_byte(void) {
    m4d_rk4_step(&s_m4d_state);
    uint32_t ux, uz;
    memcpy(&ux, &s_m4d_state.x, sizeof(uint32_t));
    memcpy(&uz, &s_m4d_state.z, sizeof(uint32_t));
    uint32_t h = (ux ^ (uz * 2654435761U));
    return (uint8_t)((h ^ (h >> 8) ^ (h >> 16) ^ (h >> 24)) & 0xFFU);
}

void telemetry_m4d_encrypt_packet(telemetry_packet_t *pkt) {
    telemetry_m4d_seed_nonce(pkt->seq_id, pkt->timestamp_ms);
    uint8_t *payload = (uint8_t *)&pkt->raw_ecg;
    uint8_t prev = s_m4d_state.prev_cipher;
    for (int i = 0; i < 8; i++) {
        uint8_t s = telemetry_m4d_get_keystream_byte();
        uint8_t c = payload[i] ^ s ^ prev;
        prev = c;
        payload[i] = c;
    }
    s_m4d_state.prev_cipher = prev;
}

void telemetry_m4d_decrypt_packet(telemetry_packet_t *pkt) {
    telemetry_m4d_seed_nonce(pkt->seq_id, pkt->timestamp_ms);
    uint8_t *payload = (uint8_t *)&pkt->raw_ecg;
    uint8_t prev = s_m4d_state.prev_cipher;
    for (int i = 0; i < 8; i++) {
        uint8_t s = telemetry_m4d_get_keystream_byte();
        uint8_t c = payload[i];
        uint8_t p = c ^ s ^ prev;
        prev = c;
        payload[i] = p;
    }
    s_m4d_state.prev_cipher = prev;
}

