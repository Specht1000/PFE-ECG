#ifndef ECG_HW_H
#define ECG_HW_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"
#include "driver/gpio.h"
#include "driver/i2c.h"
#include "ads1115.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ECG_I2C_PORT         I2C_NUM_0
#define ECG_I2C_SDA_GPIO     8
#define ECG_I2C_SCL_GPIO     9
#define ECG_I2C_FREQ_HZ      400000

#define ECG_LO_PLUS_GPIO     2
#define ECG_LO_MINUS_GPIO    3

#define ECG_ADS1115_ADDR     ADS1115_I2C_ADDR_GND
#define ECG_ADS1115_CHANNEL  ADS1115_CHANNEL_0
#define ECG_ADS1115_GAIN     ADS1115_GAIN_2_048V
#define ECG_ADS1115_RATE     ADS1115_DATA_RATE_475_SPS
#define ECG_ADS1115_MODE     ADS1115_MODE_CONTINUOUS

esp_err_t ecg_hw_init(void);
esp_err_t ecg_hw_read_sample(int16_t *sample);
esp_err_t ecg_hw_read_voltage(float *voltage);

bool ecg_hw_is_leads_off(void);
int ecg_hw_get_lo_plus(void);
int ecg_hw_get_lo_minus(void);

#ifdef __cplusplus
}
#endif

#endif // ECG_HW_H