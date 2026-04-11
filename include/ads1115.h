#ifndef ADS1115_H
#define ADS1115_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"
#include "driver/i2c.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ADS1115_CONFIG_OS_SINGLE             0x8000
#define ADS1115_CONFIG_OS_BUSY_MASK          0x8000

#define ADS1115_CONFIG_MUX_AIN0_GND          0x4000
#define ADS1115_CONFIG_MUX_AIN1_GND          0x5000
#define ADS1115_CONFIG_MUX_AIN2_GND          0x6000
#define ADS1115_CONFIG_MUX_AIN3_GND          0x7000

#define ADS1115_CONFIG_PGA_6_144V            0x0000
#define ADS1115_CONFIG_PGA_4_096V            0x0200
#define ADS1115_CONFIG_PGA_2_048V            0x0400
#define ADS1115_CONFIG_PGA_1_024V            0x0600
#define ADS1115_CONFIG_PGA_0_512V            0x0800
#define ADS1115_CONFIG_PGA_0_256V            0x0A00

#define ADS1115_CONFIG_MODE_CONTINUOUS       0x0000
#define ADS1115_CONFIG_MODE_SINGLE_SHOT      0x0100

#define ADS1115_CONFIG_DR_8_SPS              0x0000
#define ADS1115_CONFIG_DR_16_SPS             0x0020
#define ADS1115_CONFIG_DR_32_SPS             0x0040
#define ADS1115_CONFIG_DR_64_SPS             0x0060
#define ADS1115_CONFIG_DR_128_SPS            0x0080
#define ADS1115_CONFIG_DR_250_SPS            0x00A0
#define ADS1115_CONFIG_DR_475_SPS            0x00C0
#define ADS1115_CONFIG_DR_860_SPS            0x00E0

#define ADS1115_CONFIG_COMP_DISABLE          0x0003

#define ADS1115_READY_POLL_DELAY_MS          1
#define ADS1115_READY_TIMEOUT_MS             20

#define ADS1115_REG_CONVERSION   0x00
#define ADS1115_REG_CONFIG       0x01
#define ADS1115_REG_LO_THRESH    0x02
#define ADS1115_REG_HI_THRESH    0x03

#define ADS1115_I2C_ADDR_GND     0x48
#define ADS1115_I2C_ADDR_VDD     0x49
#define ADS1115_I2C_ADDR_SDA     0x4A
#define ADS1115_I2C_ADDR_SCL     0x4B

#define ADS1115_I2C_TIMEOUT_MS   100

typedef enum {
    ADS1115_CHANNEL_0 = 0,
    ADS1115_CHANNEL_1,
    ADS1115_CHANNEL_2,
    ADS1115_CHANNEL_3
} ads1115_channel_t;

typedef enum {
    ADS1115_MODE_CONTINUOUS = 0,
    ADS1115_MODE_SINGLE_SHOT
} ads1115_mode_t;

typedef enum {
    ADS1115_GAIN_6_144V = 0,   // ±6.144V
    ADS1115_GAIN_4_096V,       // ±4.096V
    ADS1115_GAIN_2_048V,       // ±2.048V
    ADS1115_GAIN_1_024V,       // ±1.024V
    ADS1115_GAIN_0_512V,       // ±0.512V
    ADS1115_GAIN_0_256V        // ±0.256V
} ads1115_gain_t;

typedef enum {
    ADS1115_DATA_RATE_8_SPS = 0,
    ADS1115_DATA_RATE_16_SPS,
    ADS1115_DATA_RATE_32_SPS,
    ADS1115_DATA_RATE_64_SPS,
    ADS1115_DATA_RATE_128_SPS,
    ADS1115_DATA_RATE_250_SPS,
    ADS1115_DATA_RATE_475_SPS,
    ADS1115_DATA_RATE_860_SPS
} ads1115_data_rate_t;

typedef struct {
    i2c_port_t port;
    uint8_t addr;
    ads1115_channel_t channel;
    ads1115_gain_t gain;
    ads1115_data_rate_t data_rate;
    ads1115_mode_t mode;
} ads1115_t;

/**
 * @brief Inicializa a struct do dispositivo.
 */
esp_err_t ads1115_init(
    ads1115_t *dev,
    i2c_port_t port,
    uint8_t addr
);

/**
 * @brief Configura canal, ganho, taxa e modo do ADS1115.
 */
esp_err_t ads1115_configure(
    ads1115_t *dev,
    ads1115_channel_t channel,
    ads1115_gain_t gain,
    ads1115_data_rate_t data_rate,
    ads1115_mode_t mode
);

/**
 * @brief Escreve a configuração atual no registrador CONFIG.
 */
esp_err_t ads1115_apply_config(ads1115_t *dev);

/**
 * @brief Inicia uma conversão single-shot.
 * Só faz sentido se o modo estiver configurado como single-shot.
 */
esp_err_t ads1115_start_single_conversion(ads1115_t *dev);

/**
 * @brief Verifica se a conversão terminou.
 * @param ready true = conversão pronta
 */
esp_err_t ads1115_is_conversion_ready(ads1115_t *dev, bool *ready);

/**
 * @brief Lê o valor bruto do registrador de conversão.
 */
esp_err_t ads1115_read_raw(ads1115_t *dev, int16_t *raw_value);

/**
 * @brief Faz uma leitura single-shot completa:
 * dispara, espera ficar pronto, lê o valor.
 */
esp_err_t ads1115_read_single(ads1115_t *dev, int16_t *raw_value);

/**
 * @brief Converte leitura bruta para tensão em volts.
 */
float ads1115_raw_to_voltage(const ads1115_t *dev, int16_t raw_value);

/**
 * @brief Retorna o fundo de escala positivo da configuração de ganho.
 */
float ads1115_get_full_scale_voltage(ads1115_gain_t gain);

#ifdef __cplusplus
}
#endif

#endif // ADS1115_H