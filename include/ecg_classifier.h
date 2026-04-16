#ifndef ECG_CLASSIFIER_H
#define ECG_CLASSIFIER_H

#include "ecg_processing.h"

#ifdef __cplusplus
extern "C" {
#endif

ecg_class_t ecg_classifier_predict(const ecg_features_t *features);
const char *ecg_classifier_class_to_string(ecg_class_t cls);

#ifdef __cplusplus
}
#endif

#endif // ECG_CLASSIFIER_H