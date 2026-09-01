clear;
clc;
close all;

%% =========================================================
% WESAD SUBJECT-LEVEL STATISTICAL TESTS
% No Statistics Toolbox required
% ==========================================================

%% Project paths

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
results_folder = fullfile(project_root, 'results');

%% Load subject-level results

load(fullfile(results_folder, ...
    'Subject_Level_Statistics.mat'));

%% Extract paired observations

baseline_HR = SubjectResults.BaselineHR;
stress_HR   = SubjectResults.StressHR;

baseline_SDNN = SubjectResults.BaselineSDNN;
stress_SDNN   = SubjectResults.StressSDNN;

baseline_RMSSD = SubjectResults.BaselineRMSSD;
stress_RMSSD   = SubjectResults.StressRMSSD;

baseline_pNN50 = SubjectResults.BaselinepNN50;
stress_pNN50   = SubjectResults.StresspNN50;

%% Differences

delta_HR = stress_HR - baseline_HR;
delta_SDNN = stress_SDNN - baseline_SDNN;
delta_RMSSD = stress_RMSSD - baseline_RMSSD;
delta_pNN50 = stress_pNN50 - baseline_pNN50;

%% =========================================================
% Two-tailed paired t-test via one-sample differences
% ==========================================================

features = { ...
    'Mean HR', ...
    'SDNN', ...
    'RMSSD', ...
    'pNN50'};

deltas = { ...
    delta_HR, ...
    delta_SDNN, ...
    delta_RMSSD, ...
    delta_pNN50};

alpha = 0.05;

fprintf('\n============================================\n');
fprintf('PAIRED STATISTICAL TESTS\n');
fprintf('============================================\n');

for i = 1:length(features)

    d = deltas{i};

    n = length(d);
    df = n - 1;

    mean_d = mean(d);
    sd_d = std(d);

    % t-statistic
    t_stat = mean_d / (sd_d / sqrt(n));

    % -----------------------------------------------------
    % Two-tailed p-value
    %
    % For t with v degrees of freedom:
    %
    % p = I_(v/(v+t^2))(v/2, 1/2)
    % -----------------------------------------------------

    x = df / (df + t_stat^2);

    p_value = betainc(x, df/2, 0.5);

    fprintf('\n%s\n', features{i});
    fprintf('Mean difference = %.4f\n', mean_d);
    fprintf('SD difference   = %.4f\n', sd_d);
    fprintf('t(%d)            = %.4f\n', df, t_stat);
    fprintf('p-value         = %.6f\n', p_value);

    if p_value < alpha
        fprintf('Result          = SIGNIFICANT\n');
    else
        fprintf('Result          = NOT SIGNIFICANT\n');
    end

end

%% =========================================================
% Percentage change
% ==========================================================

fprintf('\n============================================\n');
fprintf('PERCENT CHANGE\n');
fprintf('============================================\n');

fprintf('Mean HR  : %.2f %%\n', ...
    100 * mean(delta_HR) / mean(baseline_HR));

fprintf('SDNN     : %.2f %%\n', ...
    100 * mean(delta_SDNN) / mean(baseline_SDNN));

fprintf('RMSSD    : %.2f %%\n', ...
    100 * mean(delta_RMSSD) / mean(baseline_RMSSD));

fprintf('pNN50    : %.2f %%\n', ...
    100 * mean(delta_pNN50) / mean(baseline_pNN50));