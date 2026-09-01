clear;
clc;
close all;

%% =========================================================
% WESAD PERSONALIZED STRESS CLASSIFIER
%
% Leave-One-Subject-Out Validation
%
% Personalized features are calculated relative to the
% training-derived baseline for each subject.
% ==========================================================

%% =========================================================
% 1. PROJECT PATHS
% ==========================================================

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));

results_folder = fullfile(project_root, 'results');

%% =========================================================
% 2. LOAD EXPANDED FEATURE DATASET
% ==========================================================

feature_file = fullfile( ...
    results_folder, ...
    'WESAD_HRV_features_expanded.mat');

if ~isfile(feature_file)

    error('Expanded feature file not found:\n%s', ...
        feature_file);

end

load(feature_file);

%% =========================================================
% 3. PREPARE DATA
% ==========================================================

Subject = string(HRV_Table.Subject);
Condition = string(HRV_Table.Condition);

subjects = unique(Subject);

y = double(Condition == "Stress");

%% =========================================================
% 4. SELECT FEATURES
% ==========================================================

% We use relatively stable physiological variables.
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

feature_names = { ...
    'MeanHR', ...
    'SDNN', ...
    'RMSSD', ...
    'pNN50', ...
    'MeanRR_ms', ...
    'RR_CV', ...
    'RR_IQR_ms', ...
    'HR_IQR'};

%% =========================================================
% 5. SETTINGS
% ==========================================================

learning_rate = 0.05;
iterations = 3000;

nSubjects = length(subjects);

%% =========================================================
% 6. STORAGE
% ==========================================================

all_true = [];
all_pred = [];
all_prob = [];

%% =========================================================
% 7. LEAVE-ONE-SUBJECT-OUT
% ==========================================================

for s = 1:nSubjects

    test_subject = subjects(s);

    fprintf('\n============================================\n');
    fprintf('Testing subject: %s\n', test_subject);
    fprintf('============================================\n');

    %% -----------------------------------------------------
    % Split subject
    % ------------------------------------------------------

    test_mask = Subject == test_subject;
    train_mask = ~test_mask;

    X_train = X(train_mask,:);
    X_test = X(test_mask,:);

    y_train = y(train_mask);
    y_test = y(test_mask);

    train_subjects = unique(Subject(train_mask));

    %% =====================================================
    % PERSONALIZED BASELINE NORMALIZATION
    %
    % IMPORTANT:
    % For each training subject, calculate their own
    % baseline mean from training data.
    %
    % For the held-out test subject, its baseline is also
    % available as part of the deployment scenario because
    % personalized stress detection requires an initial
    % baseline recording.
    % ======================================================

    %% Create global baseline statistics for feature fallback

    global_baseline = zeros(1,size(X,2));

    for f = 1:size(X,2)

        baseline_values = [];

        for ts = 1:length(train_subjects)

            current_subject = train_subjects(ts);

            idx = ...
                Subject(train_mask) == current_subject & ...
                Condition(train_mask) == "Baseline";

            values = X_train(idx,f);

            baseline_values = ...
                [baseline_values; values];

        end

        global_baseline(f) = mean(baseline_values);

    end

    %% -----------------------------------------------------
    % Calculate personalized baseline for every training
    % subject and transform their windows
    % ------------------------------------------------------

    X_train_personalized = zeros(size(X_train));

    for ts = 1:length(train_subjects)

        current_subject = train_subjects(ts);

        subject_mask_train = ...
            Subject(train_mask) == current_subject;

        subject_baseline_mask = ...
            subject_mask_train & ...
            Condition(train_mask) == "Baseline";

        %% Subject baseline

        baseline_values = ...
            X_train(subject_baseline_mask,:);

        baseline_mean = mean(baseline_values,1);

        %% Avoid zero denominators

        baseline_mean(abs(baseline_mean) < eps) = eps;

        %% Relative change

        X_train_personalized(subject_mask_train,:) = ...
            (X_train(subject_mask_train,:) - baseline_mean) ...
            ./ abs(baseline_mean);

    end

    %% -----------------------------------------------------
    % Test subject baseline
    % ------------------------------------------------------

    subject_baseline_mask_test = ...
        Condition(test_mask) == "Baseline";

    test_baseline_values = ...
        X_test(subject_baseline_mask_test,:);

    if isempty(test_baseline_values)

        warning( ...
            'No baseline data found for test subject %s.', ...
            test_subject);

        continue;

    end

    test_baseline_mean = ...
        mean(test_baseline_values,1);

    test_baseline_mean( ...
        abs(test_baseline_mean) < eps) = eps;

    %% Relative test features

    X_test_personalized = ...
        (X_test - test_baseline_mean) ...
        ./ abs(test_baseline_mean);

    %% =====================================================
    % STANDARDIZE USING TRAINING DATA ONLY
    % ======================================================

    mu = mean(X_train_personalized,1);

    sigma = std(X_train_personalized,0,1);

    sigma(sigma == 0) = 1;

    X_train_personalized = ...
        (X_train_personalized - mu) ./ sigma;

    X_test_personalized = ...
        (X_test_personalized - mu) ./ sigma;

    %% =====================================================
    % LOGISTIC REGRESSION
    % ======================================================

    X_train_aug = ...
        [ones(size(X_train_personalized,1),1), ...
         X_train_personalized];

    X_test_aug = ...
        [ones(size(X_test_personalized,1),1), ...
         X_test_personalized];

    w = zeros(size(X_train_aug,2),1);

    %% Training

    for iter = 1:iterations

        z = X_train_aug * w;

        z = max(min(z,50),-50);

        p = 1 ./ (1 + exp(-z));

        gradient = ...
            (X_train_aug' * (p-y_train)) ...
            / size(X_train_aug,1);

        w = w - learning_rate * gradient;

    end

    %% =====================================================
    % TEST
    % ======================================================

    z = X_test_aug * w;

    z = max(min(z,50),-50);

    probability = ...
        1 ./ (1 + exp(-z));

    prediction = probability >= 0.5;

    %% Store

    all_true = [all_true; y_test];

    all_pred = ...
        [all_pred; double(prediction)];

    all_prob = ...
        [all_prob; probability];

    %% Subject accuracy

    subject_accuracy = ...
        mean(prediction == y_test);

    fprintf('Test windows : %d\n', length(y_test));

    fprintf('Accuracy     : %.2f %%\n', ...
        subject_accuracy * 100);

end

%% =========================================================
% 8. CONFUSION MATRIX
% ==========================================================

TP = sum(all_true == 1 & all_pred == 1);
TN = sum(all_true == 0 & all_pred == 0);
FP = sum(all_true == 0 & all_pred == 1);
FN = sum(all_true == 1 & all_pred == 0);

%% =========================================================
% 9. PERFORMANCE
% ==========================================================

accuracy = ...
    (TP+TN) / ...
    (TP+TN+FP+FN);

precision = ...
    TP / max(TP+FP,eps);

recall = ...
    TP / max(TP+FN,eps);

specificity = ...
    TN / max(TN+FP,eps);

F1 = ...
    2*precision*recall / ...
    max(precision+recall,eps);

balanced_accuracy = ...
    (recall+specificity)/2;

%% =========================================================
% 10. DISPLAY
% ==========================================================

fprintf('\n============================================\n');
fprintf('PERSONALIZED CLASSIFIER RESULTS\n');
fprintf('============================================\n');

fprintf('\n                Predicted\n');
fprintf('              Baseline Stress\n');
fprintf('Actual Baseline   %d       %d\n',TN,FP);
fprintf('Actual Stress     %d       %d\n',FN,TP);

fprintf('\nAccuracy          : %.2f %%\n', ...
    accuracy*100);

fprintf('Precision         : %.2f %%\n', ...
    precision*100);

fprintf('Recall            : %.2f %%\n', ...
    recall*100);

fprintf('Specificity       : %.2f %%\n', ...
    specificity*100);

fprintf('F1-score          : %.2f %%\n', ...
    F1*100);

fprintf('Balanced Accuracy : %.2f %%\n', ...
    balanced_accuracy*100);

%% =========================================================
% 11. SAVE RESULTS
% ==========================================================

PredictionTable = table( ...
    all_true, ...
    all_pred, ...
    all_prob, ...
    'VariableNames', { ...
    'TrueLabel', ...
    'PredictedLabel', ...
    'StressProbability'});

writetable( ...
    PredictionTable, ...
    fullfile(results_folder, ...
    'Personalized_Classifier_Predictions.csv'));

save( ...
    fullfile(results_folder, ...
    'Personalized_Classifier_Results.mat'), ...
    'PredictionTable', ...
    'TP', 'TN', 'FP', 'FN', ...
    'accuracy', ...
    'precision', ...
    'recall', ...
    'specificity', ...
    'F1', ...
    'balanced_accuracy');

fprintf('\nPersonalized classifier results saved.\n');