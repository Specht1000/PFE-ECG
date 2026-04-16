load('ecg_capture.mat');

t = double(data.timestamp_us);
t = (t - t(1)) / 1e6;

figure;
plot(t, data.raw);
grid on;
title('ECG Raw');
xlabel('Time (s)');
ylabel('ADC raw');

figure;
plot(t, data.filtered);
hold on;
plot(t, data.integrated);
plot(t, data.threshold, '--');
grid on;
legend('filtered','integrated','threshold');
title('Pan-Tompkins Stages');
xlabel('Time (s)');

figure;
plot(t, data.filtered);
hold on;
idx = data.r_peak > 0;
plot(t(idx), data.filtered(idx), 'ro');
grid on;
title('Detected R peaks');
xlabel('Time (s)');
ylabel('Filtered');

figure;
plot(t, data.bpm);
grid on;
title('Instant BPM');
xlabel('Time (s)');
ylabel('BPM');