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
% Make sure vectors are columns
ecg = ecg(:);
labels = labels(:);

Fs = double(Fs);

%% Labels of interest
BASELINE = 1;
STRESS = 2;

%% Find continuous baseline segments
baseline_mask = (labels == BASELINE);

baseline_start = find(diff([false; baseline_mask]) == 1);
baseline_end   = find(diff([baseline_mask; false]) == -1);

%% Find continuous stress segments
stress_mask = (labels == STRESS);

stress_start = find(diff([false; stress_mask]) == 1);
stress_end   = find(diff([stress_mask; false]) == -1);

%% Display results

fprintf('\nBASELINE SEGMENTS\n');
fprintf('-----------------\n');

for i = 1:length(baseline_start)

    start_time = (baseline_start(i)-1) / Fs;
    end_time   = (baseline_end(i)-1) / Fs;
    duration   = end_time - start_time;

    fprintf('Segment %d: %.2f - %.2f min | Duration: %.2f min\n', ...
        i, start_time/60, end_time/60, duration/60);
end

fprintf('\nSTRESS SEGMENTS\n');
fprintf('---------------\n');

for i = 1:length(stress_start)

    start_time = (stress_start(i)-1) / Fs;
    end_time   = (stress_end(i)-1) / Fs;
    duration   = end_time - start_time;

    fprintf('Segment %d: %.2f - %.2f min | Duration: %.2f min\n', ...
        i, start_time/60, end_time/60, duration/60);
end