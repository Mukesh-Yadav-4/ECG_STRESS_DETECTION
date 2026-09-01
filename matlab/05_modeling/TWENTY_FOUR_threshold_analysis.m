clear;
clc;
close all;

%% =========================================================
% PERSONALIZED CLASSIFIER THRESHOLD ANALYSIS
% ==========================================================

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));

results_folder = fullfile(project_root,'results');

%% Load predictions

prediction_file = fullfile( ...
    results_folder, ...
    'Personalized_Classifier_Predictions.csv');

PredictionTable = readtable(prediction_file);

%% Extract

y_true = PredictionTable.TrueLabel;

probability = PredictionTable.StressProbability;

%% Threshold range

thresholds = 0.10:0.01:0.90;

n = length(thresholds);

accuracy = zeros(n,1);
precision = zeros(n,1);
recall = zeros(n,1);
specificity = zeros(n,1);
F1 = zeros(n,1);
balanced_accuracy = zeros(n,1);

%% =========================================================
% Evaluate each threshold
% ==========================================================

for i = 1:n

    threshold = thresholds(i);

    y_pred = probability >= threshold;

    %% Confusion matrix

    TP = sum(y_true == 1 & y_pred == 1);
    TN = sum(y_true == 0 & y_pred == 0);
    FP = sum(y_true == 0 & y_pred == 1);
    FN = sum(y_true == 1 & y_pred == 0);

    %% Metrics

    accuracy(i) = ...
        (TP+TN) / ...
        max(TP+TN+FP+FN,eps);

    precision(i) = ...
        TP / max(TP+FP,eps);

    recall(i) = ...
        TP / max(TP+FN,eps);

    specificity(i) = ...
        TN / max(TN+FP,eps);

    F1(i) = ...
        2*precision(i)*recall(i) / ...
        max(precision(i)+recall(i),eps);

    balanced_accuracy(i) = ...
        (recall(i)+specificity(i))/2;

end

%% =========================================================
% Find best thresholds
% ==========================================================

[best_F1, idx_F1] = max(F1);

best_F1_threshold = thresholds(idx_F1);

[best_BA, idx_BA] = max(balanced_accuracy);

best_BA_threshold = thresholds(idx_BA);

[best_accuracy, idx_ACC] = max(accuracy);

best_accuracy_threshold = thresholds(idx_ACC);

%% =========================================================
% Display
% ==========================================================

fprintf('\n============================================\n');
fprintf('THRESHOLD ANALYSIS\n');
fprintf('============================================\n');

fprintf('\nDefault threshold:\n');
fprintf('0.50\n');

default_idx = ...
    find(abs(thresholds-0.50) < 1e-10);

fprintf('Accuracy          : %.2f %%\n', ...
    accuracy(default_idx)*100);

fprintf('Precision         : %.2f %%\n', ...
    precision(default_idx)*100);

fprintf('Recall            : %.2f %%\n', ...
    recall(default_idx)*100);

fprintf('Specificity       : %.2f %%\n', ...
    specificity(default_idx)*100);

fprintf('F1                : %.2f %%\n', ...
    F1(default_idx)*100);

fprintf('Balanced Accuracy : %.2f %%\n', ...
    balanced_accuracy(default_idx)*100);

%% Best F1

fprintf('\nBEST F1 THRESHOLD\n');
fprintf('Threshold         : %.2f\n', ...
    best_F1_threshold);

fprintf('Accuracy          : %.2f %%\n', ...
    accuracy(idx_F1)*100);

fprintf('Precision         : %.2f %%\n', ...
    precision(idx_F1)*100);

fprintf('Recall            : %.2f %%\n', ...
    recall(idx_F1)*100);

fprintf('Specificity       : %.2f %%\n', ...
    specificity(idx_F1)*100);

fprintf('F1                : %.2f %%\n', ...
    best_F1*100);

fprintf('Balanced Accuracy : %.2f %%\n', ...
    balanced_accuracy(idx_F1)*100);

%% Best balanced accuracy

fprintf('\nBEST BALANCED ACCURACY THRESHOLD\n');
fprintf('Threshold         : %.2f\n', ...
    best_BA_threshold);

fprintf('Accuracy          : %.2f %%\n', ...
    accuracy(idx_BA)*100);

fprintf('Precision         : %.2f %%\n', ...
    precision(idx_BA)*100);

fprintf('Recall            : %.2f %%\n', ...
    recall(idx_BA)*100);

fprintf('Specificity       : %.2f %%\n', ...
    specificity(idx_BA)*100);

fprintf('F1                : %.2f %%\n', ...
    F1(idx_BA)*100);

fprintf('Balanced Accuracy : %.2f %%\n', ...
    best_BA*100);

%% =========================================================
% Plot metrics vs threshold
% ==========================================================

figure;

plot(thresholds, accuracy*100, 'o-');
hold on;
plot(thresholds, precision*100, 'o-');
plot(thresholds, recall*100, 'o-');
plot(thresholds, specificity*100, 'o-');
plot(thresholds, F1*100, 'o-');
plot(thresholds, balanced_accuracy*100, 'o-');

xlabel('Classification Threshold');
ylabel('Performance (%)');

title('Classifier Performance vs Decision Threshold');

legend( ...
    'Accuracy', ...
    'Precision', ...
    'Recall', ...
    'Specificity', ...
    'F1', ...
    'Balanced Accuracy');

grid on;

%% =========================================================
% Save table
% ==========================================================

ThresholdTable = table( ...
    thresholds(:), ...
    accuracy*100, ...
    precision*100, ...
    recall*100, ...
    specificity*100, ...
    F1*100, ...
    balanced_accuracy*100, ...
    'VariableNames', { ...
    'Threshold', ...
    'Accuracy', ...
    'Precision', ...
    'Recall', ...
    'Specificity', ...
    'F1', ...
    'BalancedAccuracy'});

writetable( ...
    ThresholdTable, ...
    fullfile(results_folder, ...
    'Threshold_Analysis.csv'));

save( ...
    fullfile(results_folder, ...
    'Threshold_Analysis.mat'), ...
    'ThresholdTable');

fprintf('\nThreshold analysis saved.\n');