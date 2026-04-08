#include "ecg_hw.h"
#include "ads1115.h"

#include "driver/gpio.h"
#include "driver/i2c.h"

esp_err_t ecg_hw_init(void)
{
    i2c_config_t i2c_conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = ECG_I2C_SDA_GPIO,
        .scl_io_num = ECG_I2C_SCL_GPIO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = 400000
    };

    esp_err_t err = i2c_param_config(ADS1115_I2C_PORT, &i2c_conf);
    if (err != ESP_OK) {
        return err;
    }

    err = i2c_driver_install(ADS1115_I2C_PORT, i2c_conf.mode, 0, 0, 0);
    if (err != ESP_OK && err != ESP_ERR_INVALID_STATE) {
        return err;
    }

    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << ECG_LO_PLUS_GPIO) | (1ULL << ECG_LO_MINUS_GPIO),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };

    err = gpio_config(&io_conf);
    if (err != ESP_OK) {
        return err;
    }

    err = ads1115_init(ADS1115_I2C_PORT, ADS1115_I2C_ADDR_GND);
    if (err != ESP_OK) {
        return err;
    }

    return ESP_OK;
}

esp_err_t ecg_hw_read_sample(int16_t *sample)
{
    return ads1115_read_single(ADS1115_CHANNEL_0, sample);
}

int ecg_hw_get_lo_plus(void)
{
    return gpio_get_level(ECG_LO_PLUS_GPIO);
}

int ecg_hw_get_lo_minus(void)
{
    return gpio_get_level(ECG_LO_MINUS_GPIO);
}

bool ecg_hw_is_leads_off(void)
{
    return (ecg_hw_get_lo_plus() == 1) || (ecg_hw_get_lo_minus() == 1);
}