#ifndef TASKS_MONITOR_H
#define TASKS_MONITOR_H

#include <stdint.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

typedef enum {
    TASK_MONITOR = 0,
    TASK_APP,
    MONITOR_COUNT
} TASKS_TIMER;

typedef struct {
    TickType_t startTime;
    TickType_t endTime;
    TickType_t executionTime;
    uint32_t  executionCount;
} TaskExecutionTime;

void taskMonitorTasks(void *pvParameters);

void startTaskTimer(TASKS_TIMER task);
void endTaskTimer(TASKS_TIMER task);

#endif // TASKS_MONITOR_H