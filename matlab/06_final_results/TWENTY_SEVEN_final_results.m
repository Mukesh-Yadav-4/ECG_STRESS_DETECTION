% TWENTY_SEVEN_final_results.m
% Aggregates development models, feature ablation, subject-level detection,
% and final calibrated stress-detection results into summary tables and report figures.

clear;
clc;
close all;

%% 1. Paths & Initialization
project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
results_folder = fullfile(project_root, 'results');
figures_folder = fullfile(results_folder, 'figures', 'matlab');

if ~exist(figures_folder, 'dir')
    mkdir(figures_folder);
end

fprintf('Compiling Final WESAD Stress Detection Results...\n');

%% 2. Load Experimental Checkpoints
feature_group_file = fullfile(results_folder, 'Feature_Group_Comparison.mat');
if ~isfile(feature_group_file)
    error('Feature Group Comparison file not found: %s', feature_group_file);
end
load(feature_group_file, 'ComparisonTable');
FeatureGroupComparison = ComparisonTable;

personalized_ablation_file = fullfile(results_folder, 'Personalized_Feature_Ablation.mat');
if ~isfile(personalized_ablation_file)
    error('Personalized Feature Ablation file not found: %s', personalized_ablation_file);
end
load(personalized_ablation_file, 'ComparisonTable');
PersonalizedComparison = ComparisonTable;

final_results_file = fullfile(results_folder, 'FINAL_Stress_Detector_Results.mat');
if ~isfile(final_results_file)
    error('Final detector results file not found: %s', final_results_file);
end
load(final_results_file, 'FinalPredictions', 'threshold');

subject_file = fullfile(results_folder, 'FINAL_Subject_Stress_Performance.csv');
if ~isfile(subject_file)
    error('Subject performance file not found: %s', subject_file);
end
SubjectSummary = readtable(subject_file);

%% 3. Generate High-Contrast, Publication-Quality Report Figures

% Publication Light Theme Palette (Clean Academic Formatting)
c_bg         = [1.00 1.00 1.00];    % Pure white canvas
c_card_bg    = [1.00 1.00 1.00];    % White axis container
c_text_dark  = [0.08 0.11 0.18];    % Dark slate primary text
c_text_muted = [0.38 0.44 0.52];    % Muted slate axis labels & ticks
c_grid       = [0.89 0.92 0.95];    % Subtle light grey grid lines
c_blue       = [0.15 0.39 0.92];    % Royal Blue
c_coral      = [0.86 0.15 0.27];    % Ruby / Coral (Stress / Highlight)
c_amber      = [0.85 0.53 0.08];    % Warm Amber
c_emerald    = [0.06 0.62 0.35];    % Emerald Green
c_purple     = [0.49 0.23 0.93];    % Deep Violet

% Set global light defaults
set(groot, 'defaultFigureColor', c_bg, ...
           'defaultAxesColor', c_card_bg, ...
           'defaultAxesXColor', c_text_muted, ...
           'defaultAxesYColor', c_text_muted, ...
           'defaultTextColor', c_text_dark);

% -------------------------------------------------------------
% Single Multi-Tab Window: Feature & Subject Analysis
% -------------------------------------------------------------
screen_sz = get(0, 'ScreenSize');
fig_w = min(1120, round(screen_sz(3) * 0.74));
fig_h = min(700, round(screen_sz(4) * 0.75));
fig_x = max(30, round((screen_sz(3) - fig_w) / 2));
fig_y = max(50, round((screen_sz(4) - fig_h) / 2));

fig_main = figure('Name', 'Final Results — Publication Figures (Feature & Subject Analysis)', ...
                  'Position', [fig_x fig_y fig_w fig_h], 'Color', c_bg, 'Visible', 'off');
tab_group = uitabgroup(fig_main);

% -------------------------------------------------------------
% Tab 1: Feature Group Comparison
% -------------------------------------------------------------
tab1 = uitab(tab_group, 'Title', 'Feature Group Comparison', 'BackgroundColor', c_bg);
ax1 = axes('Parent', tab1, 'Position', [0.12 0.14 0.82 0.76]);

acc_vals1 = FeatureGroupComparison.Accuracy;
b1 = bar(ax1, acc_vals1, 'BarWidth', 0.62);
b1.FaceColor = 'flat';
for k = 1:numel(acc_vals1)
    b1.CData(k, :) = c_blue;
end
b1.EdgeColor = 'none';

set(ax1, 'Color', c_card_bg, 'XColor', c_text_muted, 'YColor', c_text_muted, ...
    'FontSize', 10.5, 'LineWidth', 1.1, 'Box', 'off');

title(ax1, {'Feature Group Diagnostic Comparison (LOSO Evaluation)', ...
    '\fontsize{10.5}\color[rgb]{0.15,0.39,0.92}\bfKey Finding: Time-domain + Frequency features yield strong performance before personalization'}, ...
    'FontSize', 13, 'FontWeight', 'bold', 'Color', c_text_dark);
xlabel(ax1, 'Feature Set Category', 'FontSize', 11, 'FontWeight', 'bold', 'Color', c_text_dark);
ylabel(ax1, 'LOSO Accuracy (%)', 'FontSize', 11, 'FontWeight', 'bold', 'Color', c_text_dark);
xticks(ax1, 1:height(FeatureGroupComparison));
xticklabels(ax1, FeatureGroupComparison.Model);
xtickangle(ax1, 25);
ylim(ax1, [60 105]);
grid(ax1, 'on');
set(ax1, 'GridColor', c_grid, 'GridAlpha', 0.8);

for i = 1:numel(acc_vals1)
    text(ax1, i, acc_vals1(i) + 1.2, sprintf('%.1f%%', acc_vals1(i)), ...
        'HorizontalAlignment', 'center', 'FontSize', 10, 'FontWeight', 'bold', 'Color', c_text_dark);
end

tab_group.SelectedTab = tab1;
drawnow;
f1 = fullfile(figures_folder, 'FINAL_Feature_Group_Comparison.png');
if isfile(f1), try, delete(f1); catch, end; end
exportgraphics(ax1, f1, 'Resolution', 300, 'BackgroundColor', 'current');
try, copyfile(f1, fullfile(results_folder, 'figures', 'FINAL_Feature_Group_Comparison.png')); catch, end

% -------------------------------------------------------------
% Tab 2: Personalized Feature Ablation
% -------------------------------------------------------------
tab2 = uitab(tab_group, 'Title', 'Personalized Feature Ablation', 'BackgroundColor', c_bg);
ax2 = axes('Parent', tab2, 'Position', [0.12 0.14 0.82 0.76]);

acc_vals2 = PersonalizedComparison.Accuracy;
b2 = bar(ax2, acc_vals2, 'BarWidth', 0.62);
b2.FaceColor = 'flat';
for k = 1:numel(acc_vals2)
    b2.CData(k, :) = c_blue;
end
b2.CData(4, :) = c_coral; % Highlight peak model in Coral
b2.EdgeColor = 'none';

set(ax2, 'Color', c_card_bg, 'XColor', c_text_muted, 'YColor', c_text_muted, ...
    'FontSize', 10.5, 'LineWidth', 1.1, 'Box', 'off');

title(ax2, {'Impact of Subject-Specific Baseline Normalization', ...
    '\fontsize{10.5}\color[rgb]{0.15,0.39,0.92}\bfKey Innovation: Personalization boosts accuracy from 81.6% to 92.4% (+10.8% Gain)'}, ...
    'FontSize', 13, 'FontWeight', 'bold', 'Color', c_text_dark);
xlabel(ax2, 'Normalization Strategy', 'FontSize', 11, 'FontWeight', 'bold', 'Color', c_text_dark);
ylabel(ax2, 'LOSO Accuracy (%)', 'FontSize', 11, 'FontWeight', 'bold', 'Color', c_text_dark);
xticks(ax2, 1:height(PersonalizedComparison));
xticklabels(ax2, PersonalizedComparison.Model);
xtickangle(ax2, 25);
ylim(ax2, [60 108]);
grid(ax2, 'on');
set(ax2, 'GridColor', c_grid, 'GridAlpha', 0.8);

for i = 1:numel(acc_vals2)
    clr = c_text_dark;
    if i == 4, clr = c_coral; end
    text(ax2, i, acc_vals2(i) + 1.2, sprintf('%.1f%%', acc_vals2(i)), ...
        'HorizontalAlignment', 'center', 'FontSize', 10, 'FontWeight', 'bold', 'Color', clr);
end

text(ax2, 4, acc_vals2(4) + 3.2, '\bf\color[rgb]{0.86,0.15,0.27}★ Peak Model (92.4%)', ...
    'HorizontalAlignment', 'center', 'FontSize', 9.5);

tab_group.SelectedTab = tab2;
drawnow;
f2 = fullfile(figures_folder, 'FINAL_Personalized_Feature_Ablation.png');
if isfile(f2), try, delete(f2); catch, end; end
exportgraphics(ax2, f2, 'Resolution', 300, 'BackgroundColor', 'current');
try, copyfile(f2, fullfile(results_folder, 'figures', 'FINAL_Personalized_Feature_Ablation.png')); catch, end

% -------------------------------------------------------------
% Tab 3: Subject-Wise Stress Detection Rate
% -------------------------------------------------------------
tab3 = uitab(tab_group, 'Title', 'Subject Stress Detection', 'BackgroundColor', c_bg);
ax3 = axes('Parent', tab3, 'Position', [0.12 0.14 0.82 0.76]);

det_rates = SubjectSummary.DetectionRate;
b3 = bar(ax3, det_rates, 'BarWidth', 0.68);
b3.FaceColor = 'flat';
for k = 1:height(SubjectSummary)
    if det_rates(k) < 30
        b3.CData(k, :) = c_coral;
    else
        b3.CData(k, :) = c_emerald;
    end
end
b3.EdgeColor = 'none';
hold(ax3, 'on');

mean_recall = 86.25;
yline(ax3, mean_recall, '--', 'Color', c_amber, 'LineWidth', 1.5);
text(ax3, 0.6, mean_recall + 6, sprintf('\\bfMean Sensitivity: %.1f%%', mean_recall), ...
    'Color', c_amber, 'FontSize', 9.5, 'FontWeight', 'bold');

set(ax3, 'Color', c_card_bg, 'XColor', c_text_muted, 'YColor', c_text_muted, ...
    'FontSize', 10.5, 'LineWidth', 1.1, 'Box', 'off');

title(ax3, {'Cross-Subject Generalization (Leave-One-Subject-Out Validation)', ...
    '\fontsize{10.5}\color[rgb]{0.15,0.39,0.92}\bfKey Finding: 14 of 15 subjects achieve high detection rate (Overall Stress Caught: 138/160 = 86.3%)'}, ...
    'FontSize', 13, 'FontWeight', 'bold', 'Color', c_text_dark);
xlabel(ax3, 'WESAD Study Subject', 'FontSize', 11, 'FontWeight', 'bold', 'Color', c_text_dark);
ylabel(ax3, 'Stress Detection Rate / Sensitivity (%)', 'FontSize', 11, 'FontWeight', 'bold', 'Color', c_text_dark);
xticks(ax3, 1:height(SubjectSummary));
xticklabels(ax3, SubjectSummary.Subject);
ylim(ax3, [0 145]);
grid(ax3, 'on');
set(ax3, 'GridColor', c_grid, 'GridAlpha', 0.8);

for i = 1:height(SubjectSummary)
    lbl = sprintf('%d/%d', SubjectSummary.DetectedStress(i), SubjectSummary.StressWindows(i));
    txt_clr = c_text_dark;
    if det_rates(i) < 30, txt_clr = c_coral; end
    text(ax3, i, det_rates(i) + 4.5, lbl, ...
        'Rotation', 90, 'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
        'FontSize', 8, 'FontWeight', 'bold', 'Color', txt_clr);
end

% Automatic callout on non-responder subject (S2: 0/10 caught)
idx_outlier = find(det_rates < 30, 1);
if ~isempty(idx_outlier)
    outlier_name = SubjectSummary.Subject{idx_outlier};
    text(ax3, idx_outlier, 24, {sprintf('\\bf\\color[rgb]{0.86,0.15,0.27}%s: Atypical', outlier_name), 'Autonomic Profile'}, ...
        'HorizontalAlignment', 'center', 'FontSize', 8);
end

tab_group.SelectedTab = tab3;
drawnow;
f3a = fullfile(figures_folder, 'FINAL_Subject_Stress_Detection.png');
f3b = fullfile(figures_folder, 'FINAL_Subject_Stress_Performance.png');
if isfile(f3a), try, delete(f3a); catch, end; end
if isfile(f3b), try, delete(f3b); catch, end; end
exportgraphics(ax3, f3a, 'Resolution', 300, 'BackgroundColor', 'current');
exportgraphics(ax3, f3b, 'Resolution', 300, 'BackgroundColor', 'current');
try, copyfile(f3a, fullfile(results_folder, 'figures', 'FINAL_Subject_Stress_Detection.png')); catch, end
try, copyfile(f3b, fullfile(results_folder, 'figures', 'FINAL_Subject_Stress_Performance.png')); catch, end

%% 4. Compile Executive Summary Tables
total_stress = sum(FinalPredictions.TrueLabel == 1);
detected_stress = sum(FinalPredictions.PredictedLabel == 1 & FinalPredictions.TrueLabel == 1);
missed_stress = total_stress - detected_stress;
final_recall = (detected_stress / max(total_stress, 1)) * 100;

FinalSummary = table( ...
    ["Total Subjects"; "Total Feature Windows"; "Baseline Windows"; "Stress Windows"; ...
     "Detected Stress Windows"; "Missed Stress Windows"; "Stress Recall (%)"; "Locked Decision Threshold"], ...
    [height(SubjectSummary); 445; 285; total_stress; detected_stress; missed_stress; final_recall; threshold], ...
    'VariableNames', {'Metric', 'Value'});

DevelopmentTable = table( ...
    ["HR-only LOSO"; "4-feature LOSO"; "13-feature LOSO"; "Personalized binary LOSO"], ...
    [77.08; 80.90; 81.57; 92.36], ...
    [64.34; 70.59; 73.03; 89.03], ...
    'VariableNames', {'Experiment', 'Accuracy', 'F1'});

fprintf('\n=== Final Project Summary ===\n');
disp(FinalSummary);

fprintf('\n=== Model Development Progression ===\n');
disp(DevelopmentTable);

%% 5. Export Summary CSVs and Master MAT Package
summary_file = fullfile(results_folder, 'FINAL_Project_Summary.csv');
development_file = fullfile(results_folder, 'FINAL_Development_Model_Comparison.csv');
final_package = fullfile(results_folder, 'FINAL_Project_Results.mat');

writetable(FinalSummary, summary_file);
writetable(DevelopmentTable, development_file);

save(final_package, 'FinalSummary', 'DevelopmentTable', 'FeatureGroupComparison', ...
    'PersonalizedComparison', 'SubjectSummary');

fprintf('Summary files and figures successfully updated in results/.\n');