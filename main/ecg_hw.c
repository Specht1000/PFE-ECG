#include "ecg_hw.h"

#include "ads1115.h"
#include "driver/gpio.h"
#include "main.h"

#define TAG "ECG_HW"

#define ECG_LO_PLUS_GPIO   2
#define ECG_LO_MINUS_GPIO  3

esp_err_t ecg_hw_init(void)
{
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << ECG_LO_PLUS_GPIO) | (1ULL << ECG_LO_MINUS_GPIO),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&io_conf));

    ads1115_config_t ads_cfg = {
        .i2c_addr = ADS1115_I2C_ADDR_GND,
        .pga = ADS1115_PGA_4_096V,
        .data_rate = ADS1115_DR_250SPS,
        .single_shot = false,
    };

    ESP_ERROR_CHECK(ads1115_init(&ads_cfg));

    LOG(TAG, "ECG hardware initialized");
    return ESP_OK;
}

esp_err_t ecg_hw_read_sample(int16_t *sample)
{
    return ads1115_read_raw(sample);
}

bool ecg_hw_get_lo_plus(void)
{
    return gpio_get_level(ECG_LO_PLUS_GPIO) != 0;
}

bool ecg_hw_get_lo_minus(void)
{
    return gpio_get_level(ECG_LO_MINUS_GPIO) != 0;
}

bool ecg_hw_is_leads_off(void)
{
    return ecg_hw_get_lo_plus() || ecg_hw_get_lo_minus();
}