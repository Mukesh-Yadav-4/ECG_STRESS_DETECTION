clear;
clc;
close all;

%% =========================================================
% CALIBRATION-AWARE PERSONALIZED STRESS DETECTION
%
% Baseline = calibration
% Stress   = detection target
%
% Evaluation is performed on stress windows only.
%
% The model is trained using the other subjects.
% ==========================================================

%% =========================================================
% 1. PROJECT PATHS
% ==========================================================

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
results_folder = fullfile(project_root, 'results');

%% =========================================================
% 2. LOAD EXPANDED FEATURE DATA
% ==========================================================

feature_file = fullfile( ...
    results_folder, ...
    'WESAD_HRV_features_expanded.mat');

if ~isfile(feature_file)

    error('Feature file not found:\n%s', feature_file);

end

load(feature_file);

%% =========================================================
% 3. BASIC DATA
% ==========================================================

Subject = string(HRV_Table.Subject);
Condition = string(HRV_Table.Condition);

subjects = unique(Subject);

nSubjects = length(subjects);

%% =========================================================
% 4. RAW FEATURES
% ==========================================================

% We use the same 8-feature personalized representation
% that was used in our previous personalized experiment.
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
% 5. TARGET
% ==========================================================

% Baseline = 0
% Stress   = 1

y = double(Condition == "Stress");

%% =========================================================
% 6. STORAGE
% ==========================================================

all_true = [];
all_pred = [];
all_prob = [];

test_subjects = strings(0,1);

%% Store stress-only predictions
stress_true = [];
stress_pred = [];
stress_prob = [];

%% =========================================================
% 7. LOSO
% ==========================================================

for s = 1:nSubjects

    test_subject = subjects(s);

    fprintf('\n============================================\n');
    fprintf('TEST SUBJECT: %s\n', test_subject);
    fprintf('============================================\n');

    %% -----------------------------------------------------
    % TRAINING SUBJECTS
    % ------------------------------------------------------

    train_mask = Subject ~= test_subject;

    X_train_raw = X(train_mask,:);
    y_train = y(train_mask);

    train_subjects = unique(Subject(train_mask));

    %% -----------------------------------------------------
    % TEST SUBJECT
    % ------------------------------------------------------

    test_mask = Subject == test_subject;

    X_test_raw = X(test_mask,:);
    y_test = y(test_mask);

    test_condition = Condition(test_mask);

    %% =====================================================
    % PERSONALIZED TRANSFORMATION FOR TRAINING SUBJECTS
    % =====================================================

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
    % CALIBRATE TEST SUBJECT
    % =====================================================

    baseline_test_mask = ...
        test_condition == "Baseline";

    stress_test_mask = ...
        test_condition == "Stress";

    %% We use baseline only to calibrate this person.

    X_test_baseline = ...
        X_test_raw(baseline_test_mask,:);

    X_test_stress = ...
        X_test_raw(stress_test_mask,:);

    %% Test subject baseline

    test_baseline_mean = ...
        mean(X_test_baseline,1);

    test_baseline_mean( ...
        abs(test_baseline_mean) < eps) = eps;

    %% Convert stress windows into personalized features

    X_test_stress_personalized = ...
        (X_test_stress - test_baseline_mean) ...
        ./ abs(test_baseline_mean);

    %% =====================================================
    % STANDARDIZATION
    % =====================================================

    mu = mean(X_train_personalized,1);

    sigma = std(X_train_personalized,0,1);

    sigma(sigma == 0) = 1;

    X_train_personalized = ...
        (X_train_personalized - mu) ./ sigma;

    X_test_stress_personalized = ...
        (X_test_stress_personalized - mu) ./ sigma;

    %% =====================================================
    % LOGISTIC REGRESSION
    % =====================================================

    X_train_aug = ...
        [ones(size(X_train_personalized,1),1), ...
         X_train_personalized];

    X_test_aug = ...
        [ones(size(X_test_stress_personalized,1),1), ...
         X_test_stress_personalized];

    w = zeros(size(X_train_aug,2),1);

    learning_rate = 0.05;
    iterations = 3000;

    %% Training

    for iter = 1:iterations

        z = X_train_aug * w;

        z = max(min(z,50),-50);

        probability = ...
            1 ./ (1 + exp(-z));

        gradient = ...
            (X_train_aug' * ...
            (probability-y_train)) ...
            / size(X_train_aug,1);

        w = w - learning_rate * gradient;

    end

    %% =====================================================
    % DETECT STRESS WINDOWS
    % =====================================================

    z_test = X_test_aug * w;

    z_test = max(min(z_test,50),-50);

    probability = ...
        1 ./ (1 + exp(-z_test));

    prediction = probability >= 0.5;

    %% =====================================================
    % STORE STRESS RESULTS
    % =====================================================

    true_stress = ones(length(prediction),1);

    stress_true = ...
        [stress_true; true_stress];

    stress_pred = ...
        [stress_pred; double(prediction)];

    stress_prob = ...
        [stress_prob; probability];

    test_subjects = ...
        [test_subjects; ...
         repmat(test_subject, ...
         length(prediction),1)];

    %% Subject stress detection rate

    stress_detection_rate = ...
        mean(prediction == true_stress);

    fprintf('Stress windows: %d\n', ...
        length(prediction));

    fprintf('Stress detection rate: %.2f %%\n', ...
        stress_detection_rate*100);

end

%% =========================================================
% 8. STRESS-ONLY METRICS
% ==========================================================

TP = sum(stress_pred == 1);

FN = sum(stress_pred == 0);

recall = TP / max(TP + FN, eps);

fprintf('\n============================================\n');
fprintf('CALIBRATED STRESS DETECTION\n');
fprintf('============================================\n');

fprintf('Total stress windows: %d\n', ...
    length(stress_true));

fprintf('Detected as stress: %d\n', TP);

fprintf('Missed stress windows: %d\n', FN);

fprintf('Stress detection rate / Recall: %.2f %%\n', ...
    recall*100);

%% =========================================================
% 9. SUBJECT-LEVEL STRESS DETECTION
% ==========================================================

fprintf('\n============================================\n');
fprintf('SUBJECT-LEVEL STRESS DETECTION\n');
fprintf('============================================\n');

for s = 1:nSubjects

    current_subject = subjects(s);

    idx = test_subjects == current_subject;

    subject_rate = ...
        mean(stress_pred(idx) == 1);

    fprintf('%s: %.2f %% of stress windows detected\n', ...
        current_subject, ...
        subject_rate*100);

end

%% =========================================================
% 10. SAVE
% ==========================================================

CalibrationResults = table( ...
    test_subjects, ...
    stress_true, ...
    stress_pred, ...
    stress_prob, ...
    'VariableNames', { ...
    'Subject', ...
    'TrueStress', ...
    'PredictedStress', ...
    'StressProbability'});

writetable( ...
    CalibrationResults, ...
    fullfile(results_folder, ...
    'Calibrated_Stress_Detection.csv'));

save( ...
    fullfile(results_folder, ...
    'Calibrated_Stress_Detection.mat'), ...
    'CalibrationResults', ...
    'recall');

fprintf('\nResults saved.\n');