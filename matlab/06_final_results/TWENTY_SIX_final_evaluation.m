clear;
clc;
close all;

%% =========================================================
% FINAL WESAD ECG STRESS DETECTION EVALUATION
%
% Locked development configuration:
%
%   Dataset       : WESAD
%   Subjects      : 15
%   Window        : 60 seconds
%   Features      : Personalized HR/HRV
%   Classifier    : Logistic regression
%   Validation    : Leave-One-Subject-Out
%   Threshold     : 0.35
%
% IMPORTANT:
% Each held-out subject is calibrated using their baseline
% recording before stress detection.
% ==========================================================

%% =========================================================
% 1. PROJECT PATHS
% ==========================================================

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));

results_folder = fullfile(project_root, 'results');

%% =========================================================
% 2. LOAD DATA
% ==========================================================

feature_file = fullfile( ...
    results_folder, ...
    'WESAD_HRV_features_expanded.mat');

if ~isfile(feature_file)
    error('Feature file not found:\n%s', feature_file);
end

load(feature_file);

%% =========================================================
% 3. DATA
% ==========================================================

Subject = string(HRV_Table.Subject);
Condition = string(HRV_Table.Condition);

subjects = unique(Subject);

nSubjects = length(subjects);

%% Binary target

% Baseline = 0
% Stress   = 1

y = double(Condition == "Stress");

%% =========================================================
% 4. PERSONALIZED FEATURE MATRIX
% ==========================================================

% Selected features:
%
% 1 = MeanHR
% 2 = SDNN
% 3 = RMSSD
% 4 = pNN50
% 5 = MeanRR
% 6 = RR_CV
% 7 = RR_IQR
% 8 = HR_IQR

X = [ ...
    HRV_Table.MeanHR, ...
    HRV_Table.SDNN * 1000, ...
    HRV_Table.RMSSD * 1000, ...
    HRV_Table.pNN50, ...
    HRV_Table.MeanRR * 1000, ...
    HRV_Table.RR_CV, ...
    HRV_Table.RR_IQR * 1000, ...
    HRV_Table.HR_IQR];

%% =========================================================
% 5. LOCKED PARAMETERS
% ==========================================================

threshold = 0.35;

learning_rate = 0.05;

iterations = 3000;

%% =========================================================
% 6. STORAGE
% ==========================================================

all_true = [];
all_pred = [];
all_prob = [];

all_subject = strings(0,1);

%% =========================================================
% 7. LEAVE-ONE-SUBJECT-OUT
% ==========================================================

for s = 1:nSubjects

    test_subject = subjects(s);

    fprintf('\n============================================\n');
    fprintf('FINAL EVALUATION: %s\n', test_subject);
    fprintf('============================================\n');

    %% -----------------------------------------------------
    % Train/test split
    % ------------------------------------------------------

    train_mask = Subject ~= test_subject;

    test_mask = Subject == test_subject;

    X_train_raw = X(train_mask,:);
    X_test_raw = X(test_mask,:);

    y_train = y(train_mask);

    test_condition = Condition(test_mask);

    %% =====================================================
    % PERSONALIZED TRAINING FEATURES
    % ======================================================

    train_subjects = unique(Subject(train_mask));

    X_train_personalized = zeros(size(X_train_raw));

    for j = 1:length(train_subjects)

        current_subject = train_subjects(j);

        subject_mask = ...
            Subject(train_mask) == current_subject;

        baseline_mask = ...
            subject_mask & ...
            Condition(train_mask) == "Baseline";

        baseline_features = ...
            X_train_raw(baseline_mask,:);

        baseline_mean = mean(baseline_features,1);

        baseline_mean(abs(baseline_mean) < eps) = eps;

        X_train_personalized(subject_mask,:) = ...
            (X_train_raw(subject_mask,:) - baseline_mean) ...
            ./ abs(baseline_mean);

    end

    %% =====================================================
    % TEST SUBJECT CALIBRATION
    % ======================================================

    test_baseline_mask = ...
        test_condition == "Baseline";

    test_stress_mask = ...
        test_condition == "Stress";

    X_test_baseline = ...
        X_test_raw(test_baseline_mask,:);

    X_test_stress = ...
        X_test_raw(test_stress_mask,:);

    %% Personal baseline

    test_baseline_mean = ...
        mean(X_test_baseline,1);

    test_baseline_mean( ...
        abs(test_baseline_mean) < eps) = eps;

    %% Transform stress windows

    X_test_stress_personalized = ...
        (X_test_stress - test_baseline_mean) ...
        ./ abs(test_baseline_mean);

    %% =====================================================
    % STANDARDIZATION
    % ======================================================

    mu = mean(X_train_personalized,1);

    sigma = std(X_train_personalized,0,1);

    sigma(sigma == 0) = 1;

    X_train_personalized = ...
        (X_train_personalized - mu) ./ sigma;

    X_test_stress_personalized = ...
        (X_test_stress_personalized - mu) ./ sigma;

    %% =====================================================
    % LOGISTIC REGRESSION
    % ======================================================

    X_train_aug = ...
        [ones(size(X_train_personalized,1),1), ...
         X_train_personalized];

    X_test_aug = ...
        [ones(size(X_test_stress_personalized,1),1), ...
         X_test_stress_personalized];

    w = zeros(size(X_train_aug,2),1);

    %% Train

    for iter = 1:iterations

        z = X_train_aug * w;

        z = max(min(z,50),-50);

        p = 1 ./ (1 + exp(-z));

        gradient = ...
            (X_train_aug' * ...
            (p-y_train)) ...
            / size(X_train_aug,1);

        w = w - learning_rate * gradient;

    end

    %% =====================================================
    % STRESS DETECTION
    % ======================================================

    z_test = X_test_aug * w;

    z_test = max(min(z_test,50),-50);

    probability = ...
        1 ./ (1 + exp(-z_test));

    prediction = probability >= threshold;

    %% Store

    true_stress = ones(length(prediction),1);

    all_true = ...
        [all_true; true_stress];

    all_pred = ...
        [all_pred; double(prediction)];

    all_prob = ...
        [all_prob; probability];

    all_subject = ...
        [all_subject;
         repmat(test_subject,length(prediction),1)];

    %% Subject result

    rate = mean(prediction);

    fprintf('Stress windows : %d\n', ...
        length(prediction));

    fprintf('Detected       : %d\n', ...
        sum(prediction));

    fprintf('Detection rate : %.2f %%\n', ...
        rate*100);

end

%% =========================================================
% 8. FINAL METRICS
% ==========================================================

TP = sum(all_true == 1 & all_pred == 1);

FN = sum(all_true == 1 & all_pred == 0);

recall = ...
    TP / max(TP+FN,eps);

fprintf('\n============================================\n');
fprintf('FINAL CALIBRATED STRESS DETECTOR\n');
fprintf('============================================\n');

fprintf('Threshold = %.2f\n', threshold);

fprintf('Total stress windows : %d\n', ...
    length(all_true));

fprintf('Detected stress      : %d\n', TP);

fprintf('Missed stress        : %d\n', FN);

fprintf('Stress Recall        : %.2f %%\n', ...
    recall*100);

%% =========================================================
% 9. SUBJECT-WISE RESULTS
% ==========================================================

fprintf('\n============================================\n');
fprintf('SUBJECT-WISE STRESS DETECTION\n');
fprintf('============================================\n');

SubjectSummary = table( ...
    subjects, ...
    zeros(nSubjects,1), ...
    zeros(nSubjects,1), ...
    zeros(nSubjects,1), ...
    'VariableNames', { ...
    'Subject', ...
    'StressWindows', ...
    'DetectedStress', ...
    'DetectionRate'});

for s = 1:nSubjects

    current_subject = subjects(s);

    idx = all_subject == current_subject;

    total_stress = sum(idx);

    detected_stress = sum(all_pred(idx));

    detection_rate = ...
        detected_stress / max(total_stress,1);

    SubjectSummary.StressWindows(s) = ...
        total_stress;

    SubjectSummary.DetectedStress(s) = ...
        detected_stress;

    SubjectSummary.DetectionRate(s) = ...
        detection_rate * 100;

    fprintf('%s: %d / %d = %.2f %%\n', ...
        current_subject, ...
        detected_stress, ...
        total_stress, ...
        detection_rate*100);

end

%% =========================================================
% 10. SAVE FINAL RESULTS
% ==========================================================

FinalPredictions = table( ...
    all_subject, ...
    all_true, ...
    all_pred, ...
    all_prob, ...
    'VariableNames', { ...
    'Subject', ...
    'TrueLabel', ...
    'PredictedLabel', ...
    'StressProbability'});

writetable( ...
    FinalPredictions, ...
    fullfile(results_folder, ...
    'FINAL_Stress_Detector_Predictions.csv'));

writetable( ...
    SubjectSummary, ...
    fullfile(results_folder, ...
    'FINAL_Subject_Stress_Performance.csv'));

save( ...
    fullfile(results_folder, ...
    'FINAL_Stress_Detector_Results.mat'), ...
    'FinalPredictions', ...
    'SubjectSummary', ...
    'recall', ...
    'threshold');

fprintf('\n============================================\n');
fprintf('FINAL RESULTS SAVED\n');
fprintf('============================================\n');

fprintf('%s\n', ...
    fullfile(results_folder, ...
    'FINAL_Stress_Detector_Predictions.csv'));

fprintf('%s\n', ...
    fullfile(results_folder, ...
    'FINAL_Subject_Stress_Performance.csv'));

fprintf('%s\n', ...
    fullfile(results_folder, ...
    'FINAL_Stress_Detector_Results.mat'));