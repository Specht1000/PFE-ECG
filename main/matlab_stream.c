#include "matlab_stream.h"

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include <inttypes.h>

#include "driver/uart.h"
#include "main.h"

#define TAG "MATLAB"

#define MATLAB_UART              UART_NUM_0
#define MATLAB_CMD_BUFFER_SIZE   64

static bool s_stream_enabled = false;
static int s_decimation = 1;
static uint32_t s_frame_counter = 0;

static char s_cmd_buffer[MATLAB_CMD_BUFFER_SIZE];
static int s_cmd_index = 0;

static void str_to_upper(char *s)
{
    while (*s) {
        *s = (char)toupper((unsigned char)*s);
        s++;
    }
}

static void matlab_stream_print_help(void)
{
    LOG(TAG, "Commands:");
    LOG(TAG, "  START        -> start CSV stream");
    LOG(TAG, "  STOP         -> stop CSV stream");
    LOG(TAG, "  DECIM N      -> send 1 every N samples");
    LOG(TAG, "  HEADER       -> print CSV header");
    LOG(TAG, "  HELP         -> show commands");
}

static void matlab_stream_print_header(void)
{
    printf("timestamp_us,raw,filtered,integrated,threshold,r_peak,bpm,class_id\n");
}

static void handle_command(const char *cmd_in)
{
    char cmd[MATLAB_CMD_BUFFER_SIZE];
    memset(cmd, 0, sizeof(cmd));
    strncpy(cmd, cmd_in, sizeof(cmd) - 1);
    str_to_upper(cmd);

    if (strcmp(cmd, "START") == 0) {
        s_stream_enabled = true;
        s_frame_counter = 0;
        LOG(TAG, "Stream ENABLED");
        matlab_stream_print_header();
        return;
    }

    if (strcmp(cmd, "STOP") == 0) {
        s_stream_enabled = false;
        LOG(TAG, "Stream DISABLED");
        return;
    }

    if (strcmp(cmd, "HEADER") == 0) {
        matlab_stream_print_header();
        return;
    }

    if (strcmp(cmd, "HELP") == 0) {
        matlab_stream_print_help();
        return;
    }

    if (strncmp(cmd, "DECIM ", 6) == 0) {
        int value = atoi(&cmd[6]);
        if (value < 1) {
            value = 1;
        }
        s_decimation = value;
        LOG(TAG, "Decimation set to %d", s_decimation);
        return;
    }

    LOG(TAG, "Unknown command: %s", cmd_in);
}

void matlab_stream_init(void)
{
    s_stream_enabled = false;
    s_decimation = 1;
    s_frame_counter = 0;
    s_cmd_index = 0;
    memset(s_cmd_buffer, 0, sizeof(s_cmd_buffer));

    LOG(TAG, "MATLAB stream ready. Type HELP on serial.");
}

void matlab_stream_poll(void)
{
    uint8_t c;
    while (uart_read_bytes(MATLAB_UART, &c, 1, 0) == 1) {
        if (c == '\r') {
            continue;
        }

        if (c == '\n') {
            s_cmd_buffer[s_cmd_index] = '\0';
            if (s_cmd_index > 0) {
                handle_command(s_cmd_buffer);
            }
            s_cmd_index = 0;
            memset(s_cmd_buffer, 0, sizeof(s_cmd_buffer));
            continue;
        }

        if (s_cmd_index < (MATLAB_CMD_BUFFER_SIZE - 1)) {
            s_cmd_buffer[s_cmd_index++] = (char)c;
        }
    }
}

bool matlab_stream_is_enabled(void)
{
    return s_stream_enabled;
}

int matlab_stream_get_decimation(void)
{
    return s_decimation;
}

void matlab_stream_send_frame(uint64_t timestamp_us, const ecg_processing_output_t *out)
{
    if (!s_stream_enabled || out == NULL) {
        return;
    }

    s_frame_counter++;
    if ((s_frame_counter % (uint32_t)s_decimation) != 0u) {
        return;
    }

    printf("%" PRIu64 ",%d,%.3f,%.3f,%.3f,%d,%.2f,%d\n",
           timestamp_us,
           out->raw_sample,
           out->filtered,
           out->integrated,
           out->threshold,
           out->beat_detected ? 1 : 0,
           out->bpm_inst,
           (int)out->current_class);
}