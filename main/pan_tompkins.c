#include "pan_tompkins.h"

#include <math.h>
#include <string.h>

static float clamp_positive(float x)
{
    return (x < 0.0f) ? 0.0f : x;
}

void ecg_pt_init(ecg_pt_state_t *st, int fs_hz)
{
    memset(st, 0, sizeof(*st));

    st->fs_hz = fs_hz;
    st->mwi_window = (int)(0.150f * (float)fs_hz);
    if (st->mwi_window < 1) {
        st->mwi_window = 1;
    }
    if (st->mwi_window > PT_MWI_MAX_WINDOW) {
        st->mwi_window = PT_MWI_MAX_WINDOW;
    }

    st->threshold = 1.0f;
}

void ecg_pt_reset(ecg_pt_state_t *st)
{
    int fs_hz = st->fs_hz;
    ecg_pt_init(st, fs_hz);
}

void ecg_pt_process(ecg_pt_state_t *st, int16_t raw_sample, ecg_pt_output_t *out)
{
    memset(out, 0, sizeof(*out));

    const float x = (float)raw_sample;

    st->dc_estimate += 0.01f * (x - st->dc_estimate);
    float hp = x - st->dc_estimate;

    st->lp_state += 0.20f * (hp - st->lp_state);
    float filtered = st->lp_state;

    float derivative = filtered - st->prev_lp;
    st->prev_lp = filtered;

    float squared = derivative * derivative;

    st->mwi_sum -= st->mwi_buffer[st->mwi_index];
    st->mwi_buffer[st->mwi_index] = squared;
    st->mwi_sum += squared;
    st->mwi_index = (st->mwi_index + 1) % st->mwi_window;

    float integrated = st->mwi_sum / (float)st->mwi_window;

    out->filtered = filtered;
    out->integrated = integrated;

    if (!st->warmup_done) {
        st->warmup_sum += integrated;
        if (integrated > st->warmup_max) {
            st->warmup_max = integrated;
        }

        if (st->sample_index >= (uint32_t)st->fs_hz) {
            float warmup_mean = st->warmup_sum / (float)st->fs_hz;
            st->noise_peak = warmup_mean;
            st->signal_peak = st->warmup_max * 0.5f;
            st->threshold = st->noise_peak + 0.25f * (st->signal_peak - st->noise_peak);
            if (st->threshold < 1.0f) {
                st->threshold = 1.0f;
            }
            st->warmup_done = true;
        }

        st->prev2_integrated = st->prev1_integrated;
        st->prev1_integrated = integrated;
        st->sample_index++;
        out->threshold = st->threshold;
        return;
    }

    float half_threshold = st->threshold * 0.5f;

    if (!st->above_half_threshold && integrated > half_threshold) {
        st->above_half_threshold = true;
        st->half_threshold_start = st->sample_index;
    } else if (st->above_half_threshold && integrated <= half_threshold) {
        uint32_t width_samples = st->sample_index - st->half_threshold_start;
        st->last_qrs_width_ms = 1000.0f * ((float)width_samples / (float)st->fs_hz);
        st->above_half_threshold = false;
    }

    bool is_local_peak = (st->prev1_integrated > st->prev2_integrated) &&
                         (st->prev1_integrated >= integrated);

    if (is_local_peak) {
        uint32_t peak_index = st->sample_index - 1;
        float peak_value = st->prev1_integrated;

        uint32_t refractory_samples = (uint32_t)(0.250f * (float)st->fs_hz);
        bool outside_refractory = (!st->have_last_peak) ||
                                  ((peak_index - st->last_r_peak_index) > refractory_samples);

        if ((peak_value > st->threshold) && outside_refractory) {
            out->r_peak_detected = true;
            out->r_peak_index = peak_index;
            out->qrs_width_ms = st->last_qrs_width_ms > 1.0f ? st->last_qrs_width_ms : 100.0f;

            if (st->have_last_peak) {
                uint32_t rr_samples = peak_index - st->last_r_peak_index;
                out->rr_ms = 1000.0f * ((float)rr_samples / (float)st->fs_hz);
                if (out->rr_ms > 1.0f) {
                    out->bpm_inst = 60000.0f / out->rr_ms;
                }
            }

            st->last_r_peak_index = peak_index;
            st->have_last_peak = true;

            st->signal_peak = 0.125f * peak_value + 0.875f * st->signal_peak;
        } else {
            st->noise_peak = 0.125f * peak_value + 0.875f * st->noise_peak;
        }

        st->threshold = st->noise_peak + 0.25f * (st->signal_peak - st->noise_peak);
        st->threshold = clamp_positive(st->threshold);
        if (st->threshold < 1.0f) {
            st->threshold = 1.0f;
        }
    }

    st->prev2_integrated = st->prev1_integrated;
    st->prev1_integrated = integrated;
    st->sample_index++;

    out->threshold = st->threshold;
}