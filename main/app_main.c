#include "main.h"
#include "ecg_classifier.h"

#define TAG "APP"

#define ECG_FS_HZ 250
#define OLED_I2C_PORT I2C_NUM_0
#define OLED_I2C_ADDR 0x3C

typedef struct {
    bool oled_ok;
    bool ecg_hw_ok;
    bool ads_read_ok;
    bool leads_connected;
    bool signal_has_variation;
    int16_t first_sample;
    int16_t min_sample;
    int16_t max_sample;
} system_check_t;

static sh1106_t s_oled;
static ecg_processing_t s_ecg_ctx;

static void oled_show_4lines(const char *l0, const char *l1, const char *l2, const char *l3)
{
    sh1106_clear(&s_oled);
    sh1106_draw_text_line(&s_oled, 0, l0 ? l0 : "");
    sh1106_draw_text_line(&s_oled, 2, l1 ? l1 : "");
    sh1106_draw_text_line(&s_oled, 3, l2 ? l2 : "");
    sh1106_draw_text_line(&s_oled, 4, l3 ? l3 : "");
}

static void run_startup_check(system_check_t *chk)
{
    memset(chk, 0, sizeof(*chk));

    chk->oled_ok = (sh1106_init(&s_oled, OLED_I2C_PORT, OLED_I2C_ADDR) == ESP_OK);
    if (chk->oled_ok) {
        sh1106_clear(&s_oled);
        sh1106_draw_text_line(&s_oled, 0, "PFE ECG");
        sh1106_draw_text_line(&s_oled, 2, "Startup check...");
    }

    LOG(TAG, "Starting system check");

    chk->ecg_hw_ok = (ecg_hw_init() == ESP_OK);
    if (!chk->ecg_hw_ok) {
        LOG(TAG, "ECG hardware init FAILED");
        return;
    }

    LOG(TAG, "ECG hardware init OK");

    chk->leads_connected = !ecg_hw_is_leads_off();
    LOG(TAG, "Leads connected: %s", chk->leads_connected ? "YES" : "NO");

    int16_t sample = 0;
    int16_t min_v = 32767;
    int16_t max_v = -32768;
    int16_t first_v = 0;
    bool first_valid = false;
    int ok_reads = 0;

    for (int i = 0; i < 100; ++i) {
        if (ecg_hw_read_sample(&sample) == ESP_OK) {
            if (!first_valid) {
                first_v = sample;
                first_valid = true;
            }

            if (sample < min_v) {
                min_v = sample;
            }
            if (sample > max_v) {
                max_v = sample;
            }

            ok_reads++;
        }
        vTaskDelay(pdMS_TO_TICKS(4));
    }

    chk->ads_read_ok = (ok_reads > 0);
    chk->first_sample = first_v;
    chk->min_sample = min_v;
    chk->max_sample = max_v;
    chk->signal_has_variation = ((max_v - min_v) > 10);

    LOG(TAG, "ADS read OK: %s", chk->ads_read_ok ? "YES" : "NO");
    LOG(TAG, "First sample: %d", chk->first_sample);
    LOG(TAG, "Min sample: %d", chk->min_sample);
    LOG(TAG, "Max sample: %d", chk->max_sample);
    LOG(TAG, "Signal variation: %s (delta=%d)",
        chk->signal_has_variation ? "YES" : "NO",
        (int)(chk->max_sample - chk->min_sample));
}

static void show_check_result(const system_check_t *chk)
{
    char l1[32];
    char l2[32];
    char l3[32];

    snprintf(l1, sizeof(l1), "OLED:%s ECG:%s",
             chk->oled_ok ? "OK" : "ERR",
             chk->ecg_hw_ok ? "OK" : "ERR");

    snprintf(l2, sizeof(l2), "ADC:%s Lead:%s",
             chk->ads_read_ok ? "OK" : "ERR",
             chk->leads_connected ? "OK" : "OFF");

    snprintf(l3, sizeof(l3), "Var:%s d=%d",
             chk->signal_has_variation ? "OK" : "BAD",
             (int)(chk->max_sample - chk->min_sample));

    oled_show_4lines("Self-test final", l1, l2, l3);
}

static void task_app(void *pv)
{
    (void)pv;

    int16_t ecg_sample = 0;
    float last_bpm = 0.0f;
    TickType_t last_wake = xTaskGetTickCount();

    while (1) {
        startTaskTimer(TASK_APP);

        bool leads_off = ecg_hw_is_leads_off();

        if (leads_off) {
            LOG(TAG, "Electrodes disconnected! LO+=%d LO-=%d",
                ecg_hw_get_lo_plus(),
                ecg_hw_get_lo_minus());

            oled_show_4lines("PFE ECG", "Electrodes disconnected", "Verify connection", "No reading available");
            vTaskDelay(pdMS_TO_TICKS(200));
            continue;
        }

        if (ecg_hw_read_sample(&ecg_sample) == ESP_OK) {
            ecg_processing_output_t out;
            ecg_processing_process_sample(&s_ecg_ctx, ecg_sample, &out);

            if (out.beat_detected && out.bpm_inst > 1.0f) {
                last_bpm = out.bpm_inst;
            }

            if (out.class_updated) {
                LOG(TAG,
                    "Beat | BPM=%.1f | class=%s | rr_mean=%.1f | rr_std=%.1f | rr_cv=%.3f | qrs=%.1f",
                    last_bpm,
                    ecg_classifier_class_to_string(out.current_class),
                    out.features.rr_mean_ms,
                    out.features.rr_std_ms,
                    out.features.rr_cv,
                    out.features.qrs_width_mean_ms);
            }

            char line1[32];
            char line2[32];
            char line3[32];

            snprintf(line1, sizeof(line1), "BPM: %.1f", last_bpm);
            snprintf(line2, sizeof(line2), "Sample: %d", ecg_sample);
            snprintf(line3, sizeof(line3), "%s",
                     s_ecg_ctx.class_valid
                        ? ecg_classifier_class_to_string(s_ecg_ctx.last_class)
                        : "warming up");

            oled_show_4lines("PFE ECG", line1, line2, line3);
        }

        vTaskDelayUntil(&last_wake, pdMS_TO_TICKS(1000 / ECG_FS_HZ));

        endTaskTimer(TASK_APP);
    }
}

void app_main(void)
{
    system_check_t chk;

    LOG(TAG, "PFE ECG booting...");
    run_startup_check(&chk);

    if (chk.oled_ok) {
        show_check_result(&chk);
        vTaskDelay(pdMS_TO_TICKS(2500));
    }

    if (!chk.ecg_hw_ok || !chk.ads_read_ok) {
        LOG(TAG, "Critical startup failure. Halting application.");
        while (1) {
            if (chk.oled_ok) {
                oled_show_4lines("PFE ECG", "Critical failure", "Verify ADC/ECG", "Restart device");
            }
            vTaskDelay(pdMS_TO_TICKS(1000));
        }
    }

    ecg_processing_init(&s_ecg_ctx, ECG_FS_HZ);

    LOG(TAG, "Startup check finished. Entering monitoring mode.");

    xTaskCreate(taskMonitorTasks, "task_monitor", 4096, NULL, 5, NULL);
    xTaskCreate(task_app, "task_app", 4096, NULL, 5, NULL);
}