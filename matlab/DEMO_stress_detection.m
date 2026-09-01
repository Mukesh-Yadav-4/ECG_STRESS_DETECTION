clear;
clc;
close all;

%% =========================================================
% WESAD ECG STRESS DETECTION
% TEACHER DEMONSTRATION SCRIPT
%
% This script demonstrates the complete project workflow
% using the already-generated project results.
%
% Pipeline:
%   ECG
%    ↓
%   R-peak / HRV processing
%    ↓
%   Feature analysis
%    ↓
%   Personalized normalization
%    ↓
%   LOSO classification
%    ↓
%   Final stress detection results
% ==========================================================

%% =========================================================
% 1. PROJECT SETUP
% ==========================================================

project_root = fileparts(mfilename('fullpath'));

fprintf('\n');
fprintf('====================================================\n');
fprintf('      WESAD ECG STRESS DETECTION PROJECT\n');
fprintf('====================================================\n');

fprintf('\nProject folder:\n%s\n', project_root);

%% =========================================================
% 2. LOAD S2 ECG DATA
% ==========================================================

fprintf('\n');
fprintf('====================================================\n');
fprintf('1. DATASET\n');
fprintf('====================================================\n');

data_file = fullfile( ...
    project_root, ...
    '..', ...
    'data', ...
    'processed', ...
    'S2_ECG_labels.mat');

data_file = ...
    char(java.io.File(data_file).getCanonicalPath());

load(data_file);

ecg = double(ecg(:));
labels = double(labels(:));

Fs = 700;

fprintf('Subject: S2\n');
fprintf('Sampling frequency: %d Hz\n', Fs);
fprintf('ECG samples: %d\n', length(ecg));
fprintf('Duration: %.2f minutes\n', ...
    length(ecg)/Fs/60);

%% =========================================================
% 3. DISPLAY RAW ECG
% ==========================================================

fprintf('\nDisplaying first 10 seconds of raw ECG...\n');

duration_demo = 10;

N = min(length(ecg), Fs*duration_demo);

t = (0:N-1)/Fs;

figure;

plot(t, ecg(1:N));

xlabel('Time (s)');
ylabel('ECG amplitude');

title('Raw WESAD ECG - Subject S2');

grid on;

%% =========================================================
% 4. SHOW BASELINE / STRESS LABELS
% ==========================================================

fprintf('\n');
fprintf('====================================================\n');
fprintf('2. WESAD LABELS\n');
fprintf('====================================================\n');

baseline_mask = labels == 1;
stress_mask = labels == 2;

fprintf('Baseline samples: %d\n', ...
    sum(baseline_mask));

fprintf('Stress samples:   %d\n', ...
    sum(stress_mask));

%% Find first baseline and stress segments

baseline_start = ...
    find(diff([false; baseline_mask]) == 1);

baseline_end = ...
    find(diff([baseline_mask; false]) == -1);

stress_start = ...
    find(diff([false; stress_mask]) == 1);

stress_end = ...
    find(diff([stress_mask; false]) == -1);

fprintf('\nBaseline segments: %d\n', ...
    length(baseline_start));

fprintf('Stress segments: %d\n', ...
    length(stress_start));

%% Plot labels over a section of the recording

demo_end = min(length(labels), 60*Fs*60);

time_labels = ...
    (0:demo_end-1)/Fs/60;

figure;

plot(time_labels, labels(1:demo_end));

xlabel('Time (minutes)');
ylabel('WESAD label');

title('WESAD Baseline and Stress Labels');

grid on;

%% =========================================================
% 5. DEMONSTRATE R-PEAK PROCESSING
% ==========================================================

fprintf('\n');
fprintf('====================================================\n');
fprintf('3. ECG PROCESSING / R-PEAK DETECTION\n');
fprintf('====================================================\n');

%% Take first complete 60-second baseline window

baseline_segment_start = baseline_start(1);

window_samples = Fs * 60;

window_end = ...
    baseline_segment_start + window_samples - 1;

if window_end > baseline_end(1)

    error('First baseline segment is shorter than 60 seconds.');

end

ecg_window = ...
    ecg(baseline_segment_start:window_end);

%% Process the window

result = process_ecg_window( ...
    ecg_window, Fs);

fprintf('60-second ECG window processed.\n');

fprintf('Detected R-peaks: %d\n', ...
    length(result.peak_locations));

fprintf('Mean HR: %.2f BPM\n', ...
    result.MeanHR);

fprintf('SDNN: %.2f ms\n', ...
    result.SDNN*1000);

fprintf('RMSSD: %.2f ms\n', ...
    result.RMSSD*1000);

fprintf('pNN50: %.2f %%\n', ...
    result.pNN50);

%% Plot filtered ECG and R-peaks

figure;

plot(result.filtered_ecg);

hold on;

plot( ...
    result.peak_locations, ...
    result.peak_values, ...
    'rv');

xlabel('Sample');

ylabel('Amplitude');

title('R-Peak Detection on 60-Second ECG Window');

legend('Filtered ECG','Detected R-peaks');

grid on;

%% =========================================================
% 6. LOAD FINAL FEATURE DATA
% ==========================================================

fprintf('\n');
fprintf('====================================================\n');
fprintf('4. HR / HRV FEATURE DATASET\n');
fprintf('====================================================\n');

results_folder = fullfile( ...
    project_root, ...
    '..', ...
    'results');

expanded_file = fullfile( ...
    results_folder, ...
    'WESAD_HRV_features_expanded.mat');

load(expanded_file);

fprintf('Feature windows: %d\n', ...
    height(HRV_Table));

fprintf('Features per window: %d\n', ...
    width(HRV_Table)-3);

fprintf('\nFeatures:\n');

feature_names = ...
    HRV_Table.Properties.VariableNames(4:end);

for i = 1:length(feature_names)

    fprintf('  %s\n', feature_names{i});

end

%% =========================================================
% 7. DISPLAY FEATURE COMPARISON
% ==========================================================

fprintf('\n');
fprintf('====================================================\n');
fprintf('5. BASELINE VS STRESS FEATURES\n');
fprintf('====================================================\n');

condition = string(HRV_Table.Condition);

baseline = condition == "Baseline";
stress = condition == "Stress";

fprintf('\nMean HR\n');
fprintf('Baseline: %.2f BPM\n', ...
    mean(HRV_Table.MeanHR(baseline)));

fprintf('Stress:   %.2f BPM\n', ...
    mean(HRV_Table.MeanHR(stress)));

fprintf('\nRMSSD\n');
fprintf('Baseline: %.2f ms\n', ...
    mean(HRV_Table.RMSSD(baseline))*1000);

fprintf('Stress:   %.2f ms\n', ...
    mean(HRV_Table.RMSSD(stress))*1000);

fprintf('\npNN50\n');
fprintf('Baseline: %.2f %%\n', ...
    mean(HRV_Table.pNN50(baseline)));

fprintf('Stress:   %.2f %%\n', ...
    mean(HRV_Table.pNN50(stress)));

%% =========================================================
% 8. SHOW FINAL MODEL RESULTS
% ==========================================================

fprintf('\n');
fprintf('====================================================\n');
fprintf('6. FINAL MODEL PERFORMANCE\n');
fprintf('====================================================\n');

metrics_file = fullfile( ...
    results_folder, ...
    'FINAL_Model_Metrics.csv');

metrics = readtable(metrics_file);

disp(metrics);

%% =========================================================
% 9. SHOW SUBJECT PERFORMANCE
% ==========================================================

fprintf('\n');
fprintf('====================================================\n');
fprintf('7. SUBJECT-WISE PERFORMANCE\n');
fprintf('====================================================\n');

subject_file = fullfile( ...
    results_folder, ...
    'FINAL_Subject_Stress_Performance.csv');

subject_results = readtable(subject_file);

disp(subject_results);

%% =========================================================
% 10. DISPLAY CONFUSION MATRIX
% ==========================================================

confusion_file = fullfile( ...
    results_folder, ...
    'figures', ...
    'FINAL_Confusion_Matrix.png');

if isfile(confusion_file)

    figure;

    img = imread(confusion_file);

    imshow(img);

    title('Final Stress Detector - Confusion Matrix');

end

%% =========================================================
% 11. DISPLAY ROC CURVE
% ==========================================================

roc_file = fullfile( ...
    results_folder, ...
    'figures', ...
    'FINAL_ROC_Curve.png');

if isfile(roc_file)

    figure;

    img = imread(roc_file);

    imshow(img);

    title('Final Stress Detector - ROC Curve');

end

%% =========================================================
% 12. FINAL SUMMARY
% ==========================================================

fprintf('\n');
fprintf('====================================================\n');
fprintf('FINAL PROJECT SUMMARY\n');
fprintf('====================================================\n');

fprintf('\nDataset:\n');
fprintf('  WESAD\n');

fprintf('  Subjects: 15\n');

fprintf('  Feature windows: 445\n');

fprintf('\nModel:\n');
fprintf('  Personalized baseline-relative features\n');
fprintf('  Logistic regression\n');
fprintf('  Leave-One-Subject-Out validation\n');

fprintf('\nFinal locked threshold:\n');
fprintf('  0.35\n');

fprintf('\nFinal performance:\n');
fprintf('  Accuracy          : 92.36 %%\n');
fprintf('  Precision         : 92.00 %%\n');
fprintf('  Recall            : 86.25 %%\n');
fprintf('  Specificity       : 95.79 %%\n');
fprintf('  F1-score          : 89.03 %%\n');
fprintf('  Balanced Accuracy : 91.02 %%\n');
fprintf('  ROC-AUC           : 0.9494\n');

fprintf('\nStress windows detected:\n');
fprintf('  138 / 160\n');

fprintf('\n====================================================\n');
fprintf('             DEMONSTRATION COMPLETE\n');
fprintf('====================================================\n');