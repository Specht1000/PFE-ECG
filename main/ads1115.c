#include "ads1115.h"
#include "esp_rom_sys.h"

static i2c_port_t s_port = ADS1115_I2C_PORT;
static uint8_t s_addr = ADS1115_I2C_ADDR_GND;

#define ADS1115_REG_CONVERSION   0x00
#define ADS1115_REG_CONFIG       0x01

static esp_err_t ads1115_write_reg(uint8_t reg, uint16_t value)
{
    uint8_t data[3];
    data[0] = reg;
    data[1] = (uint8_t)((value >> 8) & 0xFF);
    data[2] = (uint8_t)(value & 0xFF);

    return i2c_master_write_to_device(s_port, s_addr, data, sizeof(data), pdMS_TO_TICKS(100));
}

static esp_err_t ads1115_read_reg(uint8_t reg, uint16_t *value)
{
    uint8_t data[2] = {0};

    esp_err_t err = i2c_master_write_read_device(
        s_port,
        s_addr,
        &reg,
        1,
        data,
        2,
        pdMS_TO_TICKS(100)
    );

    if (err != ESP_OK) {
        return err;
    }

    *value = ((uint16_t)data[0] << 8) | data[1];
    return ESP_OK;
}

esp_err_t ads1115_init(i2c_port_t port, uint8_t addr)
{
    s_port = port;
    s_addr = addr;
    return ESP_OK;
}

esp_err_t ads1115_read_single(ads1115_channel_t channel, int16_t *raw_value)
{
    if (raw_value == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    uint16_t mux_bits = 0;
    switch (channel) {
        case ADS1115_CHANNEL_0: mux_bits = 0x4000; break; // AIN0 vs GND
        case ADS1115_CHANNEL_1: mux_bits = 0x5000; break; // AIN1 vs GND
        case ADS1115_CHANNEL_2: mux_bits = 0x6000; break; // AIN2 vs GND
        case ADS1115_CHANNEL_3: mux_bits = 0x7000; break; // AIN3 vs GND
        default: return ESP_ERR_INVALID_ARG;
    }

    /*
     * Config:
     * OS       = 1 (start single conversion)
     * MUX      = channel vs GND
     * PGA      = ±4.096V
     * MODE     = single-shot
     * DR       = 860 SPS
     * COMP     = disabled
     */
    uint16_t config =
        0x8000 |       // OS
        mux_bits |
        0x0200 |       // PGA ±4.096V
        0x0100 |       // single-shot mode
        0x00E0 |       // 860 SPS
        0x0003;        // comparator disabled

    esp_err_t err = ads1115_write_reg(ADS1115_REG_CONFIG, config);
    if (err != ESP_OK) {
        return err;
    }

    esp_rom_delay_us(1500);

    uint16_t conv = 0;
    err = ads1115_read_reg(ADS1115_REG_CONVERSION, &conv);
    if (err != ESP_OK) {
        return err;
    }

    *raw_value = (int16_t)conv;
    return ESP_OK;
}