#include "ecg_classifier.h"
#include "ecg_model_generated.h"

ecg_class_t ecg_classifier_predict(const ecg_features_t *features)
{
    return ecg_model_predict(features);
}

const char *ecg_classifier_class_to_string(ecg_class_t cls)
{
    switch (cls) {
        case ECG_CLASS_NORMAL:
            return "normal";
        case ECG_CLASS_BRADYCARDIA:
            return "bradycardia";
        case ECG_CLASS_TACHYCARDIA:
            return "tachycardia";
        case ECG_CLASS_POSSIBLE_AF:
            return "possible_af";
        default:
            return "unknown";
    }
}