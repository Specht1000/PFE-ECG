#ifndef MAIN_H
#define MAIN_H

#include <stdio.h>
#include <inttypes.h>
#include "tasks_monitor.h"
#include "ads1115.h"
#include "ecg_hw.h"
#include "ecg_processing.h"
#include "sh1106_oled.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_timer.h"

#define ENABLE_DEBUG

#ifdef __cplusplus
extern "C" {
#endif

#ifdef ENABLE_DEBUG
    #define LOG(tag, fmt, ...) printf("[" tag "] " fmt "\n", ##__VA_ARGS__)
#else
    #define LOG(tag, fmt, ...) ((void)0)
#endif

void app_main(void);

#ifdef __cplusplus
}
#endif

#endif // MAIN_H