#ifndef ECG_HW_H
#define ECG_HW_H

#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

esp_err_t ecg_hw_init(void);
esp_err_t ecg_hw_read_sample(int16_t *sample);

bool ecg_hw_is_leads_off(void);
bool ecg_hw_get_lo_plus(void);
bool ecg_hw_get_lo_minus(void);

#ifdef __cplusplus
}
#endif

#endif // ECG_HW_H