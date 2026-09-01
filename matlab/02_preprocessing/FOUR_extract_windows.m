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
labels = labels(:);
Fs = double(Fs);

%% Known S2 segments obtained from label analysis

baseline_start_min = 5.11;
baseline_end_min   = 24.18;

stress_start_min = 37.89;
stress_end_min   = 48.14;

%% Convert time to sample indices

baseline_start = round(baseline_start_min * 60 * Fs) + 1;
baseline_end   = round(baseline_end_min   * 60 * Fs);

stress_start = round(stress_start_min * 60 * Fs) + 1;
stress_end   = round(stress_end_min   * 60 * Fs);

%% Use first 5 minutes of each condition

window_duration = 60;       % seconds
number_of_windows = 5;

samples_per_window = window_duration * Fs;

%% Store windows

baseline_windows = cell(number_of_windows, 1);
stress_windows   = cell(number_of_windows, 1);

for k = 1:number_of_windows

    % Baseline
    idx1 = baseline_start + (k-1)*samples_per_window;
    idx2 = idx1 + samples_per_window - 1;

    baseline_windows{k} = ecg(idx1:idx2);

    % Stress
    idx1 = stress_start + (k-1)*samples_per_window;
    idx2 = idx1 + samples_per_window - 1;

    stress_windows{k} = ecg(idx1:idx2);

end

fprintf('Baseline windows created: %d\n', length(baseline_windows));
fprintf('Stress windows created: %d\n', length(stress_windows));

%% Plot first baseline and stress windows

t_window = (0:samples_per_window-1) / Fs;

figure;

subplot(2,1,1);
plot(t_window, baseline_windows{1});
xlabel('Time (seconds)');
ylabel('Amplitude');
title('S2 Baseline - 60 Second Window');
grid on;

subplot(2,1,2);
plot(t_window, stress_windows{1});
xlabel('Time (seconds)');
ylabel('Amplitude');
title('S2 Stress - 60 Second Window');
grid on;