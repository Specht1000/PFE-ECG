#ifndef ECG_PROCESSING_H
#define ECG_PROCESSING_H

#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#ifdef __cplusplus
extern "C" {
#endif

#define ECG_RR_MIN_US                  300000ULL   // 300 ms => 200 bpm
#define ECG_RR_MAX_US                 2000000ULL   // 2 s => 30 bpm

#define ECG_INIT_SIGNAL_LEVEL              1200
#define ECG_INIT_NOISE_LEVEL                300
#define ECG_INIT_THRESHOLD                  500
#define ECG_MIN_THRESHOLD                  100

#define ECG_PT_MOVING_WINDOW_SIZE           30
#define ECG_PT_BANDPASS_BUF_SIZE            64

typedef struct {
    /* Buffer bruto para filtros */
    int16_t raw_buf[ECG_PT_BANDPASS_BUF_SIZE];
    uint16_t raw_idx;

    /* Saídas intermediárias */
    int32_t low_pass;
    int32_t high_pass;
    int32_t derivative;
    int32_t squared;
    int32_t integrated;

    /* Estado do low-pass */
    int32_t lp_y1;
    int32_t lp_y2;

    /* Estado do high-pass */
    int64_t hp_slow_avg;

    /* Histórico para derivada */
    int32_t prev_bp_1;
    int32_t prev_bp_2;
    int32_t prev_bp_3;
    int32_t prev_bp_4;

    /* Janela móvel */
    int32_t mwi_buf[ECG_PT_MOVING_WINDOW_SIZE];
    uint16_t mwi_idx;
    int64_t mwi_sum;

    /* Pico e ritmo */
    int32_t prev_integrated;
    int32_t prev_prev_integrated;
    uint64_t last_peak_us;
    uint32_t bpm;

    /* Limiar adaptativo */
    int32_t signal_level;
    int32_t noise_level;
    int32_t threshold1;
    int32_t threshold2;

    bool initialized;
} ecg_pt_state_t;

typedef struct {
    int16_t raw;
    int32_t low_pass;
    int32_t bandpassed;
    int32_t derivative;
    int32_t squared;
    int32_t integrated;
    bool r_peak_detected;
    uint32_t bpm;
    int32_t threshold;
} ecg_pt_output_t;

void ecg_pt_init(ecg_pt_state_t *st);
void ecg_pt_reset(ecg_pt_state_t *st);
void ecg_pt_process_sample(ecg_pt_state_t *st, int16_t sample, uint64_t now_us, ecg_pt_output_t *out);

#ifdef __cplusplus
}
#endif

#endif // ECG_PROCESSING_H