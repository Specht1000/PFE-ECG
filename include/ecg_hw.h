#ifndef ECG_HW_H
#define ECG_HW_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ECG_I2C_SDA_GPIO     21
#define ECG_I2C_SCL_GPIO     22

#define ECG_LO_PLUS_GPIO     34
#define ECG_LO_MINUS_GPIO    35

esp_err_t ecg_hw_init(void);
esp_err_t ecg_hw_read_sample(int16_t *sample);
bool ecg_hw_is_leads_off(void);
int ecg_hw_get_lo_plus(void);
int ecg_hw_get_lo_minus(void);

#ifdef __cplusplus
}
#endif

#endif // ECG_HW_H