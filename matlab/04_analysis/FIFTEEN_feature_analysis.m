clear;
clc;
close all;

%% =========================================================
% WESAD FEATURE ANALYSIS
% ==========================================================

%% Project paths

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
results_folder = fullfile(project_root, 'results');

%% Load feature dataset

load(fullfile(results_folder, 'WESAD_HRV_features.mat'));

%% Convert condition

condition = string(HRV_Table.Condition);

baseline = condition == "Baseline";
stress   = condition == "Stress";

%% Extract features

HR = HRV_Table.MeanHR;
SDNN = HRV_Table.SDNN * 1000;      % seconds -> ms
RMSSD = HRV_Table.RMSSD * 1000;   % seconds -> ms
pNN50 = HRV_Table.pNN50;

feature_names = {'Mean HR','SDNN','RMSSD','pNN50'};

%% =========================================================
% BASIC FEATURE SUMMARY
% ==========================================================

fprintf('\n============================================\n');
fprintf('FEATURE ANALYSIS\n');
fprintf('============================================\n');

fprintf('\n');

fprintf('Mean HR\n');
fprintf('  Baseline: %.2f ± %.2f BPM\n', ...
    mean(HR(baseline)), std(HR(baseline)));
fprintf('  Stress:   %.2f ± %.2f BPM\n', ...
    mean(HR(stress)), std(HR(stress)));

fprintf('\nSDNN\n');
fprintf('  Baseline: %.2f ± %.2f ms\n', ...
    mean(SDNN(baseline)), std(SDNN(baseline)));
fprintf('  Stress:   %.2f ± %.2f ms\n', ...
    mean(SDNN(stress)), std(SDNN(stress)));

fprintf('\nRMSSD\n');
fprintf('  Baseline: %.2f ± %.2f ms\n', ...
    mean(RMSSD(baseline)), std(RMSSD(baseline)));
fprintf('  Stress:   %.2f ± %.2f ms\n', ...
    mean(RMSSD(stress)), std(RMSSD(stress)));

fprintf('\npNN50\n');
fprintf('  Baseline: %.2f ± %.2f %%\n', ...
    mean(pNN50(baseline)), std(pNN50(baseline)));
fprintf('  Stress:   %.2f ± %.2f %%\n', ...
    mean(pNN50(stress)), std(pNN50(stress)));

%% =========================================================
% HISTOGRAMS
% ==========================================================

figure;

histogram(HR(baseline),20);
hold on;
histogram(HR(stress),20);

xlabel('Mean HR (BPM)');
ylabel('Number of windows');
title('Mean HR: Baseline vs Stress');

legend('Baseline','Stress');
grid on;


figure;

histogram(SDNN(baseline),20);
hold on;
histogram(SDNN(stress),20);

xlabel('SDNN (ms)');
ylabel('Number of windows');
title('SDNN: Baseline vs Stress');

legend('Baseline','Stress');
grid on;


figure;

histogram(RMSSD(baseline),20);
hold on;
histogram(RMSSD(stress),20);

xlabel('RMSSD (ms)');
ylabel('Number of windows');
title('RMSSD: Baseline vs Stress');

legend('Baseline','Stress');
grid on;


figure;

histogram(pNN50(baseline),20);
hold on;
histogram(pNN50(stress),20);

xlabel('pNN50 (%)');
ylabel('Number of windows');
title('pNN50: Baseline vs Stress');

legend('Baseline','Stress');
grid on;

%% =========================================================
% FEATURE CORRELATIONS
% ==========================================================

X = [HR SDNN RMSSD pNN50];

R = corrcoef(X);

fprintf('\n============================================\n');
fprintf('FEATURE CORRELATION MATRIX\n');
fprintf('============================================\n');

disp(array2table(R, ...
    'VariableNames', feature_names, ...
    'RowNames', feature_names));

%% =========================================================
% STANDARDIZED BASELINE/STRESS SEPARATION
% ==========================================================

features = {HR, SDNN, RMSSD, pNN50};

fprintf('\n============================================\n');
fprintf('STANDARDIZED FEATURE EFFECTS\n');
fprintf('============================================\n');

for i = 1:length(features)

    x = features{i};

    baseline_values = x(baseline);
    stress_values = x(stress);

    mean_B = mean(baseline_values);
    mean_S = mean(stress_values);

    pooled_SD = sqrt( ...
        ((length(baseline_values)-1)*var(baseline_values) + ...
         (length(stress_values)-1)*var(stress_values)) ...
        / ...
        (length(baseline_values)+length(stress_values)-2));

    d = (mean_S - mean_B) / pooled_SD;

    fprintf('%s: Cohen''s d = %.3f\n', ...
        feature_names{i}, d);

end

%% =========================================================
% SIMPLE THRESHOLD ANALYSIS
% ==========================================================

fprintf('\n============================================\n');
fprintf('SIMPLE THRESHOLD ANALYSIS\n');
fprintf('============================================\n');

% Mean HR threshold
threshold_HR = (mean(HR(baseline)) + mean(HR(stress))) / 2;

prediction_HR = HR > threshold_HR;

accuracy_HR = mean( ...
    (prediction_HR == stress));

fprintf('\nMean HR threshold = %.2f BPM\n', threshold_HR);
fprintf('Window-level accuracy = %.2f %%\n', ...
    accuracy_HR*100);

%% pNN50 threshold

threshold_pNN50 = ...
    (mean(pNN50(baseline)) + mean(pNN50(stress))) / 2;

prediction_pNN50 = pNN50 < threshold_pNN50;

accuracy_pNN50 = mean( ...
    (prediction_pNN50 == stress));

fprintf('\npNN50 threshold = %.2f %%\n', threshold_pNN50);
fprintf('Window-level accuracy = %.2f %%\n', ...
    accuracy_pNN50*100);

%% =========================================================
% Save feature analysis results
% ==========================================================

FeatureResults = table( ...
    feature_names(:), ...
    'VariableNames', {'Feature'});

save( ...
    fullfile(results_folder, ...
    'Feature_Analysis.mat'), ...
    'R');

fprintf('\nFeature analysis complete.\n');