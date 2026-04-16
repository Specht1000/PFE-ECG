#ifndef ECG_PROCESSING_H
#define ECG_PROCESSING_H

#include <stdbool.h>
#include <stdint.h>
#include "pan_tompkins.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ECG_RR_BUFFER_SIZE         16
#define ECG_QRS_BUFFER_SIZE        16
#define ECG_MIN_RR_FOR_CLASSIFY    8

typedef enum {
    ECG_CLASS_NORMAL = 0,
    ECG_CLASS_BRADYCARDIA,
    ECG_CLASS_TACHYCARDIA,
    ECG_CLASS_POSSIBLE_AF,
    ECG_CLASS_UNKNOWN
} ecg_class_t;

typedef struct {
    float rr_mean_ms;
    float rr_std_ms;
    float rr_min_ms;
    float rr_max_ms;
    float rr_cv;

    float hr_mean_bpm;
    float hr_std_bpm;

    float qrs_width_mean_ms;
    float qrs_width_std_ms;

    uint32_t num_r_peaks;
    uint32_t num_rr_intervals;
} ecg_features_t;

typedef struct {
    ecg_pt_state_t pt;

    float rr_ms_buffer[ECG_RR_BUFFER_SIZE];
    float qrs_ms_buffer[ECG_QRS_BUFFER_SIZE];

    int rr_count;
    int qrs_count;

    ecg_features_t last_features;
    ecg_class_t last_class;
    bool class_valid;
} ecg_processing_t;

typedef struct {
    bool beat_detected;
    bool class_updated;
    float bpm_inst;
    ecg_class_t current_class;
    ecg_features_t features;
} ecg_processing_output_t;

void ecg_processing_init(ecg_processing_t *ctx, int fs_hz);
void ecg_processing_reset(ecg_processing_t *ctx);
void ecg_processing_process_sample(
    ecg_processing_t *ctx,
    int16_t sample,
    ecg_processing_output_t *out
);

#ifdef __cplusplus
}
#endif

#endif // ECG_PROCESSING_H