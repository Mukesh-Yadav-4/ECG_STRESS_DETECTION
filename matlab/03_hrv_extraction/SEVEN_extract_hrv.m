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

%% Known segment locations
baseline_start_min = 5.11;
stress_start_min   = 37.89;

baseline_start = round(baseline_start_min * 60 * Fs) + 1;
stress_start   = round(stress_start_min   * 60 * Fs) + 1;

%% Window settings
window_duration = 60;
samples_per_window = round(window_duration * Fs);
number_of_windows = 5;

%% Band-pass filter
low_cutoff = 0.5;
high_cutoff = 40;

[b,a] = butter(4, ...
    [low_cutoff high_cutoff]/(Fs/2), ...
    'bandpass');

%% Feature storage
results = zeros(number_of_windows*2, 7);

row = 1;

%% Process both conditions
for condition = 1:2

    if condition == 1
        condition_name = 'Baseline';
        condition_start = baseline_start;
    else
        condition_name = 'Stress';
        condition_start = stress_start;
    end

    for k = 1:number_of_windows

        %% Extract window
        start_idx = condition_start + ...
                    (k-1)*samples_per_window;

        end_idx = start_idx + ...
                  samples_per_window - 1;

        x = ecg(start_idx:end_idx);

        %% Filter
        x = filtfilt(b,a,x);

        %% Adaptive threshold
        noise_level = 1.4826 * ...
            median(abs(x - median(x)));

        min_prominence = 3 * noise_level;

        %% Detect R-peaks
        [pks,locs] = findpeaks(x, ...
            'MinPeakDistance',round(0.35*Fs), ...
            'MinPeakProminence',min_prominence);

        %% R-peak times
        peak_times = (locs-1)/Fs;

        %% RR intervals
        RR = diff(peak_times);

        %% Basic artifact rejection
        valid = RR >= 0.30 & RR <= 1.50;
        RR_clean = RR(valid);

        %% HR
        mean_RR = mean(RR_clean);
        mean_HR = 60 / mean_RR;

        %% SDNN
        SDNN = std(RR_clean);

        %% RMSSD
        successive_diff = diff(RR_clean);

        RMSSD = sqrt(mean(successive_diff.^2));

        %% pNN50
        pNN50 = 100 * ...
            sum(abs(successive_diff) > 0.050) / ...
            length(successive_diff);

        %% Store
        results(row,:) = [ ...
            condition, ...
            k, ...
            length(RR_clean), ...
            mean_RR, ...
            mean_HR, ...
            SDNN, ...
            RMSSD];

        row = row + 1;

        %% Print
        fprintf('%s Window %d:\n',condition_name,k);
        fprintf('  R-peaks  = %d\n',length(locs));
        fprintf('  Valid RR = %d\n',length(RR_clean));
        fprintf('  Mean RR  = %.4f s\n',mean_RR);
        fprintf('  Mean HR  = %.2f BPM\n',mean_HR);
        fprintf('  SDNN     = %.4f s\n',SDNN);
        fprintf('  RMSSD    = %.4f s\n',RMSSD);
        fprintf('  pNN50    = %.2f %%\n\n',pNN50);

    end
end

%% Create table
Condition = categorical(results(:,1), ...
    [1 2], {'Baseline','Stress'});

Window = results(:,2);
ValidBeats = results(:,3);
MeanRR = results(:,4);
MeanHR = results(:,5);
SDNN = results(:,6);
RMSSD = results(:,7);

HRV_Table = table( ...
    Condition, ...
    Window, ...
    ValidBeats, ...
    MeanRR, ...
    MeanHR, ...
    SDNN, ...
    RMSSD);

disp(HRV_Table);