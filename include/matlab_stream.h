#ifndef MATLAB_STREAM_H
#define MATLAB_STREAM_H

#include <stdbool.h>
#include <stdint.h>
#include "ecg_processing.h"

#ifdef __cplusplus
extern "C" {
#endif

void matlab_stream_init(void);
void matlab_stream_poll(void);
bool matlab_stream_is_enabled(void);
int matlab_stream_get_decimation(void);
void matlab_stream_send_frame(uint64_t timestamp_us, const ecg_processing_output_t *out);

#ifdef __cplusplus
}
#endif

#endif