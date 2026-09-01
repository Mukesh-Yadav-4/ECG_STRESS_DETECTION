clear;
clc;
close all;

%% =========================================================
% FINAL WESAD ECG STRESS DETECTION RESULTS
%
% Purpose:
%   Collect the important development and final calibrated
%   stress-detection results into report-ready tables/figures.
%
% Important:
%   Feature-group results and personalized-ablation results
%   are stored in DIFFERENT variables so they cannot
%   overwrite each other.
% ==========================================================

%% =========================================================
% 1. PROJECT PATHS
% ==========================================================

% Script location:
% ECG_STRESS_DETECTION/matlab/

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
results_folder = fullfile( ...
    project_root, ...
    'results');

figures_folder = fullfile( ...
    results_folder, ...
    'figures');

if ~exist(figures_folder, 'dir')
    mkdir(figures_folder);
end

fprintf('\nProject root:\n%s\n', project_root);

fprintf('\nResults folder:\n%s\n', results_folder);

%% =========================================================
% 2. LOAD FEATURE GROUP COMPARISON
% ==========================================================

feature_group_file = fullfile( ...
    results_folder, ...
    'Feature_Group_Comparison.mat');

if ~isfile(feature_group_file)

    error( ...
        'Feature Group Comparison file not found:\n%s', ...
        feature_group_file);

end

load(feature_group_file);

% Rename immediately so it cannot be overwritten later
FeatureGroupComparison = ComparisonTable;

%% =========================================================
% 3. LOAD PERSONALIZED FEATURE ABLATION
% ==========================================================

personalized_ablation_file = fullfile( ...
    results_folder, ...
    'Personalized_Feature_Ablation.mat');

if ~isfile(personalized_ablation_file)

    error( ...
        'Personalized Feature Ablation file not found:\n%s', ...
        personalized_ablation_file);

end

load(personalized_ablation_file);

% Rename immediately
PersonalizedComparison = ComparisonTable;

%% =========================================================
% 4. LOAD FINAL CALIBRATED DETECTOR RESULTS
% ==========================================================

final_results_file = fullfile( ...
    results_folder, ...
    'FINAL_Stress_Detector_Results.mat');

if ~isfile(final_results_file)

    error( ...
        'Final detector results file not found:\n%s', ...
        final_results_file);

end

load(final_results_file);

%% =========================================================
% 5. LOAD SUBJECT-WISE PERFORMANCE
% ==========================================================

subject_file = fullfile( ...
    results_folder, ...
    'FINAL_Subject_Stress_Performance.csv');

if ~isfile(subject_file)

    error( ...
        'Subject performance file not found:\n%s', ...
        subject_file);

end

SubjectSummary = readtable(subject_file);

%% =========================================================
% 6. FINAL FEATURE GROUP COMPARISON FIGURE
% ==========================================================

figure;

bar(FeatureGroupComparison.Accuracy);

xlabel('Feature Group');

ylabel('LOSO Accuracy (%)');

title('Feature Group Comparison');

xticks(1:height(FeatureGroupComparison));

xticklabels(FeatureGroupComparison.Model);

grid on;

saveas(gcf, fullfile( ...
    figures_folder, ...
    'FINAL_Feature_Group_Comparison.png'));

%% =========================================================
% 7. PERSONALIZED FEATURE ABLATION FIGURE
% ==========================================================

figure;

bar(PersonalizedComparison.Accuracy);

xlabel('Model');

ylabel('Accuracy (%)');

title('Personalized Feature Ablation');

xticks(1:height(PersonalizedComparison));

xticklabels(PersonalizedComparison.Model);

grid on;

saveas(gcf, fullfile( ...
    figures_folder, ...
    'FINAL_Personalized_Feature_Ablation.png'));

%% =========================================================
% 8. SUBJECT-WISE STRESS DETECTION FIGURE
% ==========================================================

figure;

bar(SubjectSummary.DetectionRate);

xlabel('Subject');

ylabel('Stress Detection Rate (%)');

title('Subject-Wise Stress Detection Performance');

xticks(1:height(SubjectSummary));

xticklabels(SubjectSummary.Subject);

ylim([0 110]);

grid on;

saveas(gcf, fullfile( ...
    figures_folder, ...
    'FINAL_Subject_Stress_Detection.png'));

%% =========================================================
% 9. FINAL CALIBRATED DETECTION SUMMARY
% ==========================================================

total_stress = sum( ...
    FinalPredictions.TrueLabel == 1);

detected_stress = sum( ...
    FinalPredictions.PredictedLabel == 1);

missed_stress = ...
    total_stress - detected_stress;

final_recall = ...
    detected_stress / max(total_stress, 1);

%% =========================================================
% 10. FINAL SUMMARY TABLE
% ==========================================================

Metric = {
    'Total Subjects'
    'Total Feature Windows'
    'Baseline Windows'
    'Stress Windows'
    'Detected Stress Windows'
    'Missed Stress Windows'
    'Stress Recall'
    'Locked Threshold'
    };

Value = [
    height(SubjectSummary)
    445
    285
    total_stress
    detected_stress
    missed_stress
    final_recall * 100
    threshold
    ];

FinalSummary = table( ...
    string(Metric), ...
    Value, ...
    'VariableNames', ...
    {'Metric','Value'});

%% Display

fprintf('\n============================================\n');
fprintf('FINAL PROJECT SUMMARY\n');
fprintf('============================================\n');

disp(FinalSummary);

%% =========================================================
% 11. DEVELOPMENT MODEL COMPARISON
% ==========================================================

Experiment = {
    'HR-only LOSO'
    '4-feature LOSO'
    '13-feature LOSO'
    'Personalized binary LOSO'
    };

Accuracy = [
    77.08
    80.90
    81.57
    92.36
    ];

F1 = [
    64.34
    70.59
    73.03
    89.03
    ];

DevelopmentTable = table( ...
    string(Experiment), ...
    Accuracy, ...
    F1, ...
    'VariableNames', ...
    {'Experiment','Accuracy','F1'});

fprintf('\n============================================\n');
fprintf('DEVELOPMENT MODEL COMPARISON\n');
fprintf('============================================\n');

disp(DevelopmentTable);

%% =========================================================
% 12. DISPLAY FEATURE GROUP RESULTS
% ==========================================================

fprintf('\n============================================\n');
fprintf('FEATURE GROUP RESULTS\n');
fprintf('============================================\n');

disp(FeatureGroupComparison);

%% =========================================================
% 13. DISPLAY PERSONALIZED ABLATION RESULTS
% ==========================================================

fprintf('\n============================================\n');
fprintf('PERSONALIZED FEATURE ABLATION RESULTS\n');
fprintf('============================================\n');

disp(PersonalizedComparison);

%% =========================================================
% 14. SAVE FINAL TABLES
% ==========================================================

summary_file = fullfile( ...
    results_folder, ...
    'FINAL_Project_Summary.csv');

development_file = fullfile( ...
    results_folder, ...
    'FINAL_Development_Model_Comparison.csv');

writetable( ...
    FinalSummary, ...
    summary_file);

writetable( ...
    DevelopmentTable, ...
    development_file);

%% =========================================================
% 15. SAVE COMPLETE MATLAB RESULTS PACKAGE
% ==========================================================

final_package = fullfile( ...
    results_folder, ...
    'FINAL_Project_Results.mat');

save( ...
    final_package, ...
    'FinalSummary', ...
    'DevelopmentTable', ...
    'FeatureGroupComparison', ...
    'PersonalizedComparison', ...
    'SubjectSummary');

%% =========================================================
% 16. FINAL OUTPUT
% ==========================================================

fprintf('\n============================================\n');
fprintf('FINAL RESULTS PACKAGE CREATED\n');
fprintf('============================================\n');

fprintf('\nSummary:\n%s\n', ...
    summary_file);

fprintf('\nModel comparison:\n%s\n', ...
    development_file);

fprintf('\nMATLAB package:\n%s\n', ...
    final_package);

fprintf('\nFigures saved in:\n%s\n', ...
    figures_folder);

fprintf('\n============================================\n');
fprintf('DONE\n');
fprintf('============================================\n');