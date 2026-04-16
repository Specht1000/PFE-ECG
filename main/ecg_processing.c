#include "ecg_processing.h"

#include <math.h>
#include <string.h>
#include "ecg_classifier.h"

static void push_value(float *buffer, int max_size, int *count, float value)
{
    if (*count < max_size) {
        buffer[*count] = value;
        (*count)++;
        return;
    }

    for (int i = 1; i < max_size; ++i) {
        buffer[i - 1] = buffer[i];
    }
    buffer[max_size - 1] = value;
}

static float mean_f(const float *v, int n)
{
    if (n <= 0) {
        return 0.0f;
    }

    float sum = 0.0f;
    for (int i = 0; i < n; ++i) {
        sum += v[i];
    }
    return sum / (float)n;
}

static float std_f(const float *v, int n)
{
    if (n < 2) {
        return 0.0f;
    }

    float m = mean_f(v, n);
    float acc = 0.0f;
    for (int i = 0; i < n; ++i) {
        float d = v[i] - m;
        acc += d * d;
    }
    return sqrtf(acc / (float)(n - 1));
}

static float min_f(const float *v, int n)
{
    if (n <= 0) {
        return 0.0f;
    }

    float m = v[0];
    for (int i = 1; i < n; ++i) {
        if (v[i] < m) {
            m = v[i];
        }
    }
    return m;
}

static float max_f(const float *v, int n)
{
    if (n <= 0) {
        return 0.0f;
    }

    float m = v[0];
    for (int i = 1; i < n; ++i) {
        if (v[i] > m) {
            m = v[i];
        }
    }
    return m;
}

static void build_features(ecg_processing_t *ctx, ecg_features_t *out)
{
    memset(out, 0, sizeof(*out));

    float rr_mean = mean_f(ctx->rr_ms_buffer, ctx->rr_count);
    float rr_std = std_f(ctx->rr_ms_buffer, ctx->rr_count);

    out->rr_mean_ms = rr_mean;
    out->rr_std_ms = rr_std;
    out->rr_min_ms = min_f(ctx->rr_ms_buffer, ctx->rr_count);
    out->rr_max_ms = max_f(ctx->rr_ms_buffer, ctx->rr_count);
    out->rr_cv = (rr_mean > 1.0f) ? (rr_std / rr_mean) : 0.0f;

    float hr_buf[ECG_RR_BUFFER_SIZE];
    for (int i = 0; i < ctx->rr_count; ++i) {
        hr_buf[i] = (ctx->rr_ms_buffer[i] > 1.0f) ? (60000.0f / ctx->rr_ms_buffer[i]) : 0.0f;
    }

    out->hr_mean_bpm = mean_f(hr_buf, ctx->rr_count);
    out->hr_std_bpm = std_f(hr_buf, ctx->rr_count);

    out->qrs_width_mean_ms = mean_f(ctx->qrs_ms_buffer, ctx->qrs_count);
    out->qrs_width_std_ms = std_f(ctx->qrs_ms_buffer, ctx->qrs_count);

    out->num_rr_intervals = (uint32_t)ctx->rr_count;
    out->num_r_peaks = (uint32_t)(ctx->rr_count + 1);
}

void ecg_processing_init(ecg_processing_t *ctx, int fs_hz)
{
    memset(ctx, 0, sizeof(*ctx));
    ecg_pt_init(&ctx->pt, fs_hz);
    ctx->last_class = ECG_CLASS_UNKNOWN;
    ctx->class_valid = false;
}

void ecg_processing_reset(ecg_processing_t *ctx)
{
    int fs_hz = ctx->pt.fs_hz;
    ecg_processing_init(ctx, fs_hz);
}

void ecg_processing_process_sample(
    ecg_processing_t *ctx,
    int16_t sample,
    ecg_processing_output_t *out
)
{
    memset(out, 0, sizeof(*out));
    out->current_class = ctx->last_class;
    out->raw_sample = sample;

    ecg_pt_output_t pt_out;
    ecg_pt_process(&ctx->pt, sample, &pt_out);

    out->filtered = pt_out.filtered;
    out->integrated = pt_out.integrated;
    out->threshold = pt_out.threshold;

    if (pt_out.r_peak_detected) {
        out->beat_detected = true;
        out->bpm_inst = pt_out.bpm_inst;

        if (pt_out.rr_ms > 50.0f && pt_out.rr_ms < 3000.0f) {
            push_value(ctx->rr_ms_buffer, ECG_RR_BUFFER_SIZE, &ctx->rr_count, pt_out.rr_ms);
        }

        if (pt_out.qrs_width_ms > 20.0f && pt_out.qrs_width_ms < 300.0f) {
            push_value(ctx->qrs_ms_buffer, ECG_QRS_BUFFER_SIZE, &ctx->qrs_count, pt_out.qrs_width_ms);
        }

        if (ctx->rr_count >= ECG_MIN_RR_FOR_CLASSIFY) {
            ecg_features_t features;
            build_features(ctx, &features);

            ctx->last_features = features;
            ctx->last_class = ecg_classifier_predict(&features);
            ctx->class_valid = true;

            out->class_updated = true;
            out->current_class = ctx->last_class;
            out->features = ctx->last_features;
        }
    }

    if (ctx->class_valid) {
        out->current_class = ctx->last_class;
        out->features = ctx->last_features;
    }
}