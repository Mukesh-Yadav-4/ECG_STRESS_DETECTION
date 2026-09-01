clear;
clc;
close all;

%% =========================================================
% ROC / AUC ANALYSIS
% Base MATLAB implementation
% =========================================================

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
results_folder = fullfile(project_root,'results');

%% Load personalized predictions

PredictionTable = readtable( ...
    fullfile(results_folder, ...
    'Personalized_Classifier_Predictions.csv'));

y_true = double(PredictionTable.TrueLabel);
scores = double(PredictionTable.StressProbability);

%% =========================================================
% Threshold sweep
% ==========================================================

thresholds = linspace(0,1,1001);

TPR = zeros(size(thresholds));
FPR = zeros(size(thresholds));

for i = 1:length(thresholds)

    threshold = thresholds(i);

    y_pred = scores >= threshold;

    TP = sum(y_true == 1 & y_pred == 1);
    TN = sum(y_true == 0 & y_pred == 0);
    FP = sum(y_true == 0 & y_pred == 1);
    FN = sum(y_true == 1 & y_pred == 0);

    TPR(i) = TP / max(TP + FN, eps);

    FPR(i) = FP / max(FP + TN, eps);

end

%% =========================================================
% Sort by false-positive rate
% ==========================================================

[FPR_sorted, idx] = sort(FPR);
TPR_sorted = TPR(idx);

%% Remove duplicate FPR values

[FPR_unique, unique_idx] = unique(FPR_sorted);
TPR_unique = TPR_sorted(unique_idx);

%% =========================================================
% Trapezoidal AUC
% ==========================================================

AUC = trapz(FPR_unique, TPR_unique);

%% =========================================================
% Display
% ==========================================================

fprintf('\n============================================\n');
fprintf('ROC / AUC ANALYSIS\n');
fprintf('============================================\n');

fprintf('AUC = %.4f\n', AUC);

%% =========================================================
% Find Youden's J optimum
% ==========================================================

J = TPR - FPR;

[best_J, best_idx] = max(J);

best_threshold = thresholds(best_idx);

best_TPR = TPR(best_idx);
best_FPR = FPR(best_idx);

fprintf('\nYouden optimum\n');
fprintf('Threshold : %.3f\n', best_threshold);
fprintf('TPR       : %.2f %%\n', best_TPR*100);
fprintf('FPR       : %.2f %%\n', best_FPR*100);
fprintf('Youden J  : %.4f\n', best_J);

%% =========================================================
% Plot ROC
% ==========================================================

figure;

plot(FPR_unique, TPR_unique, 'o-');

hold on;

plot([0 1],[0 1],'--');

xlabel('False Positive Rate');

ylabel('True Positive Rate');

title(sprintf('ROC Curve - Personalized Model (AUC = %.3f)',AUC));

legend('ROC','Chance');

grid on;

%% =========================================================
% Save
% ==========================================================

ROC_Results = table( ...
    FPR_unique(:), ...
    TPR_unique(:), ...
    'VariableNames', ...
    {'FalsePositiveRate','TruePositiveRate'});

writetable( ...
    ROC_Results, ...
    fullfile(results_folder, ...
    'Personalized_ROC.csv'));

save( ...
    fullfile(results_folder, ...
    'Personalized_ROC.mat'), ...
    'ROC_Results', ...
    'AUC', ...
    'best_threshold', ...
    'best_TPR', ...
    'best_FPR');

fprintf('\nROC results saved.\n');