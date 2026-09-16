% ONE_load_real_ecg.m
% Loads and visualizes the first 30 seconds of raw WESAD chest ECG for Subject S2.
% Demonstrates baseline centering, 0.5-40 Hz bandpass filtering, and initial peak detection.

clear;
clc;
close all;

%% 1. Configuration & Paths
project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
filename = fullfile(project_root, 'data', 'raw', 'WESAD', 'S2', 'S2_respiban.txt');

Fs = 700;              % RespiBAN sampling frequency (Hz)
duration = 30;         % Seconds to load
N = Fs * duration;     % Total samples

%% 2. Load Raw RespiBAN Text Stream
if ~isfile(filename)
    error('Raw file not found: %s\nPlease ensure WESAD S2 is extracted under data/raw/WESAD/S2/', filename);
end

fid = fopen(filename, 'r');
if fid == -1
    error('Could not open file: %s', filename);
end

% Skip 3 header metadata lines
fgetl(fid); fgetl(fid); fgetl(fid);

% Read first N samples across 10 channels
data = textscan(fid, '%f %f %f %f %f %f %f %f %f %f', N, ...
    'Delimiter', {' ', '\t'}, 'MultipleDelimsAsOne', true);
fclose(fid);

ecg_raw = data{3}; % Channel 1 = ECG (Lead II)
t = (0:length(ecg_raw)-1) / Fs;

fprintf('Loaded %d samples (%.2f s) at %d Hz from S2.\n', length(ecg_raw), duration, Fs);

%% 3. Preprocessing (DC Removal & Bandpass Filter)
ecg_centered = ecg_raw - mean(ecg_raw);

% 4th-order Butterworth bandpass (0.5 - 40 Hz)
[b, a] = butter(4, [0.5, 40] / (Fs / 2), 'bandpass');
ecg_filtered = filtfilt(b, a, ecg_centered);

%% 4. R-Peak & RR Interval Detection
min_distance = round(0.35 * Fs); % Min 350 ms between beats (~170 BPM max)
noise_level = 1.4826 * median(abs(ecg_filtered - median(ecg_filtered)));
min_prominence = 3.0 * noise_level;

[peak_vals, peak_locs] = findpeaks(ecg_filtered, ...
    'MinPeakDistance', min_distance, ...
    'MinPeakProminence', min_prominence);

peak_times = (peak_locs - 1) / Fs;
RR = diff(peak_times); % Seconds
HR = 60 ./ RR;         % Instantaneous BPM

fprintf('Detected %d R-peaks. Mean HR: %.1f BPM, Mean RR: %.3f s.\n', ...
    length(peak_locs), mean(HR), mean(RR));

%% 5. Visualization (Multi-Panel Figure)
figure('Name', 'WESAD S2 ECG Inspection', 'Position', [100 100 1100 700], 'Color', 'white');

subplot(3, 1, 1);
plot(t, ecg_raw, 'Color', [0.4 0.4 0.4]);
xlabel('Time (s)'); ylabel('Raw ADC');
title('Raw WESAD Chest ECG (Lead II) - S2');
grid on;

subplot(3, 1, 2);
plot(t, ecg_filtered, 'b', 'LineWidth', 0.8);
hold on;
plot(peak_times, peak_vals, 'rv', 'MarkerFaceColor', 'r', 'MarkerSize', 5);
xlabel('Time (s)'); ylabel('Amplitude');
title('Filtered ECG (0.5 - 40 Hz) with Detected R-Peaks');
legend('Filtered Signal', 'R-Peaks', 'Location', 'northeast');
grid on;

subplot(3, 1, 3);
plot(peak_times(2:end), HR, 'k-o', 'LineWidth', 1.0, 'MarkerFaceColor', [0.2 0.7 0.3], 'MarkerSize', 4);
xlabel('Time (s)'); ylabel('Heart Rate (BPM)');
title('Instantaneous Heart Rate Trajectory');
grid on;
