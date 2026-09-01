clear;
clc;
close all;

%% =========================================================
% FINAL REPORT FIGURES
%
% Creates:
%   1. ROC curve
%   2. Confusion matrix at locked threshold = 0.35
%
% Uses the saved personalized classifier probabilities.
% ==========================================================

%% =========================================================
% 1. PROJECT PATHS
% ==========================================================

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));

results_folder = fullfile( ...
    project_root, ...
    'results');

figures_folder = fullfile( ...
    results_folder, ...
    'figures');

if ~exist(figures_folder,'dir')
    mkdir(figures_folder);
end

%% =========================================================
% 2. LOAD PERSONALIZED CLASSIFIER PREDICTIONS
% ==========================================================

prediction_file = fullfile( ...
    results_folder, ...
    'Personalized_Classifier_Predictions.csv');

if ~isfile(prediction_file)

    error('Prediction file not found:\n%s', ...
        prediction_file);

end

PredictionTable = readtable(prediction_file);

y_true = double(PredictionTable.TrueLabel);

scores = double(PredictionTable.StressProbability);

%% Locked threshold

threshold = 0.35;

%% =========================================================
% 3. CONFUSION MATRIX AT LOCKED THRESHOLD
% ==========================================================

y_pred = scores >= threshold;

TP = sum(y_true == 1 & y_pred == 1);

TN = sum(y_true == 0 & y_pred == 0);

FP = sum(y_true == 0 & y_pred == 1);

FN = sum(y_true == 1 & y_pred == 0);

%% Metrics

accuracy = ...
    (TP + TN) / ...
    (TP + TN + FP + FN);

precision = ...
    TP / max(TP + FP,eps);

recall = ...
    TP / max(TP + FN,eps);

specificity = ...
    TN / max(TN + FP,eps);

F1 = ...
    2 * precision * recall / ...
    max(precision + recall,eps);

balanced_accuracy = ...
    (recall + specificity) / 2;

fprintf('\n============================================\n');
fprintf('LOCKED-THRESHOLD CONFUSION MATRIX\n');
fprintf('============================================\n');

fprintf('Threshold = %.2f\n\n',threshold);

fprintf('TN = %d\n',TN);
fprintf('FP = %d\n',FP);
fprintf('FN = %d\n',FN);
fprintf('TP = %d\n',TP);

fprintf('\nAccuracy          = %.2f %%\n', ...
    accuracy*100);

fprintf('Precision         = %.2f %%\n', ...
    precision*100);

fprintf('Recall            = %.2f %%\n', ...
    recall*100);

fprintf('Specificity       = %.2f %%\n', ...
    specificity*100);

fprintf('F1                = %.2f %%\n', ...
    F1*100);

fprintf('Balanced Accuracy = %.2f %%\n', ...
    balanced_accuracy*100);

%% =========================================================
% 4. CREATE CONFUSION MATRIX FIGURE
% ==========================================================

CM = [TN FP;
      FN TP];

figure;

imagesc(CM);

axis equal tight;

xlabel('Predicted Class');

ylabel('Actual Class');

title(sprintf( ...
    'Confusion Matrix - Personalized Model (Threshold = %.2f)', ...
    threshold));

xticks([1 2]);

yticks([1 2]);

xticklabels({'Baseline','Stress'});

yticklabels({'Baseline','Stress'});

colorbar;

%% Add numerical labels

for row = 1:2

    for col = 1:2

        text( ...
            col, ...
            row, ...
            sprintf('%d',CM(row,col)), ...
            'HorizontalAlignment','center', ...
            'FontSize',16, ...
            'FontWeight','bold');

    end

end

%% Save

saveas(gcf, fullfile( ...
    figures_folder, ...
    'FINAL_Confusion_Matrix.png'));

%% =========================================================
% 5. ROC CURVE
% ==========================================================

roc_file = fullfile( ...
    results_folder, ...
    'Personalized_ROC.csv');

if ~isfile(roc_file)

    error('ROC file not found:\n%s',roc_file);

end

ROC_Table = readtable(roc_file);

FPR = ROC_Table.FalsePositiveRate;

TPR = ROC_Table.TruePositiveRate;

%% Calculate AUC again

AUC = trapz(FPR,TPR);

%% =========================================================
% 6. ROC FIGURE
% ==========================================================

figure;

plot(FPR,TPR,'LineWidth',2);

hold on;

plot([0 1],[0 1],'--');

xlabel('False Positive Rate');

ylabel('True Positive Rate');

title(sprintf( ...
    'ROC Curve - Personalized ECG Stress Detector (AUC = %.4f)', ...
    AUC));

legend( ...
    'ROC Curve', ...
    'Chance', ...
    'Location','southeast');

xlim([0 1]);

ylim([0 1]);

grid on;

%% Save

saveas(gcf, fullfile( ...
    figures_folder, ...
    'FINAL_ROC_Curve.png'));

%% =========================================================
% 7. SAVE FINAL METRIC SUMMARY
% ==========================================================

Metric = {
    'Threshold'
    'AUC'
    'Accuracy'
    'Precision'
    'Recall'
    'Specificity'
    'F1'
    'BalancedAccuracy'
    'TN'
    'FP'
    'FN'
    'TP'
    };

Value = [
    threshold
    AUC
    accuracy * 100
    precision * 100
    recall * 100
    specificity * 100
    F1 * 100
    balanced_accuracy * 100
    TN
    FP
    FN
    TP
    ];

FinalModelMetrics = table( ...
    string(Metric), ...
    Value, ...
    'VariableNames', ...
    {'Metric','Value'});

writetable( ...
    FinalModelMetrics, ...
    fullfile(results_folder, ...
    'FINAL_Model_Metrics.csv'));

save( ...
    fullfile(results_folder, ...
    'FINAL_Model_Metrics.mat'), ...
    'FinalModelMetrics');

%% =========================================================
% 8. DISPLAY FINAL OUTPUT
% ==========================================================

fprintf('\n============================================\n');
fprintf('FINAL REPORT FIGURES CREATED\n');
fprintf('============================================\n');

fprintf('\nConfusion matrix:\n%s\n', ...
    fullfile(figures_folder, ...
    'FINAL_Confusion_Matrix.png'));

fprintf('\nROC curve:\n%s\n', ...
    fullfile(figures_folder, ...
    'FINAL_ROC_Curve.png'));

fprintf('\nMetrics:\n%s\n', ...
    fullfile(results_folder, ...
    'FINAL_Model_Metrics.csv'));

fprintf('\nAUC = %.4f\n',AUC);

fprintf('\nDONE\n');