clear;
clc;
close all;

%% =========================================================
% EXPANDED FEATURE STRESS CLASSIFIER
% Leave-One-Subject-Out Logistic Regression
% ==========================================================

%% Project paths

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
results_folder = fullfile(project_root, 'results');

%% Load expanded feature dataset

feature_file = fullfile( ...
    results_folder, ...
    'WESAD_HRV_features_expanded.mat');

load(feature_file);

%% Basic data

Subject = string(HRV_Table.Subject);
Condition = string(HRV_Table.Condition);

%% Target
% Baseline = 0
% Stress   = 1

y = double(Condition == "Stress");

%% Expanded feature matrix

X = [ ...
    HRV_Table.MeanHR, ...
    HRV_Table.MedianHR, ...
    HRV_Table.StdHR, ...
    HRV_Table.MinHR, ...
    HRV_Table.MaxHR, ...
    HRV_Table.MeanRR, ...
    HRV_Table.MedianRR, ...
    HRV_Table.SDNN * 1000, ...
    HRV_Table.RMSSD * 1000, ...
    HRV_Table.pNN50, ...
    HRV_Table.RR_CV, ...
    HRV_Table.RR_IQR, ...
    HRV_Table.HR_IQR];

feature_names = { ...
    'MeanHR', ...
    'MedianHR', ...
    'StdHR', ...
    'MinHR', ...
    'MaxHR', ...
    'MeanRR', ...
    'MedianRR', ...
    'SDNN', ...
    'RMSSD', ...
    'pNN50', ...
    'RR_CV', ...
    'RR_IQR', ...
    'HR_IQR'};

fprintf('\n============================================\n');
fprintf('EXPANDED FEATURE STRESS CLASSIFIER\n');
fprintf('============================================\n');

fprintf('Subjects : %d\n', length(unique(Subject)));
fprintf('Samples  : %d\n', length(y));
fprintf('Features : %d\n', size(X,2));

%% =========================================================
% Logistic regression settings
% ==========================================================

learning_rate = 0.05;
iterations = 3000;

%% Prediction storage

all_true = [];
all_pred = [];
all_prob = [];
all_test_subject = strings(0,1);

subjects = unique(Subject);
nSubjects = length(subjects);

%% =========================================================
% LEAVE-ONE-SUBJECT-OUT
% ==========================================================

for s = 1:nSubjects

    test_subject = subjects(s);

    fprintf('\n--------------------------------------------\n');
    fprintf('Testing subject: %s\n', test_subject);
    fprintf('--------------------------------------------\n');

    %% Split subjects

    test_mask = Subject == test_subject;
    train_mask = ~test_mask;

    X_train = X(train_mask,:);
    X_test  = X(test_mask,:);

    y_train = y(train_mask);
    y_test  = y(test_mask);

    %% Standardize using training data ONLY

    mu = mean(X_train,1);
    sigma = std(X_train,0,1);

    sigma(sigma == 0) = 1;

    X_train = (X_train - mu) ./ sigma;
    X_test  = (X_test - mu) ./ sigma;

    %% Add intercept

    X_train = [ones(size(X_train,1),1) X_train];
    X_test  = [ones(size(X_test,1),1) X_test];

    %% Initialize weights

    w = zeros(size(X_train,2),1);

    %% =====================================================
    % Train logistic regression
    % ======================================================

    for iter = 1:iterations

        z = X_train * w;

        % Numerical protection
        z = max(min(z,50),-50);

        probability = 1 ./ (1 + exp(-z));

        gradient = ...
            (X_train' * (probability - y_train)) ...
            / size(X_train,1);

        w = w - learning_rate * gradient;

    end

    %% =====================================================
    % Test unseen subject
    % ======================================================

    z = X_test * w;

    z = max(min(z,50),-50);

    probability = 1 ./ (1 + exp(-z));

    prediction = probability >= 0.5;

    %% Store

    all_true = [all_true; y_test];
    all_pred = [all_pred; double(prediction)];
    all_prob = [all_prob; probability];

    all_test_subject = ...
        [all_test_subject;
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
% METRICS
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

balanced_accuracy = ...
    (recall + specificity) / 2;

fprintf('\n============================================\n');
fprintf('FINAL PERFORMANCE\n');
fprintf('============================================\n');

fprintf('Accuracy          : %.2f %%\n', accuracy*100);
fprintf('Precision         : %.2f %%\n', precision*100);
fprintf('Recall            : %.2f %%\n', recall*100);
fprintf('Specificity       : %.2f %%\n', specificity*100);
fprintf('F1-score          : %.2f %%\n', F1*100);
fprintf('Balanced Accuracy : %.2f %%\n', balanced_accuracy*100);

%% =========================================================
% SAVE
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
    'Expanded_Classifier_Predictions.csv'));

save( ...
    fullfile(results_folder, ...
    'Expanded_Classifier_Results.mat'), ...
    'PredictionTable', ...
    'TP', 'TN', 'FP', 'FN', ...
    'accuracy', ...
    'precision', ...
    'recall', ...
    'specificity', ...
    'F1', ...
    'balanced_accuracy', ...
    'feature_names');

fprintf('\nExpanded classifier results saved.\n');