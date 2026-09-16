% TWENTY_NINE_project_dashboard.m
% Master multi-panel project dashboard for WESAD ECG Stress Detection.
% Features cosmic space-themed telemetry styling, clear non-overlapping annotations,
% and clinical performance metrics across all 15 Leave-One-Subject-Out (LOSO) folds.

clear;
clc;
close all;

%% 1. Paths & Data Loading
matlab_root = fileparts(mfilename('fullpath'));
project_root = fileparts(matlab_root);
results_folder = fullfile(project_root, 'results');
figures_folder = fullfile(results_folder, 'figures', 'matlab');

if ~exist(figures_folder, 'dir')
    mkdir(figures_folder);
end

FeatureGroup = readtable(fullfile(results_folder, 'Feature_Group_Comparison.csv'));
Personalized = readtable(fullfile(results_folder, 'Personalized_Feature_Ablation.csv'));
Subject = readtable(fullfile(results_folder, 'FINAL_Subject_Stress_Performance.csv'));
ROC = readtable(fullfile(results_folder, 'Personalized_ROC.csv'));

FPR = ROC.FalsePositiveRate;
TPR = ROC.TruePositiveRate;
AUC = trapz(FPR, TPR);

% Final validated operating parameters (tau = 0.35)
accuracy = 92.36;
precision = 92.00;
recall = 86.25;
specificity = 95.79;
F1 = 89.03;
balanced_accuracy = 91.02;
threshold = 0.35;
TP = 138; TN = 273; FP = 12; FN = 22;

% Publication Light Theme Palette (Clean Academic Formatting)
c_bg         = [1.00 1.00 1.00];    % Pure white canvas
c_card_bg    = [1.00 1.00 1.00];    % White axis container
c_text_dark  = [0.08 0.11 0.18];    % Dark slate primary text
c_text_muted = [0.38 0.44 0.52];    % Muted slate axis labels & ticks
c_grid       = [0.89 0.92 0.95];    % Subtle light grey grid lines
c_blue       = [0.15 0.39 0.92];    % Royal Blue (Accuracy / Primary model)
c_coral      = [0.86 0.15 0.27];    % Ruby / Coral (Stress / Recall)
c_amber      = [0.85 0.53 0.08];    % Warm Amber (F1-score / Operating point)
c_emerald    = [0.06 0.62 0.35];    % Emerald Green (High detection)
c_purple     = [0.49 0.23 0.93];    % Deep Violet

% Set global light defaults
set(groot, 'defaultFigureColor', c_bg, ...
           'defaultAxesColor', c_card_bg, ...
           'defaultAxesXColor', c_text_muted, ...
           'defaultAxesYColor', c_text_muted, ...
           'defaultTextColor', c_text_dark);

%% 2. Figure Layout Setup
fig_w = 1500;
fig_h = 860;
fig_x = 50;
fig_y = 50;

fig = figure('Color', c_bg, 'Position', [fig_x fig_y fig_w fig_h], ...
             'Name', 'WESAD ECG Stress Detection — Results Dashboard', ...
             'Visible', 'off');

t = tiledlayout(fig, 2, 3, 'TileSpacing', 'compact', 'Padding', 'compact');
title(t, 'WESAD ECG Stress Detection Pipeline — Results Dashboard', ...
    'FontSize', 13.5, 'FontWeight', 'bold', 'Color', c_text_dark);
subtitle(t, '15-Fold Leave-One-Subject-Out (LOSO) Cross-Validation  •  Baseline-Relative HRV  •  Operating Point: \tau = 0.35', ...
    'FontSize', 9.5, 'FontWeight', 'bold', 'Color', c_blue);

%% Panel 1: Model Development Progression
ax1 = nexttile(t);
model_names = {'HR only', '4 features', '13 features', 'Personalized'};
model_accuracy = [77.08; 80.90; 81.57; 92.36];

b1 = bar(ax1, model_accuracy, 'BarWidth', 0.62);
b1.FaceColor = 'flat';
for k = 1:3
    b1.CData(k, :) = c_blue;
end
b1.CData(4, :) = c_coral; % Highlight winning personalized model in Coral
b1.EdgeColor = 'none';

set(ax1, 'Color', c_card_bg, 'XColor', c_text_muted, 'YColor', c_text_muted, ...
    'FontSize', 8.5, 'LineWidth', 1.0, 'Box', 'off');
title(ax1, {'Model Development Progression', '\fontsize{8.5}\color[rgb]{0.38,0.44,0.52}Raw HR to Baseline-Relative HRV'}, ...
    'FontSize', 10, 'FontWeight', 'bold', 'Color', c_text_dark);
ylabel(ax1, 'Accuracy (%)', 'FontSize', 9, 'FontWeight', 'bold', 'Color', c_text_dark);
xticks(ax1, 1:4);
xticklabels(ax1, model_names);
xtickangle(ax1, 10);
ylim(ax1, [0 112]);
grid(ax1, 'on');
set(ax1, 'GridColor', c_grid, 'GridAlpha', 0.8);

for i = 1:4
    clr = c_text_dark;
    if i == 4, clr = c_coral; end
    text(ax1, i, model_accuracy(i) + 3.0, sprintf('%.1f%%', model_accuracy(i)), ...
        'HorizontalAlignment', 'center', 'FontWeight', 'bold', 'FontSize', 8.5, 'Color', clr);
end

%% Panel 2: Personalized Feature Ablation
ax2 = nexttile(t);
ablation_values = [Personalized.Accuracy, Personalized.F1];
b2 = bar(ax2, ablation_values, 'grouped', 'BarWidth', 0.82);
b2(1).FaceColor = c_blue;  b2(1).EdgeColor = 'none';
b2(2).FaceColor = c_amber; b2(2).EdgeColor = 'none';

set(ax2, 'Color', c_card_bg, 'XColor', c_text_muted, 'YColor', c_text_muted, ...
    'FontSize', 8, 'LineWidth', 1.0, 'Box', 'off');
title(ax2, {'Personalized Feature Ablation', '\fontsize{8.5}\color[rgb]{0.38,0.44,0.52}Relative HR + HRV Feature Subsets'}, ...
    'FontSize', 10, 'FontWeight', 'bold', 'Color', c_text_dark);
ylabel(ax2, 'Performance (%)', 'FontSize', 9, 'FontWeight', 'bold', 'Color', c_text_dark);
xticks(ax2, 1:height(Personalized));

ablation_labels = {'ΔHR only', '+ ΔSDNN', '+ ΔRMSSD', '+ ΔpNN50', '+ Classical HRV', '+ Distribution', 'All 8 Features'};
xticklabels(ax2, ablation_labels);
xtickangle(ax2, 20);
ylim(ax2, [0 115]);
legend(ax2, b2, {'Accuracy', 'F1-score'}, 'Location', 'northwest', ...
    'Orientation', 'horizontal', 'Box', 'on', 'Color', c_bg, 'TextColor', c_text_dark, 'EdgeColor', c_grid, 'FontSize', 8);
grid(ax2, 'on');
set(ax2, 'GridColor', c_grid, 'GridAlpha', 0.8);

%% Panel 3: Subject-by-Subject Recall
ax3 = nexttile(t);
b3 = bar(ax3, Subject.DetectionRate, 'BarWidth', 0.68);
b3.FaceColor = 'flat';
for k = 1:height(Subject)
    if Subject.DetectionRate(k) < 30
        b3.CData(k, :) = c_coral; % Highlight atypical responder in Coral
    else
        b3.CData(k, :) = c_emerald;
    end
end
b3.EdgeColor = 'none';
hold(ax3, 'on');

yline(ax3, recall, '--', 'LineWidth', 1.3, 'Color', c_amber, 'HandleVisibility', 'off');
text(ax3, 0.8, 134, sprintf('── Mean Recall: %.1f%%', recall), ...
    'FontSize', 8, 'FontWeight', 'bold', 'Color', c_amber);

set(ax3, 'Color', c_card_bg, 'XColor', c_text_muted, 'YColor', c_text_muted, ...
    'FontSize', 8, 'LineWidth', 1.0, 'Box', 'off');
title(ax3, {'Subject Stress Recall (15 Folds)', '\fontsize{8.5}\color[rgb]{0.38,0.44,0.52}Subject-by-Subject Recall at \tau = 0.35'}, ...
    'FontSize', 10, 'FontWeight', 'bold', 'Color', c_text_dark);
ylabel(ax3, 'Detection Rate (%)', 'FontSize', 9, 'FontWeight', 'bold', 'Color', c_text_dark);
xticks(ax3, 1:height(Subject));
xticklabels(ax3, Subject.Subject);
ylim(ax3, [0 148]);
grid(ax3, 'on');
set(ax3, 'GridColor', c_grid, 'GridAlpha', 0.8);

for i = 1:height(Subject)
    lbl = sprintf('%d/%d', Subject.DetectedStress(i), Subject.StressWindows(i));
    txt_color = c_text_dark;
    if Subject.DetectionRate(i) < 30, txt_color = c_coral; end
    text(ax3, i, Subject.DetectionRate(i) + 4, lbl, ...
        'Rotation', 90, 'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
        'FontSize', 7.5, 'FontWeight', 'bold', 'Color', txt_color);
end

%% Panel 4: Calibrated Confusion Matrix
ax4 = nexttile(t);
CM = [TN, FP; FN, TP];
imagesc(ax4, CM);

% Smooth light blue colormap
light_blue_map = [linspace(0.95, 0.15, 64)', linspace(0.97, 0.39, 64)', linspace(1.00, 0.92, 64)'];
colormap(ax4, light_blue_map);
axis(ax4, 'equal', 'tight');

set(ax4, 'Color', c_card_bg, 'XColor', c_text_muted, 'YColor', c_text_muted, ...
    'FontSize', 8.5, 'LineWidth', 1.0, 'Box', 'on');
xticks(ax4, [1 2]); yticks(ax4, [1 2]);
xticklabels(ax4, {'Pred Baseline', 'Pred Stress'});
yticklabels(ax4, {'Actual Baseline', 'Actual Stress'});
xlabel(ax4, 'Predicted Condition', 'FontSize', 9, 'FontWeight', 'bold', 'Color', c_text_dark);
ylabel(ax4, 'Actual Condition', 'FontSize', 9, 'FontWeight', 'bold', 'Color', c_text_dark);
title(ax4, {'LOSO Confusion Matrix (\tau = 0.35)', '\fontsize{8.5}\color[rgb]{0.38,0.44,0.52}Accuracy: 92.4% (411/445 Correct)'}, ...
    'FontSize', 10, 'FontWeight', 'bold', 'Color', c_text_dark);

cb4 = colorbar(ax4);
cb4.Color = c_text_muted;
cb4.FontSize = 8;

dash_cell_labels = {
    sprintf('\\bf%d\\rm\n\\fontsize{7.5}True Baseline\n(95.8%%)', TN), ...
    sprintf('\\bf%d\\rm\n\\fontsize{7.5}False Stress\n(4.2%%)', FP); ...
    sprintf('\\bf%d\\rm\n\\fontsize{7.5}Missed Stress\n(13.8%%)', FN), ...
    sprintf('\\bf%d\\rm\n\\fontsize{7.5}Detected Stress\n(86.3%%)', TP)
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
        text(ax4, c, r, dash_cell_labels{r, c}, ...
            'HorizontalAlignment', 'center', 'FontSize', 9.5, 'FontWeight', 'bold', 'Color', txt_c);
    end
end

%% Panel 5: Final ROC Curve
ax5 = nexttile(t);
plot(ax5, FPR, TPR, 'LineWidth', 2.4, 'Color', c_coral);
hold(ax5, 'on');
plot(ax5, [0 1], [0 1], '--', 'Color', c_text_muted, 'LineWidth', 1.1);
operating_fpr = FP / (FP + TN);
operating_tpr = TP / (TP + FN);
plot(ax5, operating_fpr, operating_tpr, 'o', 'MarkerSize', 7, ...
    'MarkerFaceColor', c_amber, 'MarkerEdgeColor', c_text_dark);

% Callout box on operating point
text(ax5, operating_fpr + 0.06, operating_tpr - 0.12, ...
    sprintf('\\bf\\tau = %.2f\\rm\nRecall: %.1f%%\nSpec: %.1f%%', threshold, recall, specificity), ...
    'FontSize', 7.5, 'BackgroundColor', c_bg, 'EdgeColor', c_coral, 'Color', c_text_dark, 'LineWidth', 0.9);

set(ax5, 'Color', c_card_bg, 'XColor', c_text_muted, 'YColor', c_text_muted, ...
    'FontSize', 8.5, 'LineWidth', 1.0, 'Box', 'on');
title(ax5, {'ROC Trajectory (\tau = 0.35)', sprintf('\\fontsize{8.5}\\color[rgb]{0.38,0.44,0.52}Test ROC-AUC = %.4f', AUC)}, ...
    'FontSize', 10, 'FontWeight', 'bold', 'Color', c_text_dark);
xlabel(ax5, 'False Positive Rate (1 - Specificity)', 'FontSize', 9, 'FontWeight', 'bold', 'Color', c_text_dark);
ylabel(ax5, 'True Positive Rate (Sensitivity)', 'FontSize', 9, 'FontWeight', 'bold', 'Color', c_text_dark);
xlim(ax5, [-0.02 1.02]); ylim(ax5, [-0.02 1.02]);
legend(ax5, {'Model ROC', 'Chance', '\tau = 0.35'}, 'Location', 'southeast', ...
    'Color', c_bg, 'TextColor', c_text_dark, 'EdgeColor', c_grid, 'FontSize', 8);
grid(ax5, 'on');
set(ax5, 'GridColor', c_grid, 'GridAlpha', 0.8);

%% Panel 6: Performance Scorecard (Compact Non-Clipping)
ax6 = nexttile(t);
axis(ax6, 'off');
title(ax6, {'Performance Scorecard', '\fontsize{8.5}\color[rgb]{0.38,0.44,0.52}15-Fold Leave-One-Subject-Out (LOSO)'}, ...
    'FontSize', 10, 'FontWeight', 'bold', 'Color', c_text_dark);

scorecard_lines = {
    sprintf('\\bf\\color[rgb]{0.15,0.39,0.92}● Overall Accuracy     \\color[rgb]{0.08,0.11,0.18}: %5.2f%% \\rm(411/445 Correct)', accuracy)
    sprintf('\\bf\\color[rgb]{0.86,0.15,0.27}● Stress Recall (Sens) \\color[rgb]{0.08,0.11,0.18}: %5.2f%% \\rm(138/160 Caught)', recall)
    sprintf('\\bf\\color[rgb]{0.06,0.62,0.35}● Baseline Specificity \\color[rgb]{0.08,0.11,0.18}: %5.2f%% \\rm(Only 12 False Alarms)', specificity)
    sprintf('\\bf\\color[rgb]{0.85,0.53,0.08}● Precision            \\color[rgb]{0.08,0.11,0.18}: %5.2f%% \\rm(High Trust / Few FP)', precision)
    sprintf('\\bf\\color[rgb]{0.38,0.44,0.52}● Balanced Accuracy   : %5.2f%%', balanced_accuracy)
    sprintf('\\bf\\color[rgb]{0.38,0.44,0.52}● Harmonic F1-Score    : %5.2f%%', F1)
    sprintf('\\bf\\color[rgb]{0.15,0.39,0.92}● Model ROC-AUC        :  %.4f', AUC)
    ''
    '\color[rgb]{0.80,0.84,0.88}──────────────────────────────────────────'
    sprintf('\\color[rgb]{0.38,0.44,0.52}Operating Threshold (\\tau) : %.2f (Sensitivity-Tuned)', threshold)
    '\color[rgb]{0.38,0.44,0.52}Validation Protocol        : 15-Fold LOSO'
    '\color[rgb]{0.38,0.44,0.52}Feature Normalization      : Baseline-Relative HRV'
};

text(ax6, 0.04, 0.95, scorecard_lines, ...
    'Units', 'normalized', 'VerticalAlignment', 'top', ...
    'FontSize', 8.2, 'FontName', 'Consolas', 'Color', c_text_dark);

%% 3. Export High-Resolution Dashboard
dashboard_file = fullfile(figures_folder, 'FINAL_Project_Dashboard.png');
if isfile(dashboard_file)
    try, delete(dashboard_file); catch, end
end
exportgraphics(fig, dashboard_file, 'Resolution', 220, 'BackgroundColor', 'current');

% Also copy to results/figures/ for README and documentation links
root_figures = fullfile(results_folder, 'figures');
if exist(root_figures, 'dir')
    try, copyfile(dashboard_file, fullfile(root_figures, 'FINAL_Project_Dashboard.png')); catch, end
end

close(fig);
fprintf('Master Publication Light Project Dashboard saved to:\n  %s\n', dashboard_file);