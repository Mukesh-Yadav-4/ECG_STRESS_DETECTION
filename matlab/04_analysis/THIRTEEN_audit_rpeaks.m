clear;
clc;
close all;

%% Project root
project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));

data_folder = fullfile(project_root, 'data', 'processed');

Fs = 700;

%% Subjects to audit
subjects = {'S11','S16'};

%% Condition start times
% These will be found automatically from labels.

for s = 1:length(subjects)

    subject = subjects{s};

    fprintf('\n========================================\n');
    fprintf('AUDITING %s\n', subject);
    fprintf('========================================\n');

    %% Load subject
    filename = fullfile( ...
        data_folder, ...
        [subject '_ECG_labels.mat']);

    load(filename);

    ecg = double(ecg(:));
    labels = double(labels(:));

    %% Find baseline and stress segments

    baseline_mask = labels == 1;
    stress_mask   = labels == 2;

    baseline_start = find(diff([false; baseline_mask]) == 1);
    stress_start   = find(diff([false; stress_mask]) == 1);

    %% First 60-second window

    window_samples = 60 * Fs;

    baseline_ecg = ecg( ...
        baseline_start(1) : ...
        baseline_start(1) + window_samples - 1);

    stress_ecg = ecg( ...
        stress_start(1) : ...
        stress_start(1) + window_samples - 1);

    %% Filter

    low_cutoff = 0.5;
    high_cutoff = 40;

    [b,a] = butter(4, ...
        [low_cutoff high_cutoff]/(Fs/2), ...
        'bandpass');

    baseline_filtered = filtfilt(b,a,baseline_ecg);
    stress_filtered   = filtfilt(b,a,stress_ecg);

    %% Adaptive thresholds

    baseline_noise = ...
        1.4826 * median(abs( ...
        baseline_filtered - median(baseline_filtered)));

    stress_noise = ...
        1.4826 * median(abs( ...
        stress_filtered - median(stress_filtered)));

    %% Detect peaks

    [baseline_pks, baseline_locs] = findpeaks( ...
        baseline_filtered, ...
        'MinPeakDistance', round(0.35*Fs), ...
        'MinPeakProminence', 3*baseline_noise);

    [stress_pks, stress_locs] = findpeaks( ...
        stress_filtered, ...
        'MinPeakDistance', round(0.35*Fs), ...
        'MinPeakProminence', 3*stress_noise);

    %% Print results

    fprintf('\nBaseline peaks: %d\n', length(baseline_locs));
    fprintf('Stress peaks:   %d\n', length(stress_locs));

    fprintf('Baseline HR: %.2f BPM\n', ...
        60 / mean(diff(baseline_locs/Fs)));

    fprintf('Stress HR: %.2f BPM\n', ...
        60 / mean(diff(stress_locs/Fs)));

    %% Time vector

    t = (0:window_samples-1)/Fs;

    %% Baseline plot

    figure;

    plot(t, baseline_filtered);
    hold on;

    plot( ...
        (baseline_locs-1)/Fs, ...
        baseline_pks, ...
        'ro');

    xlabel('Time (seconds)');
    ylabel('Amplitude');

    title([subject ' - Baseline Window 1']);

    legend('Filtered ECG','Detected R-peaks');

    grid on;

    %% Stress plot

    figure;

    plot(t, stress_filtered);
    hold on;

    plot( ...
        (stress_locs-1)/Fs, ...
        stress_pks, ...
        'ro');

    xlabel('Time (seconds)');
    ylabel('Amplitude');

    title([subject ' - Stress Window 1']);

    legend('Filtered ECG','Detected R-peaks');

    grid on;

end