#include "ads1115.h"

#include <string.h>
#include "driver/i2c.h"
#include "main.h"

#define TAG "ADS1115"

#define I2C_PORT                I2C_NUM_0
#define I2C_SDA_GPIO            8
#define I2C_SCL_GPIO            9
#define I2C_CLK_SPEED_HZ        400000

#define ADS1115_REG_CONVERSION  0x00
#define ADS1115_REG_CONFIG      0x01

static ads1115_config_t s_cfg;
static bool s_initialized = false;

static uint16_t ads1115_build_config_word(const ads1115_config_t *cfg)
{
    uint16_t word = 0;

    if (cfg->single_shot) {
        word |= (1u << 15);
    }

    word |= (0x04u << 12); /* AIN0 single-ended */
    word |= ((uint16_t)cfg->pga & 0x07u) << 9;
    word |= ((cfg->single_shot ? 1u : 0u) << 8);
    word |= ((uint16_t)cfg->data_rate & 0x07u) << 5;
    word |= 0x03u; /* comparator disabled */

    return word;
}

esp_err_t ads1115_init(const ads1115_config_t *cfg)
{
    if (cfg == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    i2c_config_t i2c_cfg = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_SDA_GPIO,
        .scl_io_num = I2C_SCL_GPIO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = I2C_CLK_SPEED_HZ,
    };

    ESP_ERROR_CHECK(i2c_param_config(I2C_PORT, &i2c_cfg));

    esp_err_t err = i2c_driver_install(I2C_PORT, I2C_MODE_MASTER, 0, 0, 0);
    if (err != ESP_OK && err != ESP_ERR_INVALID_STATE) {
        return err;
    }

    s_cfg = *cfg;

    uint16_t config_word = ads1115_build_config_word(cfg);
    uint8_t payload[3] = {
        ADS1115_REG_CONFIG,
        (uint8_t)((config_word >> 8) & 0xFF),
        (uint8_t)(config_word & 0xFF)
    };

    ESP_ERROR_CHECK(i2c_master_write_to_device(
        I2C_PORT,
        s_cfg.i2c_addr,
        payload,
        sizeof(payload),
        pdMS_TO_TICKS(100)
    ));

    s_initialized = true;
    LOG(TAG, "ADS1115 initialized, addr=0x%02X", s_cfg.i2c_addr);
    return ESP_OK;
}

esp_err_t ads1115_read_raw(int16_t *out_raw)
{
    if (!s_initialized || out_raw == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    uint8_t reg = ADS1115_REG_CONVERSION;
    uint8_t data[2] = {0};

    ESP_ERROR_CHECK(i2c_master_write_read_device(
        I2C_PORT,
        s_cfg.i2c_addr,
        &reg,
        1,
        data,
        2,
        pdMS_TO_TICKS(100)
    ));

    *out_raw = (int16_t)((data[0] << 8) | data[1]);
    return ESP_OK;
}