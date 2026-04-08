#ifndef ADS1115_H
#define ADS1115_H

#include <stdint.h>
#include "esp_err.h"
#include "driver/i2c.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ADS1115_I2C_PORT         I2C_NUM_0
#define ADS1115_I2C_ADDR_GND     0x48

typedef enum {
    ADS1115_CHANNEL_0 = 0,
    ADS1115_CHANNEL_1 = 1,
    ADS1115_CHANNEL_2 = 2,
    ADS1115_CHANNEL_3 = 3
} ads1115_channel_t;

esp_err_t ads1115_init(i2c_port_t port, uint8_t addr);
esp_err_t ads1115_read_single(ads1115_channel_t channel, int16_t *raw_value);

#ifdef __cplusplus
}
#endif

#endif // ADS1115_H