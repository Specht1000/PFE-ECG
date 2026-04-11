#include "ecg_hw.h"

static ads1115_t s_ads;
static bool s_ecg_hw_initialized = false;

static esp_err_t ecg_hw_i2c_init(void)
{
    i2c_config_t i2c_conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = ECG_I2C_SDA_GPIO,
        .scl_io_num = ECG_I2C_SCL_GPIO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = ECG_I2C_FREQ_HZ
    };

    esp_err_t err = i2c_param_config(ECG_I2C_PORT, &i2c_conf);
    if (err != ESP_OK) {
        return err;
    }

    err = i2c_driver_install(ECG_I2C_PORT, i2c_conf.mode, 0, 0, 0);
    if (err != ESP_OK && err != ESP_ERR_INVALID_STATE) {
        return err;
    }

    return ESP_OK;
}

static esp_err_t ecg_hw_gpio_init(void)
{
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << ECG_LO_PLUS_GPIO) | (1ULL << ECG_LO_MINUS_GPIO),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };

    return gpio_config(&io_conf);
}

static esp_err_t ecg_hw_ads1115_init(void)
{
    esp_err_t err = ads1115_init(&s_ads, ECG_I2C_PORT, ECG_ADS1115_ADDR);
    if (err != ESP_OK) {
        return err;
    }

    err = ads1115_configure(
        &s_ads,
        ECG_ADS1115_CHANNEL,
        ECG_ADS1115_GAIN,
        ECG_ADS1115_RATE,
        ECG_ADS1115_MODE
    );
    if (err != ESP_OK) {
        return err;
    }

    err = ads1115_apply_config(&s_ads);
    if (err != ESP_OK) {
        return err;
    }

    return ESP_OK;
}

esp_err_t ecg_hw_init(void)
{
    esp_err_t err = ecg_hw_i2c_init();
    if (err != ESP_OK) {
        return err;
    }

    err = ecg_hw_gpio_init();
    if (err != ESP_OK) {
        return err;
    }

    err = ecg_hw_ads1115_init();
    if (err != ESP_OK) {
        return err;
    }

    s_ecg_hw_initialized = true;
    return ESP_OK;
}

esp_err_t ecg_hw_read_sample(int16_t *sample)
{
    if (sample == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!s_ecg_hw_initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    return ads1115_read_raw(&s_ads, sample);
}

esp_err_t ecg_hw_read_voltage(float *voltage)
{
    if (voltage == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!s_ecg_hw_initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    int16_t raw = 0;
    esp_err_t err = ads1115_read_raw(&s_ads, &raw);
    if (err != ESP_OK) {
        return err;
    }

    *voltage = ads1115_raw_to_voltage(&s_ads, raw);
    return ESP_OK;
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