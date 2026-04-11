#include "main.h"

static ecg_pt_state_t s_pt_state;

static void taskApp(void *pv)
{
    (void)pv;

    int16_t ecg_sample = 0;
    ecg_pt_output_t pt_out;

    char line0[32];
    char line1[32];
    char line2[32];
    char line3[32];

    while (1) {
        startTaskTimer(TASK_APP);

        bool leads_off = ecg_hw_is_leads_off();

        if (leads_off) {
            LOG("APP", "Electrodes disconnected! LO+=%d LO-=%d",
                ecg_hw_get_lo_plus(),
                ecg_hw_get_lo_minus());

            sh1106_clear();
            sh1106_draw_text_line(0, "PFE ECG");
            sh1106_draw_text_line(2, "Eletrodos soltos");
            sh1106_draw_text_line(3, "Verifique conexao");
        } 
        else {
            if (ecg_hw_read_sample(&ecg_sample) == ESP_OK) {
                uint64_t now_us = (uint64_t)esp_timer_get_time();

                ecg_pt_process_sample(&s_pt_state, ecg_sample, now_us, &pt_out);

                LOG("APP",
                    "RAW=%d BP=%ld DER=%ld MWI=%ld TH=%ld BPM=%" PRIu32 " PEAK=%d",
                    pt_out.raw,
                    (long)pt_out.bandpassed,
                    (long)pt_out.derivative,
                    (long)pt_out.integrated,
                    (long)pt_out.threshold,
                    pt_out.bpm,
                    pt_out.r_peak_detected ? 1 : 0);

                snprintf(line0, sizeof(line0), "PFE ECG");
                snprintf(line1, sizeof(line1), "ECG:%d", pt_out.raw);
                snprintf(line2, sizeof(line2), "BPM:%" PRIu32, pt_out.bpm);
                snprintf(line3, sizeof(line3), "Pk:%d Th:%ld",
                         pt_out.r_peak_detected ? 1 : 0,
                         (long)pt_out.threshold);

                sh1106_clear();
                sh1106_draw_text_line(0, line0);
                sh1106_draw_text_line(1, line1);
                sh1106_draw_text_line(2, line2);
                sh1106_draw_text_line(3, line3);
            } 
            else {
                LOG("APP", "Failed to read ECG sample");
            }
        }

        /*
         * ~200 Hz
         */
        vTaskDelay(pdMS_TO_TICKS(5));

        endTaskTimer(TASK_APP);
    }
}

void app_main(void)
{
    LOG("BOOT", "PFE_ECG starting...");

    esp_err_t err;

    err = ecg_hw_init();
    if (err != ESP_OK) {
        LOG("BOOT", "ecg_hw_init failed: %s", esp_err_to_name(err));
        return;
    }

    err = sh1106_init(SH1106_I2C_PORT, SH1106_I2C_ADDR);
    if (err != ESP_OK) {
        LOG("BOOT", "sh1106_init failed: %s", esp_err_to_name(err));
        return;
    }

    ecg_pt_init(&s_pt_state);

    sh1106_clear();
    sh1106_draw_text_line(0, "PFE ECG");
    sh1106_draw_text_line(2, "Starting...");

    xTaskCreate(taskMonitorTasks, "task_monitor", 4096, NULL, 5, NULL);
    xTaskCreate(taskApp,          "task_app",     4096, NULL, 4, NULL);
}