function data = read_ecg_stream(comPort, baudRate, nSamples)
if nargin < 1, comPort = "COM7"; end
if nargin < 2, baudRate = 115200; end
if nargin < 3, nSamples = 2000; end

s = serialport(comPort, baudRate);
configureTerminator(s, "LF");
flush(s);

writeline(s, "STOP");
pause(0.2);
writeline(s, "DECIM 1");
pause(0.2);
writeline(s, "START");

data = zeros(nSamples, 8);
count = 0;

while count < nSamples
    line = readline(s);
    if startsWith(line, "timestamp_us")
        continue;
    end

    vals = str2double(split(strtrim(line), ","));
    if numel(vals) == 8 && all(~isnan(vals))
        count = count + 1;
        data(count, :) = vals.';
    end
end

writeline(s, "STOP");

data = array2table(data, ...
    'VariableNames', {'timestamp_us','raw','filtered','integrated','threshold','r_peak','bpm','class_id'});

save('ecg_capture.mat', 'data');
disp('Saved ecg_capture.mat');
end