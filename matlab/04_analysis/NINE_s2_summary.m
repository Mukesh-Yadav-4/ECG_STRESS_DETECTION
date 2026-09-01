clear;
clc;
close all;

%% S2 feature values from our current analysis

baseline_HR = [81.716 70.929 75.761 72.396 74.146];
stress_HR   = [83.253 79.534 77.945 83.716 74.948];

baseline_SDNN = [113.24 74.361 95.967 51.419 98.092];
stress_SDNN   = [73.625 73.358 78.651 91.105 114.10];

baseline_RMSSD = [75.44 52.618 87.27 53.83 92.787];
stress_RMSSD   = [67.307 47.263 34.785 92.325 77.099];

baseline_pNN50 = [26.58 31.88 43.24 38.03 36.11];
stress_pNN50   = [18.52 23.08 13.16 14.63 23.29];

%% Calculate averages

fprintf('\nS2 SUMMARY\n');
fprintf('============================\n');

fprintf('\nMean HR:\n');
fprintf('Baseline = %.2f BPM\n', mean(baseline_HR));
fprintf('Stress   = %.2f BPM\n', mean(stress_HR));

fprintf('\nSDNN:\n');
fprintf('Baseline = %.2f ms\n', mean(baseline_SDNN));
fprintf('Stress   = %.2f ms\n', mean(stress_SDNN));

fprintf('\nRMSSD:\n');
fprintf('Baseline = %.2f ms\n', mean(baseline_RMSSD));
fprintf('Stress   = %.2f ms\n', mean(stress_RMSSD));

fprintf('\npNN50:\n');
fprintf('Baseline = %.2f %%\n', mean(baseline_pNN50));
fprintf('Stress   = %.2f %%\n', mean(stress_pNN50));

%% Percentage change

fprintf('\nPERCENTAGE CHANGE\n');
fprintf('============================\n');

fprintf('Mean HR: %.2f %%\n', ...
    100*(mean(stress_HR)-mean(baseline_HR))/mean(baseline_HR));

fprintf('SDNN: %.2f %%\n', ...
    100*(mean(stress_SDNN)-mean(baseline_SDNN))/mean(baseline_SDNN));

fprintf('RMSSD: %.2f %%\n', ...
    100*(mean(stress_RMSSD)-mean(baseline_RMSSD))/mean(baseline_RMSSD));

fprintf('pNN50: %.2f %%\n', ...
    100*(mean(stress_pNN50)-mean(baseline_pNN50))/mean(baseline_pNN50));