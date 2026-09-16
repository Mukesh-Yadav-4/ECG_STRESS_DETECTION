% TWENTY_personalized_classifier.m
% Implements Leave-One-Subject-Out (LOSO) cross-validation with subject-specific
% baseline calibration (delta_x = (x - mu_base) / mu_base) and gradient-descent
% Logistic Regression.

clear;
clc;
close all;

%% 1. Setup Paths & Load Features
project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
results_folder = fullfile(project_root, 'results');
feature_file = fullfile(results_folder, 'WESAD_HRV_features_expanded.mat');

if ~isfile(feature_file)
    % Fall back to CSV if MAT is unavailable
    csv_file = fullfile(results_folder, 'WESAD_HRV_features_expanded.csv');
    HRV_Table = readtable(csv_file);
else
    load(feature_file, 'HRV_Table');
end

Subject = string(HRV_Table.Subject);
Condition = string(HRV_Table.Condition);
subjects = unique(Subject);
nSubjects = length(subjects);

y = double(Condition == "Stress");

% Select stable time-domain HRV metrics
X = [ ...
    HRV_Table.MeanHR, ...
    HRV_Table.SDNN * 1000, ...
    HRV_Table.RMSSD * 1000, ...
    HRV_Table.pNN50, ...
    HRV_Table.MeanRR * 1000, ...
    HRV_Table.RR_CV, ...
    HRV_Table.RR_IQR * 1000, ...
    HRV_Table.HR_IQR ...
];

feature_names = {'MeanHR', 'SDNN', 'RMSSD', 'pNN50', 'MeanRR_ms', 'RR_CV', 'RR_IQR_ms', 'HR_IQR'};

%% 2. LOSO Cross-Validation Hyperparameters
learning_rate = 0.05;
iterations = 3000;
eps_val = 1e-6;

all_true = [];
all_pred = [];
all_prob = [];

fprintf('Running 15-Fold Leave-One-Subject-Out (LOSO) Evaluation...\n');

%% 3. Leave-One-Subject-Out Loop
for s = 1:nSubjects
    test_subject = subjects(s);
    test_mask = (Subject == test_subject);
    train_mask = ~test_mask;

    X_train = X(train_mask, :);
    X_test = X(test_mask, :);
    y_train = y(train_mask);
    y_test = y(test_mask);

    train_subjects = unique(Subject(train_mask));

    % --- Subject-specific baseline normalization (Training Set) ---
    X_train_personalized = zeros(size(X_train));
    for ts = 1:length(train_subjects)
        curr_sub = train_subjects(ts);
        sub_train_mask = (Subject(train_mask) == curr_sub);
        base_mask = sub_train_mask & (Condition(train_mask) == "Baseline");

        base_vals = X_train(base_mask, :);
        base_mean = mean(base_vals, 1);
        base_mean(abs(base_mean) < eps_val) = eps_val;

        X_train_personalized(sub_train_mask, :) = ...
            (X_train(sub_train_mask, :) - base_mean) ./ abs(base_mean);
    end

    % --- Subject-specific baseline normalization (Test Subject) ---
    test_base_mask = (Condition(test_mask) == "Baseline");
    test_base_vals = X_test(test_base_mask, :);

    if isempty(test_base_vals)
        warning('No baseline windows found for test subject %s. Skipping fold.', test_subject);
        continue;
    end

    test_base_mean = mean(test_base_vals, 1);
    test_base_mean(abs(test_base_mean) < eps_val) = eps_val;

    X_test_personalized = (X_test - test_base_mean) ./ abs(test_base_mean);

    % Standardize using training distribution only (zero data leakage)
    mu = mean(X_train_personalized, 1);
    sigma = std(X_train_personalized, 0, 1);
    sigma(sigma == 0) = 1;

    X_train_norm = (X_train_personalized - mu) ./ sigma;
    X_test_norm = (X_test_personalized - mu) ./ sigma;

    % Augment with bias column
    X_train_aug = [ones(size(X_train_norm, 1), 1), X_train_norm];
    X_test_aug = [ones(size(X_test_norm, 1), 1), X_test_norm];

    % --- Train Logistic Regression via Gradient Descent ---
    w = zeros(size(X_train_aug, 2), 1);
    for iter = 1:iterations
        z = X_train_aug * w;
        z = max(min(z, 50), -50); % Numerical stability clamp
        p = 1 ./ (1 + exp(-z));
        grad = (X_train_aug' * (p - y_train)) / size(X_train_aug, 1);
        w = w - learning_rate * grad;
    end

    % --- Test Prediction ---
    z_test = X_test_aug * w;
    z_test = max(min(z_test, 50), -50);
    prob = 1 ./ (1 + exp(-z_test));
    pred = double(prob >= 0.5);

    all_true = [all_true; y_test];
    all_pred = [all_pred; pred];
    all_prob = [all_prob; prob];

    fprintf('  Fold [%02d/%02d] Subject %-4s | Windows: %2d | Acc: %5.1f%%\n', ...
        s, nSubjects, test_subject, length(y_test), mean(pred == y_test) * 100);
end

%% 4. Confusion Matrix & Diagnostic Metrics
TP = sum(all_true == 1 & all_pred == 1);
TN = sum(all_true == 0 & all_pred == 0);
FP = sum(all_true == 0 & all_pred == 1);
FN = sum(all_true == 1 & all_pred == 0);

accuracy = (TP + TN) / (TP + TN + FP + FN);
precision = TP / max(TP + FP, eps);
recall = TP / max(TP + FN, eps);
specificity = TN / max(TN + FP, eps);
F1 = 2 * precision * recall / max(precision + recall, eps);
balanced_accuracy = (recall + specificity) / 2;

fprintf('\n=== Personalized Classifier LOSO Performance ===\n');
fprintf('Confusion Matrix:\n');
fprintf('               Predicted Base   Predicted Stress\n');
fprintf('  Actual Base  :    %4d             %4d\n', TN, FP);
fprintf('  Actual Stress:    %4d             %4d\n', FN, TP);
fprintf('\n');
fprintf('Accuracy          : %6.2f %%\n', accuracy * 100);
fprintf('Balanced Accuracy : %6.2f %%\n', balanced_accuracy * 100);
fprintf('Precision         : %6.2f %%\n', precision * 100);
fprintf('Recall / Sens     : %6.2f %%\n', recall * 100);
fprintf('Specificity       : %6.2f %%\n', specificity * 100);
fprintf('F1-Score          : %6.2f %%\n', F1 * 100);

%% 5. Save Results
PredictionTable = table(all_true, all_pred, all_prob, ...
    'VariableNames', {'TrueLabel', 'PredictedLabel', 'StressProbability'});

writetable(PredictionTable, fullfile(results_folder, 'Personalized_Classifier_Predictions.csv'));
save(fullfile(results_folder, 'Personalized_Classifier_Results.mat'), ...
    'PredictionTable', 'TP', 'TN', 'FP', 'FN', 'accuracy', 'precision', ...
    'recall', 'specificity', 'F1', 'balanced_accuracy');

fprintf('\nResults successfully saved to results/ folder.\n');