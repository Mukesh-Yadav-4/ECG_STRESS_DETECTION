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

%% Known condition segments

baseline_start_min = 5.11;
stress_start_min = 37.89;

baseline_start = round(baseline_start_min * 60 * Fs) + 1;
stress_start   = round(stress_start_min   * 60 * Fs) + 1;

%% Window parameters

window_duration = 60;              % seconds
samples_per_window = window_duration * Fs;

number_of_windows = 5;

%% Storage

baseline_windows = cell(number_of_windows,1);
stress_windows = cell(number_of_windows,1);

%% Extract windows

for k = 1:number_of_windows

    % Baseline
    start_idx = baseline_start + (k-1)*samples_per_window;
    end_idx   = start_idx + samples_per_window - 1;

    baseline_windows{k} = ecg(start_idx:end_idx);

    % Stress
    start_idx = stress_start + (k-1)*samples_per_window;
    end_idx   = start_idx + samples_per_window - 1;

    stress_windows{k} = ecg(start_idx:end_idx);

end

%% Filter settings

low_cutoff = 0.5;
high_cutoff = 40;

[b,a] = butter(4, ...
    [low_cutoff high_cutoff]/(Fs/2), ...
    'bandpass');

%% Filter every window

baseline_filtered = cell(number_of_windows,1);
stress_filtered = cell(number_of_windows,1);

for k = 1:number_of_windows

    baseline_filtered{k} = filtfilt(b,a,baseline_windows{k});

    stress_filtered{k} = filtfilt(b,a,stress_windows{k});

end

fprintf('Filtering completed for %d baseline and %d stress windows.\n', ...
    number_of_windows, number_of_windows);

%% Plot window 1 after filtering

t_window = (0:samples_per_window-1)/Fs;

figure;

subplot(2,1,1);
plot(t_window, baseline_filtered{1});
xlabel('Time (seconds)');
ylabel('Amplitude');
title('Baseline Window 1 - Filtered ECG');
grid on;

subplot(2,1,2);
plot(t_window, stress_filtered{1});
xlabel('Time (seconds)');
ylabel('Amplitude');
title('Stress Window 1 - Filtered ECG');
grid on;