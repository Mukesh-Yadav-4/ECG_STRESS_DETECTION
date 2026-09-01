clear;
clc;
close all;

%% =========================================================
% WESAD MULTI-SUBJECT ECG FEATURE EXTRACTION
%
% Input:
%   data/processed/S*_ECG_labels.mat
%
% Output:
%   results/WESAD_HRV_features_expanded.csv
%   results/WESAD_HRV_features_expanded.mat
%
% Conditions:
%   Label 1 = Baseline
%   Label 2 = Stress
%
% Window:
%   60 seconds
% ==========================================================

%% =========================================================
%% =========================================================
% PROJECT PATHS
% ==========================================================

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));

data_folder = fullfile( ...
    project_root, ...
    'data', ...
    'processed');

results_folder = fullfile( ...
    project_root, ...
    'results');

if ~exist(results_folder, 'dir')
    mkdir(results_folder);
end

%% =========================================================
% 2. SUBJECT LIST
% ==========================================================

subjects = { ...
    'S2', ...
    'S3', ...
    'S4', ...
    'S5', ...
    'S6', ...
    'S7', ...
    'S8', ...
    'S9', ...
    'S10', ...
    'S11', ...
    'S13', ...
    'S14', ...
    'S15', ...
    'S16', ...
    'S17'};

%% =========================================================
% 3. ECG SETTINGS
% ==========================================================

Fs = 700;                  % WESAD chest ECG sampling rate
window_duration = 60;      % seconds
samples_per_window = Fs * window_duration;

BASELINE = 1;
STRESS = 2;

%% =========================================================
% 4. CHECK PROCESSING FUNCTION
% ==========================================================

if exist('process_ecg_window', 'file') ~= 2
    error(['process_ecg_window.m was not found on the MATLAB path. ', ...
           'Make sure the functions folder/file is available.']);
end

%% =========================================================
% 5. RESULTS STORAGE
% ==========================================================

all_results = cell(0, 16);

result_row = 1;

%% =========================================================
% 6. PROCESS EACH SUBJECT
% ==========================================================

for s = 1:length(subjects)

    subject = subjects{s};

    fprintf('\n========================================\n');
    fprintf('Processing %s\n', subject);
    fprintf('========================================\n');

    %% -----------------------------------------------------
    % Load subject data
    % ------------------------------------------------------

    filename = fullfile( ...
        data_folder, ...
        [subject '_ECG_labels.mat']);

    if ~isfile(filename)

        fprintf('WARNING: File not found:\n%s\n', filename);
        continue;

    end

    load(filename);

    %% -----------------------------------------------------
    % Convert to column vectors
    % ------------------------------------------------------

    ecg = double(ecg(:));
    labels = double(labels(:));

    %% -----------------------------------------------------
    % Safety check
    % ------------------------------------------------------

    if length(ecg) ~= length(labels)

        fprintf('ERROR: ECG and labels length mismatch.\n');
        fprintf('ECG: %d samples\n', length(ecg));
        fprintf('Labels: %d samples\n', length(labels));

        continue;

    end

    fprintf('Samples: %d\n', length(ecg));
    fprintf('Duration: %.2f minutes\n', ...
        length(ecg) / Fs / 60);

    %% =====================================================
    % FIND BASELINE SEGMENTS
    % ======================================================

    baseline_mask = labels == BASELINE;

    baseline_start = ...
        find(diff([false; baseline_mask]) == 1);

    baseline_end = ...
        find(diff([baseline_mask; false]) == -1);

    %% =====================================================
    % FIND STRESS SEGMENTS
    % ======================================================

    stress_mask = labels == STRESS;

    stress_start = ...
        find(diff([false; stress_mask]) == 1);

    stress_end = ...
        find(diff([stress_mask; false]) == -1);

    fprintf('Baseline segments: %d\n', ...
        length(baseline_start));

    fprintf('Stress segments:   %d\n', ...
        length(stress_start));

    %% =====================================================
    % PROCESS BASELINE
    % ======================================================

    for seg = 1:length(baseline_start)

        segment_start = baseline_start(seg);
        segment_end = baseline_end(seg);

        segment_length = ...
            segment_end - segment_start + 1;

        number_of_windows = ...
            floor(segment_length / samples_per_window);

        fprintf('Baseline segment %d: %d windows\n', ...
            seg, number_of_windows);

        for w = 1:number_of_windows

            %% Window indices

            start_idx = ...
                segment_start + ...
                (w - 1) * samples_per_window;

            end_idx = ...
                start_idx + ...
                samples_per_window - 1;

            %% Extract ECG

            ecg_window = ecg(start_idx:end_idx);

            %% Process ECG

            result = process_ecg_window( ...
                ecg_window, Fs);

            %% Store features

            all_results(result_row,:) = { ...
                subject, ...
                'Baseline', ...
                w, ...
                result.MeanHR, ...
                result.MedianHR, ...
                result.StdHR, ...
                result.MinHR, ...
                result.MaxHR, ...
                result.MeanRR, ...
                result.MedianRR, ...
                result.SDNN, ...
                result.RMSSD, ...
                result.pNN50, ...
                result.RR_CV, ...
                result.RR_IQR, ...
                result.HR_IQR};

            result_row = result_row + 1;

        end

    end

    %% =====================================================
    % PROCESS STRESS
    % ======================================================

    for seg = 1:length(stress_start)

        segment_start = stress_start(seg);
        segment_end = stress_end(seg);

        segment_length = ...
            segment_end - segment_start + 1;

        number_of_windows = ...
            floor(segment_length / samples_per_window);

        fprintf('Stress segment %d: %d windows\n', ...
            seg, number_of_windows);

        for w = 1:number_of_windows

            %% Window indices

            start_idx = ...
                segment_start + ...
                (w - 1) * samples_per_window;

            end_idx = ...
                start_idx + ...
                samples_per_window - 1;

            %% Extract ECG

            ecg_window = ecg(start_idx:end_idx);

            %% Process ECG

            result = process_ecg_window( ...
                ecg_window, Fs);

            %% Store features

            all_results(result_row,:) = { ...
                subject, ...
                'Stress', ...
                w, ...
                result.MeanHR, ...
                result.MedianHR, ...
                result.StdHR, ...
                result.MinHR, ...
                result.MaxHR, ...
                result.MeanRR, ...
                result.MedianRR, ...
                result.SDNN, ...
                result.RMSSD, ...
                result.pNN50, ...
                result.RR_CV, ...
                result.RR_IQR, ...
                result.HR_IQR};

            result_row = result_row + 1;

        end

    end

    %% Free subject variables before next subject

    clear ecg labels

end

%% =========================================================
% 7. CREATE FINAL FEATURE TABLE
% ==========================================================

HRV_Table = cell2table( ...
    all_results, ...
    'VariableNames', { ...
    'Subject', ...
    'Condition', ...
    'Window', ...
    'MeanHR', ...
    'MedianHR', ...
    'StdHR', ...
    'MinHR', ...
    'MaxHR', ...
    'MeanRR', ...
    'MedianRR', ...
    'SDNN', ...
    'RMSSD', ...
    'pNN50', ...
    'RR_CV', ...
    'RR_IQR', ...
    'HR_IQR'});

%% =========================================================
% 8. BASIC OUTPUT
% ==========================================================

fprintf('\n========================================\n');
fprintf('PROCESSING COMPLETE\n');
fprintf('========================================\n');

fprintf('Total windows: %d\n', ...
    height(HRV_Table));

fprintf('Total features per window: %d\n', ...
    width(HRV_Table) - 3);

%% Display first rows

fprintf('\nFIRST 20 ROWS\n');
fprintf('=============\n');

disp(HRV_Table( ...
    1:min(20,height(HRV_Table)), :));

%% =========================================================
% 9. CHECK FOR MISSING VALUES
% ==========================================================

fprintf('\n========================================\n');
fprintf('MISSING VALUE CHECK\n');
fprintf('========================================\n');

numeric_data = HRV_Table{:,4:end};

nan_count = sum(isnan(numeric_data), 1);

feature_names = HRV_Table.Properties.VariableNames(4:end);

for i = 1:length(feature_names)

    fprintf('%s: %d NaN\n', ...
        feature_names{i}, ...
        nan_count(i));

end

%% =========================================================
% 10. SAVE EXPANDED DATASET
% ==========================================================

expanded_csv = fullfile( ...
    results_folder, ...
    'WESAD_HRV_features_expanded.csv');

expanded_mat = fullfile( ...
    results_folder, ...
    'WESAD_HRV_features_expanded.mat');

writetable( ...
    HRV_Table, ...
    expanded_csv);

save( ...
    expanded_mat, ...
    'HRV_Table');

%% =========================================================
% 11. FINAL CONFIRMATION
% ==========================================================

fprintf('\n========================================\n');
fprintf('EXPANDED RESULTS SAVED\n');
fprintf('========================================\n');

fprintf('%s\n', expanded_csv);
fprintf('%s\n', expanded_mat);

fprintf('\nFile existence check:\n');

fprintf('CSV: %d\n', isfile(expanded_csv));
fprintf('MAT: %d\n', isfile(expanded_mat));