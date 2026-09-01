clear;
clc;
close all;

%% Project paths

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));

results_folder = fullfile(project_root, 'results');

%% Load feature dataset

load(fullfile(results_folder, 'WESAD_HRV_features.mat'));

%% Convert conditions to strings

condition = string(HRV_Table.Condition);

baseline = condition == "Baseline";
stress   = condition == "Stress";

%% Convert HRV units for plotting

MeanHR = HRV_Table.MeanHR;
SDNN_ms = HRV_Table.SDNN * 1000;
RMSSD_ms = HRV_Table.RMSSD * 1000;
pNN50 = HRV_Table.pNN50;

%% Summary

fprintf('\nDATASET SUMMARY\n');
fprintf('================\n');

fprintf('Total windows : %d\n', height(HRV_Table));
fprintf('Baseline      : %d\n', sum(baseline));
fprintf('Stress        : %d\n', sum(stress));

%% ---------------------------------------------------------
% Mean HR distributions
% ----------------------------------------------------------

figure;

histogram(MeanHR(baseline), 20);
hold on;
histogram(MeanHR(stress), 20);

xlabel('Mean Heart Rate (BPM)');
ylabel('Number of Windows');

title('Mean HR Distribution');

legend('Baseline', 'Stress');

grid on;

%% ---------------------------------------------------------
% SDNN distributions
% ----------------------------------------------------------

figure;

histogram(SDNN_ms(baseline), 20);
hold on;
histogram(SDNN_ms(stress), 20);

xlabel('SDNN (ms)');
ylabel('Number of Windows');

title('SDNN Distribution');

legend('Baseline', 'Stress');

grid on;

%% ---------------------------------------------------------
% RMSSD distributions
% ----------------------------------------------------------

figure;

histogram(RMSSD_ms(baseline), 20);
hold on;
histogram(RMSSD_ms(stress), 20);

xlabel('RMSSD (ms)');
ylabel('Number of Windows');

title('RMSSD Distribution');

legend('Baseline', 'Stress');

grid on;

%% ---------------------------------------------------------
% pNN50 distributions
% ----------------------------------------------------------

figure;

histogram(pNN50(baseline), 20);
hold on;
histogram(pNN50(stress), 20);

xlabel('pNN50 (%)');
ylabel('Number of Windows');

title('pNN50 Distribution');

legend('Baseline', 'Stress');

grid on;

%% Mean HR by subject and condition

subjects = unique(string(HRV_Table.Subject));

baseline_subject_mean = zeros(length(subjects),1);
stress_subject_mean = zeros(length(subjects),1);

for i = 1:length(subjects)

    idx_baseline = ...
        string(HRV_Table.Subject) == subjects(i) & ...
        baseline;

    idx_stress = ...
        string(HRV_Table.Subject) == subjects(i) & ...
        stress;

    baseline_subject_mean(i) = mean(MeanHR(idx_baseline));
    stress_subject_mean(i) = mean(MeanHR(idx_stress));

end

figure;

plot(1:length(subjects), ...
    baseline_subject_mean, ...
    'o-');

hold on;

plot(1:length(subjects), ...
    stress_subject_mean, ...
    'o-');

xlabel('Subject');
ylabel('Mean HR (BPM)');

title('Subject-Level Mean HR: Baseline vs Stress');

xticks(1:length(subjects));
xticklabels(subjects);

legend('Baseline','Stress');

grid on;