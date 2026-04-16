#include "ecg_model_generated.h"

ecg_class_t ecg_model_predict(const ecg_features_t *f)
{
    if (f == 0) {
        return ECG_CLASS_UNKNOWN;
    }

    if (f->hr_mean_bpm < 60.0f) {
        return ECG_CLASS_BRADYCARDIA;
    }

    if (f->hr_mean_bpm > 100.0f) {
        return ECG_CLASS_TACHYCARDIA;
    }

    if ((f->rr_cv > 0.10f) ||
        (f->rr_std_ms > 110.0f) ||
        ((f->rr_std_ms > 80.0f) && (f->hr_std_bpm > 8.0f))) {
        return ECG_CLASS_POSSIBLE_AF;
    }

    return ECG_CLASS_NORMAL;
}