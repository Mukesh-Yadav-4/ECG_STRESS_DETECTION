/**
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

/* ================= 32-BIT CHAOTIC STREAM CIPHER (MARSAGLIA / WEYL) ================= */
#define CHAOS_SECRET_KEY  0x9E3779B9U
#define CHAOS_INIT_IV     0x5AU
#define CHAOS_WEYL_CONST  0x61C88647U

/**
 * @brief Reset chaotic keystream generator state and IV
 */
void telemetry_cipher_reset(uint32_t key, uint8_t iv);

/**
 * @brief Encrypt ECG samples in-place using per-packet Nonce-seeded chaotic keystream
 */
void telemetry_encrypt_packet(telemetry_packet_t *pkt);

/**
 * @brief Decrypt ECG samples in-place using per-packet Nonce-seeded chaotic keystream
 */
void telemetry_decrypt_packet(telemetry_packet_t *pkt);

#ifdef __cplusplus
}
#endif

#endif /* TELEMETRY_PROTOCOL_H */
