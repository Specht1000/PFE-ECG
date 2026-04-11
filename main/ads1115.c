#include "ads1115.h"

static esp_err_t ads1115_write_reg(ads1115_t *dev, uint8_t reg, uint16_t value)
{
    if (dev == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    uint8_t data[3];
    data[0] = reg;
    data[1] = (uint8_t)((value >> 8) & 0xFF);
    data[2] = (uint8_t)(value & 0xFF);

    return i2c_master_write_to_device(
        dev->port,
        dev->addr,
        data,
        sizeof(data),
        pdMS_TO_TICKS(ADS1115_I2C_TIMEOUT_MS)
    );
}

static esp_err_t ads1115_read_reg(ads1115_t *dev, uint8_t reg, uint16_t *value)
{
    if (dev == NULL || value == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    uint8_t data[2] = {0};

    esp_err_t err = i2c_master_write_read_device(
        dev->port,
        dev->addr,
        &reg,
        1,
        data,
        2,
        pdMS_TO_TICKS(ADS1115_I2C_TIMEOUT_MS)
    );

    if (err != ESP_OK) {
        return err;
    }

    *value = ((uint16_t)data[0] << 8) | data[1];
    return ESP_OK;
}

static uint16_t ads1115_build_mux_bits(ads1115_channel_t channel)
{
    switch (channel) {
        case ADS1115_CHANNEL_0: return ADS1115_CONFIG_MUX_AIN0_GND;
        case ADS1115_CHANNEL_1: return ADS1115_CONFIG_MUX_AIN1_GND;
        case ADS1115_CHANNEL_2: return ADS1115_CONFIG_MUX_AIN2_GND;
        case ADS1115_CHANNEL_3: return ADS1115_CONFIG_MUX_AIN3_GND;
        default: return ADS1115_CONFIG_MUX_AIN0_GND;
    }
}

static uint16_t ads1115_build_gain_bits(ads1115_gain_t gain)
{
    switch (gain) {
        case ADS1115_GAIN_6_144V: return ADS1115_CONFIG_PGA_6_144V;
        case ADS1115_GAIN_4_096V: return ADS1115_CONFIG_PGA_4_096V;
        case ADS1115_GAIN_2_048V: return ADS1115_CONFIG_PGA_2_048V;
        case ADS1115_GAIN_1_024V: return ADS1115_CONFIG_PGA_1_024V;
        case ADS1115_GAIN_0_512V: return ADS1115_CONFIG_PGA_0_512V;
        case ADS1115_GAIN_0_256V: return ADS1115_CONFIG_PGA_0_256V;
        default: return ADS1115_CONFIG_PGA_2_048V;
    }
}

static uint16_t ads1115_build_data_rate_bits(ads1115_data_rate_t data_rate)
{
    switch (data_rate) {
        case ADS1115_DATA_RATE_8_SPS:   return ADS1115_CONFIG_DR_8_SPS;
        case ADS1115_DATA_RATE_16_SPS:  return ADS1115_CONFIG_DR_16_SPS;
        case ADS1115_DATA_RATE_32_SPS:  return ADS1115_CONFIG_DR_32_SPS;
        case ADS1115_DATA_RATE_64_SPS:  return ADS1115_CONFIG_DR_64_SPS;
        case ADS1115_DATA_RATE_128_SPS: return ADS1115_CONFIG_DR_128_SPS;
        case ADS1115_DATA_RATE_250_SPS: return ADS1115_CONFIG_DR_250_SPS;
        case ADS1115_DATA_RATE_475_SPS: return ADS1115_CONFIG_DR_475_SPS;
        case ADS1115_DATA_RATE_860_SPS: return ADS1115_CONFIG_DR_860_SPS;
        default: return ADS1115_CONFIG_DR_128_SPS;
    }
}

static uint16_t ads1115_build_mode_bits(ads1115_mode_t mode)
{
    return (mode == ADS1115_MODE_SINGLE_SHOT)
        ? ADS1115_CONFIG_MODE_SINGLE_SHOT
        : ADS1115_CONFIG_MODE_CONTINUOUS;
}

static uint16_t ads1115_build_config_word(const ads1115_t *dev, bool start_conversion)
{
    uint16_t config = 0;

    if (start_conversion) {
        config |= ADS1115_CONFIG_OS_SINGLE;
    }

    config |= ads1115_build_mux_bits(dev->channel);
    config |= ads1115_build_gain_bits(dev->gain);
    config |= ads1115_build_mode_bits(dev->mode);
    config |= ads1115_build_data_rate_bits(dev->data_rate);
    config |= ADS1115_CONFIG_COMP_DISABLE;

    return config;
}

esp_err_t ads1115_init(
    ads1115_t *dev,
    i2c_port_t port,
    uint8_t addr
)
{
    if (dev == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    dev->port = port;
    dev->addr = addr;
    dev->channel = ADS1115_CHANNEL_0;
    dev->gain = ADS1115_GAIN_2_048V;
    dev->data_rate = ADS1115_DATA_RATE_475_SPS;
    dev->mode = ADS1115_MODE_CONTINUOUS;

    return ESP_OK;
}

esp_err_t ads1115_configure(
    ads1115_t *dev,
    ads1115_channel_t channel,
    ads1115_gain_t gain,
    ads1115_data_rate_t data_rate,
    ads1115_mode_t mode
)
{
    if (dev == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (channel > ADS1115_CHANNEL_3) {
        return ESP_ERR_INVALID_ARG;
    }

    dev->channel = channel;
    dev->gain = gain;
    dev->data_rate = data_rate;
    dev->mode = mode;

    return ESP_OK;
}

esp_err_t ads1115_apply_config(ads1115_t *dev)
{
    if (dev == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    uint16_t config = ads1115_build_config_word(
        dev,
        (dev->mode == ADS1115_MODE_SINGLE_SHOT)
    );

    return ads1115_write_reg(dev, ADS1115_REG_CONFIG, config);
}

esp_err_t ads1115_start_single_conversion(ads1115_t *dev)
{
    if (dev == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (dev->mode != ADS1115_MODE_SINGLE_SHOT) {
        return ESP_ERR_INVALID_STATE;
    }

    uint16_t config = ads1115_build_config_word(dev, true);
    return ads1115_write_reg(dev, ADS1115_REG_CONFIG, config);
}

esp_err_t ads1115_is_conversion_ready(ads1115_t *dev, bool *ready)
{
    if (dev == NULL || ready == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    uint16_t config = 0;
    esp_err_t err = ads1115_read_reg(dev, ADS1115_REG_CONFIG, &config);
    if (err != ESP_OK) {
        return err;
    }

    *ready = ((config & ADS1115_CONFIG_OS_BUSY_MASK) != 0);
    return ESP_OK;
}

esp_err_t ads1115_read_raw(ads1115_t *dev, int16_t *raw_value)
{
    if (dev == NULL || raw_value == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    uint16_t conv = 0;
    esp_err_t err = ads1115_read_reg(dev, ADS1115_REG_CONVERSION, &conv);
    if (err != ESP_OK) {
        return err;
    }

    *raw_value = (int16_t)conv;
    return ESP_OK;
}

esp_err_t ads1115_read_single(ads1115_t *dev, int16_t *raw_value)
{
    if (dev == NULL || raw_value == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (dev->mode != ADS1115_MODE_SINGLE_SHOT) {
        return ESP_ERR_INVALID_STATE;
    }

    esp_err_t err = ads1115_start_single_conversion(dev);
    if (err != ESP_OK) {
        return err;
    }

    bool ready = false;
    int waited_ms = 0;

    while (!ready && waited_ms < ADS1115_READY_TIMEOUT_MS) {
        vTaskDelay(pdMS_TO_TICKS(ADS1115_READY_POLL_DELAY_MS));
        waited_ms += ADS1115_READY_POLL_DELAY_MS;

        err = ads1115_is_conversion_ready(dev, &ready);
        if (err != ESP_OK) {
            return err;
        }
    }

    if (!ready) {
        return ESP_ERR_TIMEOUT;
    }

    return ads1115_read_raw(dev, raw_value);
}

float ads1115_get_full_scale_voltage(ads1115_gain_t gain)
{
    switch (gain) {
        case ADS1115_GAIN_6_144V: return 6.144f;
        case ADS1115_GAIN_4_096V: return 4.096f;
        case ADS1115_GAIN_2_048V: return 2.048f;
        case ADS1115_GAIN_1_024V: return 1.024f;
        case ADS1115_GAIN_0_512V: return 0.512f;
        case ADS1115_GAIN_0_256V: return 0.256f;
        default: return 2.048f;
    }
}

float ads1115_raw_to_voltage(const ads1115_t *dev, int16_t raw_value)
{
    if (dev == NULL) {
        return 0.0f;
    }

    float fs = ads1115_get_full_scale_voltage(dev->gain);
    return ((float)raw_value * fs) / 32768.0f;
}