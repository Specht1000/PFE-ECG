#ifndef ADS1115_H
#define ADS1115_H

#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ADS1115_I2C_ADDR_GND   0x48

typedef enum {
    ADS1115_PGA_6_144V = 0,
    ADS1115_PGA_4_096V,
    ADS1115_PGA_2_048V,
    ADS1115_PGA_1_024V,
    ADS1115_PGA_0_512V,
    ADS1115_PGA_0_256V
} ads1115_pga_t;

typedef enum {
    ADS1115_DR_8SPS = 0,
    ADS1115_DR_16SPS,
    ADS1115_DR_32SPS,
    ADS1115_DR_64SPS,
    ADS1115_DR_128SPS,
    ADS1115_DR_250SPS,
    ADS1115_DR_475SPS,
    ADS1115_DR_860SPS
} ads1115_dr_t;

typedef struct {
    uint8_t i2c_addr;
    ads1115_pga_t pga;
    ads1115_dr_t data_rate;
    bool single_shot;
} ads1115_config_t;

esp_err_t ads1115_init(const ads1115_config_t *cfg);
esp_err_t ads1115_read_raw(int16_t *out_raw);

#ifdef __cplusplus
}
#endif

#endif // ADS1115_H