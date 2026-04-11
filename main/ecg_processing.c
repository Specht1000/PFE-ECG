#include "ecg_processing.h"

static int16_t ecg_buf_get_i16(const int16_t *buf, uint16_t size, int idx_mod)
{
    while (idx_mod < 0) {
        idx_mod += size;
    }

    idx_mod %= size;
    return buf[idx_mod];
}

static int32_t ecg_clip_i64_to_i32(int64_t value)
{
    if (value > 2147483647LL) {
        return 2147483647;
    }
    if (value < -2147483648LL) {
        return -2147483648LL;
    }
    return (int32_t)value;
}

void ecg_pt_init(ecg_pt_state_t *st)
{
    if (st == NULL) {
        return;
    }

    memset(st, 0, sizeof(*st));

    st->signal_level = ECG_INIT_SIGNAL_LEVEL;
    st->noise_level = ECG_INIT_NOISE_LEVEL;
    st->threshold1 = ECG_INIT_THRESHOLD;
    st->threshold2 = ECG_INIT_THRESHOLD / 2;
    st->initialized = true;
}

void ecg_pt_reset(ecg_pt_state_t *st)
{
    ecg_pt_init(st);
}

static int32_t pan_tompkins_lowpass(ecg_pt_state_t *st, int16_t x)
{
    /*
     * Low-pass clássico:
     * y[n] = 2y[n-1] - y[n-2] + x[n] - 2x[n-6] + x[n-12]
     */

    uint16_t idx = st->raw_idx;
    st->raw_buf[idx] = x;

    int16_t xn    = ecg_buf_get_i16(st->raw_buf, ECG_PT_BANDPASS_BUF_SIZE, idx);
    int16_t xn_6  = ecg_buf_get_i16(st->raw_buf, ECG_PT_BANDPASS_BUF_SIZE, idx - 6);
    int16_t xn_12 = ecg_buf_get_i16(st->raw_buf, ECG_PT_BANDPASS_BUF_SIZE, idx - 12);

    int64_t y = (2LL * st->lp_y1) - st->lp_y2 + xn - (2LL * xn_6) + xn_12;
    int32_t y32 = ecg_clip_i64_to_i32(y);

    st->lp_y2 = st->lp_y1;
    st->lp_y1 = y32;

    st->raw_idx = (st->raw_idx + 1U) % ECG_PT_BANDPASS_BUF_SIZE;

    return y32;
}

static int32_t pan_tompkins_highpass(ecg_pt_state_t *st, int32_t x_lp)
{
    /*
     * Versão simplificada:
     * high = current_lp - média lenta
     */

    st->hp_slow_avg = (st->hp_slow_avg * 31LL + x_lp) / 32LL;

    int64_t hp = (int64_t)x_lp - st->hp_slow_avg;
    return ecg_clip_i64_to_i32(hp);
}

static int32_t pan_tompkins_derivative(ecg_pt_state_t *st, int32_t x_bp)
{
    /*
     * Derivada aproximada:
     * y[n] = (2x[n] + x[n-1] - x[n-3] - 2x[n-4]) / 8
     */

    int64_t y = (2LL * x_bp + st->prev_bp_1 - st->prev_bp_3 - 2LL * st->prev_bp_4) / 8LL;
    int32_t y32 = ecg_clip_i64_to_i32(y);

    st->prev_bp_4 = st->prev_bp_3;
    st->prev_bp_3 = st->prev_bp_2;
    st->prev_bp_2 = st->prev_bp_1;
    st->prev_bp_1 = x_bp;

    return y32;
}

static int32_t pan_tompkins_square(int32_t x)
{
    int64_t sq = (int64_t)x * (int64_t)x;

    if (sq > 2147483647LL) {
        return 2147483647;
    }

    return (int32_t)sq;
}

static int32_t pan_tompkins_mwi(ecg_pt_state_t *st, int32_t x_sq)
{
    st->mwi_sum -= st->mwi_buf[st->mwi_idx];
    st->mwi_buf[st->mwi_idx] = x_sq;
    st->mwi_sum += x_sq;

    st->mwi_idx = (st->mwi_idx + 1U) % ECG_PT_MOVING_WINDOW_SIZE;

    return (int32_t)(st->mwi_sum / ECG_PT_MOVING_WINDOW_SIZE);
}

static void ecg_update_thresholds(ecg_pt_state_t *st, int32_t peak, bool is_signal)
{
    if (is_signal) {
        st->signal_level = (peak + 7 * st->signal_level) / 8;
    } else {
        st->noise_level = (peak + 7 * st->noise_level) / 8;
    }

    st->threshold1 = st->noise_level + ((st->signal_level - st->noise_level) / 4);
    st->threshold2 = st->threshold1 / 2;

    if (st->threshold1 < ECG_MIN_THRESHOLD) {
        st->threshold1 = ECG_MIN_THRESHOLD;
    }

    if (st->threshold2 < (ECG_MIN_THRESHOLD / 2)) {
        st->threshold2 = ECG_MIN_THRESHOLD / 2;
    }
}

void ecg_pt_process_sample(ecg_pt_state_t *st, int16_t sample, uint64_t now_us, ecg_pt_output_t *out)
{
    if (st == NULL || out == NULL || !st->initialized) {
        return;
    }

    memset(out, 0, sizeof(*out));
    out->raw = sample;

    int32_t lp  = pan_tompkins_lowpass(st, sample);
    int32_t hp  = pan_tompkins_highpass(st, lp);
    int32_t der = pan_tompkins_derivative(st, hp);
    int32_t sq  = pan_tompkins_square(der);
    int32_t mwi = pan_tompkins_mwi(st, sq);

    st->low_pass   = lp;
    st->high_pass  = hp;
    st->derivative = der;
    st->squared    = sq;
    st->integrated = mwi;

    out->low_pass    = lp;
    out->bandpassed  = hp;
    out->derivative  = der;
    out->squared     = sq;
    out->integrated  = mwi;
    out->threshold   = st->threshold1;
    out->bpm         = st->bpm;

    /*
     * Detecta máximo local no sinal integrado:
     * prev_integrated > prev_prev_integrated
     * prev_integrated >= current
     */
    bool local_peak =
        (st->prev_integrated > st->prev_prev_integrated) &&
        (st->prev_integrated >= mwi);

    if (local_peak) {
        int32_t peak = st->prev_integrated;

        if (peak > st->threshold1) {
            bool accepted = false;

            if (st->last_peak_us == 0ULL) {
                st->last_peak_us = now_us;
                accepted = true;
            } else {
                uint64_t rr_us = now_us - st->last_peak_us;

                if (rr_us >= ECG_RR_MIN_US && rr_us <= ECG_RR_MAX_US) {
                    st->bpm = (uint32_t)(60000000ULL / rr_us);
                    st->last_peak_us = now_us;
                    accepted = true;
                }
            }

            if (accepted) {
                out->r_peak_detected = true;
                out->bpm = st->bpm;
                ecg_update_thresholds(st, peak, true);
            } else {
                ecg_update_thresholds(st, peak, false);
            }
        } else {
            ecg_update_thresholds(st, peak, false);
        }
    }

    st->prev_prev_integrated = st->prev_integrated;
    st->prev_integrated = mwi;
}