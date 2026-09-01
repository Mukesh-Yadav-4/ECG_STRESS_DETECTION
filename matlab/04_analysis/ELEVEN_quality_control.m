clear;
clc;
close all;

%% =========================================================
% WESAD HRV FEATURE QUALITY CONTROL
% ==========================================================

%% Project path

project_root = fileparts(fileparts(mfilename('fullpath')));

results_folder = fullfile(project_root, 'results');

%% Load master feature dataset

results_file = fullfile( ...
    results_folder, ...
    'WESAD_HRV_features.mat');

fprintf('Loading:\n%s\n\n', results_file);

if ~isfile(results_file)
    error('Feature file not found: %s', results_file);
end

load(results_file);

%% Basic information

fprintf('Total windows: %d\n', height(HRV_Table));

fprintf('\nFIRST 10 ROWS\n');
fprintf('=============\n');

disp(HRV_Table(1:min(10,height(HRV_Table)),:));

%% Check missing values

fprintf('\nMISSING VALUES\n');
fprintf('==============\n');

fprintf('MeanHR NaN: %d\n', sum(isnan(HRV_Table.MeanHR)));
fprintf('SDNN NaN : %d\n', sum(isnan(HRV_Table.SDNN)));
fprintf('RMSSD NaN: %d\n', sum(isnan(HRV_Table.RMSSD)));
fprintf('pNN50 NaN: %d\n', sum(isnan(HRV_Table.pNN50)));

%% Feature ranges

fprintf('\nFEATURE RANGES\n');
fprintf('==============\n');

fprintf('Mean HR : %.2f - %.2f BPM\n', ...
    min(HRV_Table.MeanHR), ...
    max(HRV_Table.MeanHR));

fprintf('SDNN    : %.2f - %.2f ms\n', ...
    min(HRV_Table.SDNN)*1000, ...
    max(HRV_Table.SDNN)*1000);

fprintf('RMSSD   : %.2f - %.2f ms\n', ...
    min(HRV_Table.RMSSD)*1000, ...
    max(HRV_Table.RMSSD)*1000);

fprintf('pNN50   : %.2f - %.2f %%\n', ...
    min(HRV_Table.pNN50), ...
    max(HRV_Table.pNN50));

%% Condition counts

fprintf('\nCONDITION COUNTS\n');
fprintf('================\n');

condition = string(HRV_Table.Condition);

baseline_count = sum(condition == "Baseline");
stress_count   = sum(condition == "Stress");

fprintf('Baseline windows: %d\n', baseline_count);
fprintf('Stress windows:   %d\n', stress_count);

%% Subject counts

subjects = unique(string(HRV_Table.Subject));

fprintf('\nSUBJECT COUNTS\n');
fprintf('==============\n');

for i = 1:length(subjects)

    subject = subjects(i);

    nBaseline = sum( ...
        string(HRV_Table.Subject) == subject & ...
        condition == "Baseline");

    nStress = sum( ...
        string(HRV_Table.Subject) == subject & ...
        condition == "Stress");

    fprintf('%s: Baseline = %d, Stress = %d\n', ...
        subject, nBaseline, nStress);

end