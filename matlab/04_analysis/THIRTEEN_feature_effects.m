clear;
clc;
close all;

%% =========================================================
% WESAD FEATURE EFFECT ANALYSIS
% ==========================================================

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
results_folder = fullfile(project_root, 'results');

%% Load results

load(fullfile(results_folder, 'Subject_Level_Statistics.mat'));

%% Extract changes

delta_HR = SubjectResults.DeltaHR;

delta_SDNN = SubjectResults.DeltaSDNN;

delta_RMSSD = SubjectResults.DeltaRMSSD;

delta_pNN50 = SubjectResults.DeltapNN50;

%% =========================================================
% Plot individual subject changes
% ==========================================================

figure;

plot(1:length(delta_HR), delta_HR, 'o-');
yline(0,'--');

xlabel('Subject');
ylabel('\Delta Mean HR (BPM)');
title('Subject-Level Stress Effect on Mean HR');

xticks(1:height(SubjectResults));
xticklabels(SubjectResults.Subject);

grid on;


figure;

plot(1:length(delta_SDNN), delta_SDNN, 'o-');
yline(0,'--');

xlabel('Subject');
ylabel('\Delta SDNN (ms)');
title('Subject-Level Stress Effect on SDNN');

xticks(1:height(SubjectResults));
xticklabels(SubjectResults.Subject);

grid on;


figure;

plot(1:length(delta_RMSSD), delta_RMSSD, 'o-');
yline(0,'--');

xlabel('Subject');
ylabel('\Delta RMSSD (ms)');
title('Subject-Level Stress Effect on RMSSD');

xticks(1:height(SubjectResults));
xticklabels(SubjectResults.Subject);

grid on;


figure;

plot(1:length(delta_pNN50), delta_pNN50, 'o-');
yline(0,'--');

xlabel('Subject');
ylabel('\Delta pNN50 (percentage points)');
title('Subject-Level Stress Effect on pNN50');

xticks(1:height(SubjectResults));
xticklabels(SubjectResults.Subject);

grid on;