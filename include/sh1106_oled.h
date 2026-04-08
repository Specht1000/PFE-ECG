#ifndef SH1106_OLED_H
#define SH1106_OLED_H

#include <stdint.h>
#include "esp_err.h"
#include "driver/i2c.h"

#ifdef __cplusplus
extern "C" {
#endif

#define SH1106_I2C_PORT      I2C_NUM_0
#define SH1106_I2C_ADDR      0x3C

#define SH1106_WIDTH         128
#define SH1106_HEIGHT        64
#define SH1106_PAGES         8

esp_err_t sh1106_init(i2c_port_t port, uint8_t addr);
esp_err_t sh1106_clear(void);
esp_err_t sh1106_draw_text_line(uint8_t line, const char *text);

#ifdef __cplusplus
}
#endif

#endif // SH1106_OLED_H