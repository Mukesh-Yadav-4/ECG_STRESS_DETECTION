clear;
clc;
close all;

%% =========================================================
% SUBJECT FEATURE TRAJECTORY ANALYSIS
% ==========================================================

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
results_folder = fullfile(project_root,'results');

%% Load expanded feature dataset

load(fullfile( ...
    results_folder, ...
    'WESAD_HRV_features_expanded.mat'));

Subject = string(HRV_Table.Subject);
Condition = string(HRV_Table.Condition);

subjects_to_plot = {'S2','S9','S11','S14','S16'};

%% Features

feature_names = { ...
    'MeanHR', ...
    'RMSSD', ...
    'pNN50'};

%% Raw feature matrix

X = [ ...
    HRV_Table.MeanHR, ...
    HRV_Table.RMSSD * 1000, ...
    HRV_Table.pNN50];

%% =========================================================
% Plot each selected subject
% ==========================================================

for s = 1:length(subjects_to_plot)

    current_subject = subjects_to_plot{s};

    subject_mask = Subject == current_subject;

    baseline_mask = ...
        subject_mask & Condition == "Baseline";

    stress_mask = ...
        subject_mask & Condition == "Stress";

    %% Subject baseline

    baseline_mean = mean(X(baseline_mask,:),1);

    %% Relative values

    baseline_mean(abs(baseline_mean) < eps) = eps;

    stress_values = X(stress_mask,:);

    relative_stress = ...
        (stress_values - baseline_mean) ...
        ./ abs(baseline_mean) * 100;

    %% Print

    fprintf('\n========================================\n');
    fprintf('%s\n',current_subject);
    fprintf('========================================\n');

    fprintf('Mean HR baseline: %.2f BPM\n', ...
        baseline_mean(1));

    fprintf('Mean stress HR change: %.2f %%\n', ...
        mean(relative_stress(:,1)));

    fprintf('Mean stress RMSSD change: %.2f %%\n', ...
        mean(relative_stress(:,2)));

    fprintf('Mean stress pNN50 change: %.2f %%\n', ...
        mean(relative_stress(:,3)));

    %% Plot

    figure;

    plot( ...
        1:size(relative_stress,1), ...
        relative_stress(:,1), ...
        'o-');

    yline(0,'--');

    xlabel('Stress window');
    ylabel('Relative Mean HR change (%)');

    title([current_subject ...
        ' - Personalized HR Change During Stress']);

    grid on;

end