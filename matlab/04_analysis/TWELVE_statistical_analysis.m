clear;
clc;
close all;

%% =========================================================
% WESAD SUBJECT-LEVEL STATISTICAL ANALYSIS
% ==========================================================

%% Project paths

project_root = fileparts(fileparts(mfilename('fullpath')));
results_folder = fullfile(project_root, 'results');

%% Load feature dataset

feature_file = fullfile( ...
    results_folder, ...
    'WESAD_HRV_features.mat');

load(feature_file);

%% Convert columns

subject = string(HRV_Table.Subject);
condition = string(HRV_Table.Condition);

subjects = unique(subject);
nSubjects = length(subjects);

%% =========================================================
% SUBJECT-LEVEL MEANS
% ==========================================================

baseline_HR = zeros(nSubjects,1);
stress_HR   = zeros(nSubjects,1);

baseline_SDNN = zeros(nSubjects,1);
stress_SDNN   = zeros(nSubjects,1);

baseline_RMSSD = zeros(nSubjects,1);
stress_RMSSD   = zeros(nSubjects,1);

baseline_pNN50 = zeros(nSubjects,1);
stress_pNN50   = zeros(nSubjects,1);

for i = 1:nSubjects

    s = subjects(i);

    idxB = subject == s & condition == "Baseline";
    idxS = subject == s & condition == "Stress";

    baseline_HR(i) = mean(HRV_Table.MeanHR(idxB));
    stress_HR(i)   = mean(HRV_Table.MeanHR(idxS));

    baseline_SDNN(i) = mean(HRV_Table.SDNN(idxB)) * 1000;
    stress_SDNN(i)   = mean(HRV_Table.SDNN(idxS)) * 1000;

    baseline_RMSSD(i) = mean(HRV_Table.RMSSD(idxB)) * 1000;
    stress_RMSSD(i)   = mean(HRV_Table.RMSSD(idxS)) * 1000;

    baseline_pNN50(i) = mean(HRV_Table.pNN50(idxB));
    stress_pNN50(i)   = mean(HRV_Table.pNN50(idxS));

end

%% =========================================================
% DIFFERENCES
% ==========================================================

delta_HR = stress_HR - baseline_HR;

delta_SDNN = stress_SDNN - baseline_SDNN;

delta_RMSSD = stress_RMSSD - baseline_RMSSD;

delta_pNN50 = stress_pNN50 - baseline_pNN50;

%% =========================================================
% SUMMARY STATISTICS
% ==========================================================

fprintf('\n============================================\n');
fprintf('SUBJECT-LEVEL STATISTICAL ANALYSIS\n');
fprintf('============================================\n');

fprintf('\nNumber of subjects: %d\n', nSubjects);

%% HR

fprintf('\nMEAN HEART RATE\n');
fprintf('Baseline mean = %.2f BPM\n', mean(baseline_HR));
fprintf('Stress mean   = %.2f BPM\n', mean(stress_HR));
fprintf('Mean change   = %.2f BPM\n', mean(delta_HR));
fprintf('SD of change  = %.2f BPM\n', std(delta_HR));

%% SDNN

fprintf('\nSDNN\n');
fprintf('Baseline mean = %.2f ms\n', mean(baseline_SDNN));
fprintf('Stress mean   = %.2f ms\n', mean(stress_SDNN));
fprintf('Mean change   = %.2f ms\n', mean(delta_SDNN));
fprintf('SD of change  = %.2f ms\n', std(delta_SDNN));

%% RMSSD

fprintf('\nRMSSD\n');
fprintf('Baseline mean = %.2f ms\n', mean(baseline_RMSSD));
fprintf('Stress mean   = %.2f ms\n', mean(stress_RMSSD));
fprintf('Mean change   = %.2f ms\n', mean(delta_RMSSD));
fprintf('SD of change  = %.2f ms\n', std(delta_RMSSD));

%% pNN50

fprintf('\npNN50\n');
fprintf('Baseline mean = %.2f %%\n', mean(baseline_pNN50));
fprintf('Stress mean   = %.2f %%\n', mean(stress_pNN50));
fprintf('Mean change   = %.2f percentage points\n', ...
    mean(delta_pNN50));
fprintf('SD of change  = %.2f percentage points\n', ...
    std(delta_pNN50));

%% =========================================================
% DIRECTION OF CHANGE
% ==========================================================

fprintf('\nDIRECTION OF CHANGE\n');
fprintf('===================\n');

fprintf('HR increased   : %d / %d\n', ...
    sum(delta_HR > 0), nSubjects);

fprintf('SDNN decreased : %d / %d\n', ...
    sum(delta_SDNN < 0), nSubjects);

fprintf('RMSSD decreased: %d / %d\n', ...
    sum(delta_RMSSD < 0), nSubjects);

fprintf('pNN50 decreased: %d / %d\n', ...
    sum(delta_pNN50 < 0), nSubjects);

%% =========================================================
% STANDARDIZED EFFECT SIZE
% Paired Cohen's dz = mean(delta) / std(delta)
% ==========================================================

dz_HR = mean(delta_HR) / std(delta_HR);

dz_SDNN = mean(delta_SDNN) / std(delta_SDNN);

dz_RMSSD = mean(delta_RMSSD) / std(delta_RMSSD);

dz_pNN50 = mean(delta_pNN50) / std(delta_pNN50);

fprintf('\nPAIRED EFFECT SIZES (Cohen''s dz)\n');
fprintf('===================================\n');

fprintf('HR     : %.3f\n', dz_HR);
fprintf('SDNN   : %.3f\n', dz_SDNN);
fprintf('RMSSD  : %.3f\n', dz_RMSSD);
fprintf('pNN50  : %.3f\n', dz_pNN50);

%% =========================================================
% 95%% BOOTSTRAP CONFIDENCE INTERVAL
% ==========================================================

rng(1);

B = 10000;

feature_names = {'HR','SDNN','RMSSD','pNN50'};

deltas = { ...
    delta_HR, ...
    delta_SDNN, ...
    delta_RMSSD, ...
    delta_pNN50};

fprintf('\nBOOTSTRAP 95%% CONFIDENCE INTERVALS\n');
fprintf('===================================\n');

for f = 1:length(deltas)

    d = deltas{f};

    bootstrap_means = zeros(B,1);

    for b = 1:B

        sample_idx = randi(nSubjects,nSubjects,1);

        bootstrap_means(b) = ...
            mean(d(sample_idx));

    end

    CI = prctile(bootstrap_means,[2.5 97.5]);

    fprintf('%s: %.3f to %.3f\n', ...
        feature_names{f}, ...
        CI(1), CI(2));

end

%% =========================================================
% PLOT SUBJECT-LEVEL CHANGES
% ==========================================================

figure;

plot(1:nSubjects, delta_HR, 'o-');

yline(0,'--');

xlabel('Subject');
ylabel('\Delta HR (BPM)');

title('Subject-Level Change in Heart Rate');

xticks(1:nSubjects);
xticklabels(subjects);

grid on;

%% RMSSD change

figure;

plot(1:nSubjects, delta_RMSSD, 'o-');

yline(0,'--');

xlabel('Subject');
ylabel('\Delta RMSSD (ms)');

title('Subject-Level Change in RMSSD');

xticks(1:nSubjects);
xticklabels(subjects);

grid on;

%% pNN50 change

figure;

plot(1:nSubjects, delta_pNN50, 'o-');

yline(0,'--');

xlabel('Subject');
ylabel('\Delta pNN50 (percentage points)');

title('Subject-Level Change in pNN50');

xticks(1:nSubjects);
xticklabels(subjects);

grid on;

%% =========================================================
% SAVE SUBJECT-LEVEL RESULTS
% ==========================================================

SubjectResults = table( ...
    subjects, ...
    baseline_HR, stress_HR, delta_HR, ...
    baseline_SDNN, stress_SDNN, delta_SDNN, ...
    baseline_RMSSD, stress_RMSSD, delta_RMSSD, ...
    baseline_pNN50, stress_pNN50, delta_pNN50, ...
    'VariableNames', { ...
    'Subject', ...
    'BaselineHR', ...
    'StressHR', ...
    'DeltaHR', ...
    'BaselineSDNN', ...
    'StressSDNN', ...
    'DeltaSDNN', ...
    'BaselineRMSSD', ...
    'StressRMSSD', ...
    'DeltaRMSSD', ...
    'BaselinepNN50', ...
    'StresspNN50', ...
    'DeltapNN50'});

writetable( ...
    SubjectResults, ...
    fullfile(results_folder, ...
    'Subject_Level_Statistics.csv'));

save( ...
    fullfile(results_folder, ...
    'Subject_Level_Statistics.mat'), ...
    'SubjectResults');

fprintf('\nResults saved successfully.\n');