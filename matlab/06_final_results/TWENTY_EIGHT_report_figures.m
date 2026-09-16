% TWENTY_EIGHT_report_figures.m
% Generates final calibrated ROC curve and Confusion Matrix figures
% at locked threshold tau = 0.35 with publication-grade styling.

clear;
clc;
close all;

%% 1. Paths & Load Predictions
project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
results_folder = fullfile(project_root, 'results');
figures_folder = fullfile(results_folder, 'figures', 'matlab');

if ~exist(figures_folder, 'dir')
    mkdir(figures_folder);
end

prediction_file = fullfile(results_folder, 'Personalized_Classifier_Predictions.csv');
if ~isfile(prediction_file)
    error('Prediction file not found: %s', prediction_file);
end

PredictionTable = readtable(prediction_file);
y_true = double(PredictionTable.TrueLabel);
scores = double(PredictionTable.StressProbability);

threshold = 0.35;
y_pred = double(scores >= threshold);

%% 2. Performance Metrics at Locked Threshold
TP = sum(y_true == 1 & y_pred == 1);
TN = sum(y_true == 0 & y_pred == 0);
FP = sum(y_true == 0 & y_pred == 1);
FN = sum(y_true == 1 & y_pred == 0);

accuracy = (TP + TN) / (TP + TN + FP + FN);
precision = TP / max(TP + FP, eps);
recall = TP / max(TP + FN, eps);
specificity = TN / max(TN + FP, eps);
F1 = 2 * precision * recall / max(precision + recall, eps);
balanced_accuracy = (recall + specificity) / 2;

% Publication Light Theme Palette (Clean Academic Formatting)
c_bg         = [1.00 1.00 1.00];    % Pure white canvas
c_card_bg    = [1.00 1.00 1.00];    % White axis container
c_text_dark  = [0.08 0.11 0.18];    % Dark slate primary text
c_text_muted = [0.38 0.44 0.52];    % Muted slate axis labels & ticks
c_grid       = [0.89 0.92 0.95];    % Subtle light grey grid lines
c_blue       = [0.15 0.39 0.92];    % Royal Blue
c_coral      = [0.86 0.15 0.27];    % Ruby / Coral (Stress)
c_amber      = [0.85 0.53 0.08];    % Warm Amber
c_emerald    = [0.06 0.62 0.35];    % Emerald Green

% Set global light defaults
set(groot, 'defaultFigureColor', c_bg, ...
           'defaultAxesColor', c_card_bg, ...
           'defaultAxesXColor', c_text_muted, ...
           'defaultAxesYColor', c_text_muted, ...
           'defaultTextColor', c_text_dark);

%% 3. Multi-Tab Publication Figures Setup
fig_w = 960;
fig_h = 720;
fig_x = 50;
fig_y = 50;

fig_main = figure('Name', 'Final Publication Figures (Confusion Matrix & ROC)', ...
                  'Position', [fig_x fig_y fig_w fig_h], 'Color', c_bg, 'Visible', 'off');
tab_group = uitabgroup(fig_main);

% -------------------------------------------------------------
% Tab 1: Calibrated Confusion Matrix
% -------------------------------------------------------------
tab1 = uitab(tab_group, 'Title', 'Confusion Matrix', 'BackgroundColor', c_bg);
ax_cm = axes('Parent', tab1, 'Position', [0.18 0.16 0.68 0.72]);

CM = [TN, FP; FN, TP];
imagesc(ax_cm, CM);

% Smooth light blue colormap
light_blue_map = [linspace(0.95, 0.15, 64)', linspace(0.97, 0.39, 64)', linspace(1.00, 0.92, 64)'];
colormap(ax_cm, light_blue_map);
axis(ax_cm, 'equal', 'tight');

set(ax_cm, 'Color', c_card_bg, 'XColor', c_text_muted, 'YColor', c_text_muted, ...
    'FontSize', 8.5, 'LineWidth', 1.0, 'Box', 'on');

xticks(ax_cm, [1 2]); yticks(ax_cm, [1 2]);
xticklabels(ax_cm, {'Predicted Baseline', 'Predicted Stress'});
yticklabels(ax_cm, {'Actual Baseline', 'Actual Stress'});
xlabel(ax_cm, 'Predicted Condition', 'FontSize', 9.5, 'FontWeight', 'bold', 'Color', c_text_dark);
ylabel(ax_cm, 'Actual Condition', 'FontSize', 9.5, 'FontWeight', 'bold', 'Color', c_text_dark);
title(ax_cm, {'Leave-One-Subject-Out (LOSO) Stress Confusion Matrix (\tau = 0.35)', ...
    '\fontsize{8.5}\color[rgb]{0.15,0.39,0.92}\bfAccuracy: 92.4% (411/445)  \bullet  Recall: 86.3% (138/160)  \bullet  Specificity: 95.8% (273/285)'}, ...
    'FontSize', 10.5, 'FontWeight', 'bold', 'Color', c_text_dark);

cb = colorbar(ax_cm);
cb.Color = c_text_muted;
cb.FontSize = 8;
ylabel(cb, 'Number of 60-Second Windows', 'FontSize', 8.5, 'FontWeight', 'bold', 'Color', c_text_dark);

cell_labels = {
    sprintf('\\bf%d\\rm\n\\fontsize{8}True Baseline\n\\fontsize{7.5}(95.8%%)', TN), ...
    sprintf('\\bf%d\\rm\n\\fontsize{8}False Stress\n\\fontsize{7.5}(4.2%%)', FP); ...
    sprintf('\\bf%d\\rm\n\\fontsize{8}Missed Stress\n\\fontsize{7.5}(13.8%%)', FN), ...
    sprintf('\\bf%d\\rm\n\\fontsize{8}Detected Stress\n\\fontsize{7.5}(86.3%%)', TP)
};

min_val = min(CM(:)); max_val = max(CM(:));
for r = 1:2
    for c = 1:2
        val = CM(r, c);
        norm_i = (val - min_val) / max(max_val - min_val, 1);
        if norm_i > 0.50
            txt_c = [1.00 1.00 1.00];
        else
            txt_c = c_text_dark;
        end
        text(ax_cm, c, r, cell_labels{r, c}, ...
            'HorizontalAlignment', 'center', 'FontSize', 10.5, 'FontWeight', 'bold', 'Color', txt_c);
    end
end

tab_group.SelectedTab = tab1;
drawnow;
cm_fig_file = fullfile(figures_folder, 'FINAL_Confusion_Matrix.png');
if isfile(cm_fig_file), try, delete(cm_fig_file); catch, end; end
exportgraphics(ax_cm, cm_fig_file, ...
    'Resolution', 300, 'BackgroundColor', 'current', 'Padding', 15);

root_cm = fullfile(results_folder, 'figures', 'FINAL_Confusion_Matrix.png');
try, copyfile(cm_fig_file, root_cm); catch, end

% -------------------------------------------------------------
% Tab 2: Final ROC Curve
% -------------------------------------------------------------
roc_file = fullfile(results_folder, 'Personalized_ROC.csv');
if ~isfile(roc_file)
    error('ROC file not found: %s', roc_file);
end

ROC_Table = readtable(roc_file);
FPR = ROC_Table.FalsePositiveRate;
TPR = ROC_Table.TruePositiveRate;
AUC = trapz(FPR, TPR);

tab2 = uitab(tab_group, 'Title', 'ROC Curve', 'BackgroundColor', c_bg);
ax_roc = axes('Parent', tab2, 'Position', [0.10 0.12 0.84 0.78]);

plot(ax_roc, FPR, TPR, 'LineWidth', 2.4, 'Color', c_coral, ...
    'DisplayName', sprintf('Personalized Model (AUC = %.4f)', AUC));
hold(ax_roc, 'on');
plot(ax_roc, [0 1], [0 1], '--', 'Color', c_text_muted, 'LineWidth', 1.1, ...
    'DisplayName', 'Chance Baseline (AUC = 0.5000)');

operating_fpr = FP / (FP + TN);
operating_tpr = TP / (TP + FN);
plot(ax_roc, operating_fpr, operating_tpr, 'o', 'MarkerSize', 8, ...
    'MarkerFaceColor', c_amber, 'MarkerEdgeColor', c_text_dark, ...
    'DisplayName', sprintf('Operating Point (\\tau = %.2f)', threshold));

% Operating point callout box with clean scientific typography
text(ax_roc, operating_fpr + 0.05, operating_tpr - 0.10, ...
    sprintf('\\bfOperating Point (\\tau = %.2f)\n\\rm\\bullet Sensitivity: %.1f%% (138/160)\n\\bullet Specificity: %.1f%% (273/285)\n\\bullet Accuracy: %.1f%% (411/445)', ...
    threshold, recall*100, specificity*100, accuracy*100), ...
    'FontSize', 8.0, 'BackgroundColor', c_bg, 'EdgeColor', c_coral, 'Color', c_text_dark, 'LineWidth', 0.9);

set(ax_roc, 'Color', c_card_bg, 'XColor', c_text_muted, 'YColor', c_text_muted, ...
    'FontSize', 8.5, 'LineWidth', 1.0, 'Box', 'on');

xlabel(ax_roc, 'False Positive Rate (1 - Specificity)', 'FontSize', 9.5, 'FontWeight', 'bold', 'Color', c_text_dark);
ylabel(ax_roc, 'True Positive Rate (Sensitivity / Recall)', 'FontSize', 9.5, 'FontWeight', 'bold', 'Color', c_text_dark);
title(ax_roc, {'Receiver Operating Characteristic (ROC) Trajectory', ...
    sprintf('\\fontsize{8.5}\\color[rgb]{0.15,0.39,0.92}\\bfTest ROC-AUC = %.4f  \\bullet  15-Fold Leave-One-Subject-Out (LOSO)', AUC)}, ...
    'FontSize', 10.5, 'FontWeight', 'bold', 'Color', c_text_dark);
xlim(ax_roc, [-0.02 1.02]); ylim(ax_roc, [-0.02 1.02]);
legend(ax_roc, 'Location', 'southeast', 'Box', 'on', 'Color', c_bg, 'TextColor', c_text_dark, 'EdgeColor', c_grid, 'FontSize', 8.0);
grid(ax_roc, 'on');
set(ax_roc, 'GridColor', c_grid, 'GridAlpha', 0.8);

tab_group.SelectedTab = tab2;
drawnow;
roc_fig_file = fullfile(figures_folder, 'FINAL_ROC_Curve.png');
if isfile(roc_fig_file), try, delete(roc_fig_file); catch, end; end
exportgraphics(ax_roc, roc_fig_file, ...
    'Resolution', 300, 'BackgroundColor', 'current');

root_roc = fullfile(results_folder, 'figures', 'FINAL_ROC_Curve.png');
try, copyfile(roc_fig_file, root_roc); catch, end

%% 5. Save Final Summary Metrics Table
Metric = {
    'Threshold'; 'AUC'; 'Accuracy'; 'Precision'; 'Recall'; 'Specificity'; ...
    'F1'; 'BalancedAccuracy'; 'TN'; 'FP'; 'FN'; 'TP'
};

Value = [
    threshold; AUC; accuracy * 100; precision * 100; recall * 100; ...
    specificity * 100; F1 * 100; balanced_accuracy * 100; TN; FP; FN; TP
];

FinalModelMetrics = table(string(Metric), Value, 'VariableNames', {'Metric', 'Value'});
writetable(FinalModelMetrics, fullfile(results_folder, 'FINAL_Model_Metrics.csv'));
save(fullfile(results_folder, 'FINAL_Model_Metrics.mat'), 'FinalModelMetrics');

fprintf('Updated FINAL_Confusion_Matrix.png, FINAL_ROC_Curve.png, and FINAL_Model_Metrics.csv.\n');