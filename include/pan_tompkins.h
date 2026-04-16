#ifndef PAN_TOMPKINS_H
#define PAN_TOMPKINS_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define PT_MWI_MAX_WINDOW 64

typedef struct {
    int fs_hz;

    float dc_estimate;
    float lp_state;
    float prev_lp;

    float mwi_buffer[PT_MWI_MAX_WINDOW];
    int mwi_window;
    int mwi_index;
    float mwi_sum;

    uint32_t sample_index;

    float prev2_integrated;
    float prev1_integrated;

    bool warmup_done;
    float warmup_sum;
    float warmup_max;

    float signal_peak;
    float noise_peak;
    float threshold;

    uint32_t last_r_peak_index;
    bool have_last_peak;

    bool above_half_threshold;
    uint32_t half_threshold_start;

    float last_qrs_width_ms;
} ecg_pt_state_t;

typedef struct {
    bool r_peak_detected;
    uint32_t r_peak_index;
    float rr_ms;
    float bpm_inst;
    float qrs_width_ms;

    float filtered;
    float integrated;
    float threshold;
} ecg_pt_output_t;

void ecg_pt_init(ecg_pt_state_t *st, int fs_hz);
void ecg_pt_reset(ecg_pt_state_t *st);
void ecg_pt_process(ecg_pt_state_t *st, int16_t raw_sample, ecg_pt_output_t *out);

#ifdef __cplusplus
}
#endif

#endif // PAN_TOMPKINS_H