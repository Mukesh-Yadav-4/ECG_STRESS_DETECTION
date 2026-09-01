clear;
clc;
close all;

%% =========================================================
% WESAD ECG STRESS CLASSIFIER
% Leave-One-Subject-Out Validation
% Base MATLAB implementation
% ==========================================================

%% Project paths

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
results_folder = fullfile(project_root, 'results');

%% Load feature dataset

feature_file = fullfile( ...
    results_folder, ...
    'WESAD_HRV_features.mat');

load(feature_file);

%% ---------------------------------------------------------
% Extract data
% ----------------------------------------------------------

Subject = string(HRV_Table.Subject);
Condition = string(HRV_Table.Condition);

%% Convert target labels
% Baseline = 0
% Stress   = 1

y = double(Condition == "Stress");

%% Feature matrix

X = [ ...
    HRV_Table.MeanHR, ...
    HRV_Table.SDNN * 1000, ...
    HRV_Table.RMSSD * 1000, ...
    HRV_Table.pNN50];

feature_names = { ...
    'MeanHR', ...
    'SDNN', ...
    'RMSSD', ...
    'pNN50'};

%% Subjects

subjects = unique(Subject);

nSubjects = length(subjects);
nSamples = length(y);
nFeatures = size(X,2);

fprintf('\n============================================\n');
fprintf('WESAD STRESS CLASSIFIER\n');
fprintf('============================================\n');

fprintf('Subjects : %d\n', nSubjects);
fprintf('Samples  : %d\n', nSamples);
fprintf('Features : %d\n', nFeatures);

%% =========================================================
% Logistic regression settings
% ==========================================================

learning_rate = 0.05;
iterations = 3000;

%% Storage for predictions

all_true = [];
all_pred = [];
all_prob = [];
all_test_subject = strings(0,1);

%% =========================================================
% LEAVE-ONE-SUBJECT-OUT
% ==========================================================

for s = 1:nSubjects

    test_subject = subjects(s);

    fprintf('\n--------------------------------------------\n');
    fprintf('Testing subject: %s\n', test_subject);
    fprintf('--------------------------------------------\n');

    %% Training/test masks

    test_mask = Subject == test_subject;
    train_mask = ~test_mask;

    X_train = X(train_mask,:);
    y_train = y(train_mask);

    X_test = X(test_mask,:);
    y_test = y(test_mask);

    %% -----------------------------------------------------
    % Standardize using TRAINING data only
    % ------------------------------------------------------

    mu = mean(X_train,1);
    sigma = std(X_train,0,1);

    % Prevent division by zero
    sigma(sigma == 0) = 1;

    X_train_norm = ...
        (X_train - mu) ./ sigma;

    X_test_norm = ...
        (X_test - mu) ./ sigma;

    %% -----------------------------------------------------
    % Add intercept
    % ------------------------------------------------------

    X_train_aug = [ones(size(X_train_norm,1),1) X_train_norm];
    X_test_aug  = [ones(size(X_test_norm,1),1) X_test_norm];

    nTrain = size(X_train_aug,1);

    %% -----------------------------------------------------
    % Initialize weights
    % ------------------------------------------------------

    w = zeros(size(X_train_aug,2),1);

    %% -----------------------------------------------------
    % Logistic regression training
    % ------------------------------------------------------

    for iter = 1:iterations

        % Linear prediction
        z = X_train_aug * w;

        % Sigmoid
        p = 1 ./ (1 + exp(-z));

        % Gradient
        gradient = ...
            (X_train_aug' * (p - y_train)) / nTrain;

        % Update
        w = w - learning_rate * gradient;

    end

    %% -----------------------------------------------------
    % Test
    % ------------------------------------------------------

    z_test = X_test_aug * w;

    probability = ...
        1 ./ (1 + exp(-z_test));

    prediction = probability >= 0.5;

    %% Store predictions

    all_true = [all_true; y_test];
    all_pred = [all_pred; double(prediction)];
    all_prob = [all_prob; probability];
    all_test_subject = ...
        [all_test_subject; ...
         repmat(test_subject,sum(test_mask),1)];

    %% Subject accuracy

    subject_accuracy = ...
        mean(prediction == y_test);

    fprintf('Test samples : %d\n', length(y_test));
    fprintf('Accuracy     : %.2f %%\n', ...
        subject_accuracy * 100);

end

%% =========================================================
% CONFUSION MATRIX
% ==========================================================

TP = sum(all_true == 1 & all_pred == 1);
TN = sum(all_true == 0 & all_pred == 0);
FP = sum(all_true == 0 & all_pred == 1);
FN = sum(all_true == 1 & all_pred == 0);

fprintf('\n============================================\n');
fprintf('CONFUSION MATRIX\n');
fprintf('============================================\n');

fprintf('\n                Predicted\n');
fprintf('              Baseline Stress\n');
fprintf('Actual Baseline   %d       %d\n', TN, FP);
fprintf('Actual Stress     %d       %d\n', FN, TP);

%% =========================================================
% PERFORMANCE METRICS
% ==========================================================

accuracy = ...
    (TP + TN) / (TP + TN + FP + FN);

precision = ...
    TP / max(TP + FP, eps);

recall = ...
    TP / max(TP + FN, eps);

specificity = ...
    TN / max(TN + FP, eps);

F1 = ...
    2 * precision * recall / ...
    max(precision + recall, eps);

fprintf('\n============================================\n');
fprintf('FINAL PERFORMANCE\n');
fprintf('============================================\n');

fprintf('Accuracy    : %.2f %%\n', accuracy * 100);
fprintf('Precision   : %.2f %%\n', precision * 100);
fprintf('Recall      : %.2f %%\n', recall * 100);
fprintf('Specificity : %.2f %%\n', specificity * 100);
fprintf('F1-score    : %.2f %%\n', F1 * 100);

%% =========================================================
% SAVE PREDICTIONS
% ==========================================================

PredictionTable = table( ...
    all_test_subject, ...
    all_true, ...
    all_pred, ...
    all_prob, ...
    'VariableNames', { ...
    'Subject', ...
    'TrueLabel', ...
    'PredictedLabel', ...
    'StressProbability'});

writetable( ...
    PredictionTable, ...
    fullfile(results_folder, ...
    'Stress_Classifier_Predictions.csv'));

save( ...
    fullfile(results_folder, ...
    'Stress_Classifier_Results.mat'), ...
    'PredictionTable', ...
    'TP', 'TN', 'FP', 'FN', ...
    'accuracy', ...
    'precision', ...
    'recall', ...
    'specificity', ...
    'F1');

fprintf('\nClassifier results saved.\n');