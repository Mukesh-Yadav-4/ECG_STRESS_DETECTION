clear;
clc;
close all;

%% Load data
project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));

data_file = fullfile( ...
    project_root, ...
    'data', ...
    'processed', ...
    'S2_ECG_labels.mat');

load(data_file);

ecg = ecg(:);
Fs = double(Fs);

%% Condition start times
baseline_start_min = 5.11;
stress_start_min   = 37.89;

baseline_start = round(baseline_start_min * 60 * Fs) + 1;
stress_start   = round(stress_start_min   * 60 * Fs) + 1;

%% Window settings
window_duration = 60;          % seconds
samples_per_window = round(window_duration * Fs);
number_of_windows = 5;

%% Band-pass filter
low_cutoff = 0.5;
high_cutoff = 40;

[b,a] = butter(4, ...
    [low_cutoff high_cutoff] / (Fs/2), ...
    'bandpass');

%% Storage
baseline_peaks = cell(number_of_windows,1);
stress_peaks   = cell(number_of_windows,1);

baseline_peak_times = cell(number_of_windows,1);
stress_peak_times   = cell(number_of_windows,1);

%% Process windows
for k = 1:number_of_windows

    %% ----- BASELINE -----

    start_idx = baseline_start + (k-1)*samples_per_window;
    end_idx   = start_idx + samples_per_window - 1;

    x = ecg(start_idx:end_idx);

    % Filter
    x = filtfilt(b,a,x);

    % Robust noise estimate without Statistics Toolbox
    noise_level = 1.4826 * median(abs(x - median(x)));

    % Adaptive prominence threshold
    min_prominence = 3 * noise_level;

    % Detect R-peaks
    [pks,locs] = findpeaks(x, ...
        'MinPeakDistance', round(0.35*Fs), ...
        'MinPeakProminence', min_prominence);

    baseline_peaks{k} = locs;
    baseline_peak_times{k} = (locs-1)/Fs;


    %% ----- STRESS -----

    start_idx = stress_start + (k-1)*samples_per_window;
    end_idx   = start_idx + samples_per_window - 1;

    x = ecg(start_idx:end_idx);

    % Filter
    x = filtfilt(b,a,x);

    % Robust noise estimate
    noise_level = 1.4826 * median(abs(x - median(x)));

    % Adaptive prominence threshold
    min_prominence = 3 * noise_level;

    % Detect R-peaks
    [pks,locs] = findpeaks(x, ...
        'MinPeakDistance', round(0.35*Fs), ...
        'MinPeakProminence', min_prominence);

    stress_peaks{k} = locs;
    stress_peak_times{k} = (locs-1)/Fs;

end

%% Print peak counts

fprintf('\nR-PEAK COUNTS\n');
fprintf('-------------\n');

for k = 1:number_of_windows

    fprintf('Baseline Window %d: %d peaks\n', ...
        k, length(baseline_peaks{k}));

    fprintf('Stress Window %d:   %d peaks\n', ...
        k, length(stress_peaks{k}));

end

%% Time vector
t_window = (0:samples_per_window-1)/Fs;

%% Visualize Baseline Window 1

x = ecg(baseline_start : ...
        baseline_start + samples_per_window - 1);

x = filtfilt(b,a,x);

noise_level = 1.4826 * median(abs(x - median(x)));

[pks,locs] = findpeaks(x, ...
    'MinPeakDistance', round(0.35*Fs), ...
    'MinPeakProminence', 3*noise_level);

figure;

plot(t_window,x);
hold on;

plot((locs-1)/Fs,pks,'ro');

xlabel('Time (seconds)');
ylabel('Amplitude');

title('Baseline Window 1 - Detected R-Peaks');

legend('Filtered ECG','Detected R-peaks');

grid on;


%% Visualize Stress Window 1

x = ecg(stress_start : ...
        stress_start + samples_per_window - 1);

x = filtfilt(b,a,x);

noise_level = 1.4826 * median(abs(x - median(x)));

[pks,locs] = findpeaks(x, ...
    'MinPeakDistance', round(0.35*Fs), ...
    'MinPeakProminence', 3*noise_level);

figure;

plot(t_window,x);
hold on;

plot((locs-1)/Fs,pks,'ro');

xlabel('Time (seconds)');
ylabel('Amplitude');

title('Stress Window 1 - Detected R-Peaks');

legend('Filtered ECG','Detected R-peaks');

grid on;