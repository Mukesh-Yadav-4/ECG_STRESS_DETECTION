clear;
clc;
close all;

%% =========================================================
% FINAL ECG STRESS DETECTION PROJECT DASHBOARD
% ==========================================================

matlab_root = fileparts(mfilename('fullpath'));
project_root = fileparts(matlab_root);

results_folder = fullfile(project_root,'results');
figures_folder = fullfile(results_folder,'figures');

if ~exist(figures_folder,'dir')
    mkdir(figures_folder);
end

%% =========================================================
% LOAD RESULTS
% ==========================================================

FeatureGroup = readtable(fullfile( ...
    results_folder,'Feature_Group_Comparison.csv'));

Personalized = readtable(fullfile( ...
    results_folder,'Personalized_Feature_Ablation.csv'));

Subject = readtable(fullfile( ...
    results_folder,'FINAL_Subject_Stress_Performance.csv'));

ROC = readtable(fullfile( ...
    results_folder,'Personalized_ROC.csv'));

FPR = ROC.FalsePositiveRate;
TPR = ROC.TruePositiveRate;

AUC = trapz(FPR,TPR);

%% =========================================================
% FINAL VALUES
% ==========================================================

accuracy = 92.36;
precision = 92.00;
recall = 86.25;
specificity = 95.79;
F1 = 89.03;
balanced_accuracy = 91.02;

threshold = 0.35;

TP = 138;
TN = 273;
FP = 12;
FN = 22;

%% =========================================================
% CREATE FIGURE
% ==========================================================

fig = figure( ...
    'Color','white', ...
    'Position',[50 50 1700 1050], ...
    'Name','ECG Stress Detection - Final Dashboard');

%% =========================================================
% TITLE
% ==========================================================

annotation( ...
    fig, ...
    'textbox',[0.10 0.945 0.80 0.035], ...
    'String','ECG Stress Detection using WESAD', ...
    'EdgeColor','none', ...
    'HorizontalAlignment','center', ...
    'FontSize',24, ...
    'FontWeight','bold', ...
    'Color','black');

annotation( ...
    fig, ...
    'textbox',[0.10 0.915 0.80 0.025], ...
    'String','Personalized HR/HRV Features • Logistic Regression • LOSO Validation', ...
    'EdgeColor','none', ...
    'HorizontalAlignment','center', ...
    'FontSize',13, ...
    'Color',[0.25 0.25 0.25]);

%% =========================================================
% LAYOUT
% ==========================================================

t = tiledlayout(fig,2,3, ...
    'TileSpacing','compact', ...
    'Padding','loose');

%% =========================================================
% 1. MODEL DEVELOPMENT
% ==========================================================

ax1 = nexttile(t);

model_names = { ...
    'HR only'
    '4 features'
    '13 features'
    'Personalized'};

model_accuracy = [
    77.08
    80.90
    81.57
    92.36];

b1 = bar(ax1,model_accuracy);

b1.FaceColor = [0.20 0.45 0.75];

title(ax1,'Model Development', ...
    'FontSize',16, ...
    'FontWeight','bold');

ylabel(ax1,'Accuracy (%)');

xticks(ax1,1:4);
xticklabels(ax1,model_names);

ylim(ax1,[0 100]);

grid(ax1,'on');

set(ax1, ...
    'FontSize',10, ...
    'Box','off', ...
    'Color','white', ...
    'XColor','black', ...
    'YColor','black');

for i = 1:4

    text( ...
        ax1, ...
        i, ...
        model_accuracy(i)+2, ...
        sprintf('%.1f%%',model_accuracy(i)), ...
        'HorizontalAlignment','center', ...
        'FontWeight','bold', ...
        'FontSize',11);

end

%% =========================================================
% 2. PERSONALIZED FEATURE ABLATION
% ==========================================================

ax2 = nexttile(t);

ablation_values = [
    Personalized.Accuracy, ...
    Personalized.F1];

b2 = bar(ax2,ablation_values,'grouped');

b2(1).FaceColor = [0.20 0.45 0.75];
b2(2).FaceColor = [0.85 0.45 0.20];

title(ax2,'Personalized Feature Ablation', ...
    'FontSize',16, ...
    'FontWeight','bold');

ylabel(ax2,'Performance (%)');

xticks(ax2,1:height(Personalized));

xticklabels(ax2,Personalized.Model);

xtickangle(ax2,35);

ylim(ax2,[0 100]);

legend( ...
    ax2, ...
    b2, ...
    {'Accuracy','F1-score'}, ...
    'Location','southoutside', ...
    'Orientation','horizontal');

grid(ax2,'on');

set(ax2, ...
    'FontSize',8, ...
    'Box','off', ...
    'Color','white', ...
    'XColor','black', ...
    'YColor','black');

%% =========================================================
% 3. SUBJECT PERFORMANCE
% ==========================================================

ax3 = nexttile(t);

b3 = bar(ax3,Subject.DetectionRate);

b3.FaceColor = [0.20 0.60 0.45];

hold(ax3,'on');

yline( ...
    recall, ...
    '--', ...
    'LineWidth',1.5, ...
    'HandleVisibility','off');

title(ax3,'Stress Detection Across Subjects', ...
    'FontSize',16, ...
    'FontWeight','bold');

ylabel(ax3,'Detection Rate (%)');

xticks(ax3,1:height(Subject));

xticklabels(ax3,Subject.Subject);

ylim(ax3,[0 110]);

grid(ax3,'on');

set(ax3, ...
    'FontSize',9, ...
    'Box','off', ...
    'Color','white', ...
    'XColor','black', ...
    'YColor','black');

for i = 1:height(Subject)

    text( ...
        ax3, ...
        b3.XEndPoints(i), ...
        Subject.DetectionRate(i)+3, ...
        sprintf('%.0f%%',Subject.DetectionRate(i)), ...
        'HorizontalAlignment','center', ...
        'FontSize',8, ...
        'FontWeight','bold');

end

%% =========================================================
% 4. CONFUSION MATRIX
% ==========================================================

ax4 = nexttile(t);

CM = [
    TN FP
    FN TP];

imagesc(ax4,CM);

axis(ax4,'equal');
axis(ax4,'tight');

xticks(ax4,[1 2]);
yticks(ax4,[1 2]);

xticklabels(ax4,{'Baseline','Stress'});
yticklabels(ax4,{'Baseline','Stress'});

xlabel(ax4,'Predicted');
ylabel(ax4,'Actual');

title(ax4,'Final Confusion Matrix', ...
    'FontSize',16, ...
    'FontWeight','bold');

set(ax4, ...
    'FontSize',10, ...
    'Box','off', ...
    'Color','white', ...
    'XColor','black', ...
    'YColor','black');

colorbar(ax4);

for r = 1:2
    for c = 1:2

        text( ...
            ax4, ...
            c, ...
            r, ...
            sprintf('%d',CM(r,c)), ...
            'HorizontalAlignment','center', ...
            'FontSize',20, ...
            'FontWeight','bold', ...
            'Color','white');

    end
end

%% =========================================================
% 5. ROC CURVE
% ==========================================================

ax5 = nexttile(t);

plot( ...
    ax5, ...
    FPR, ...
    TPR, ...
    'LineWidth',2.5, ...
    'Color',[0.15 0.45 0.85]);

hold(ax5,'on');

plot( ...
    ax5, ...
    [0 1], ...
    [0 1], ...
    '--', ...
    'Color',[0.5 0.5 0.5], ...
    'LineWidth',1.2);

title( ...
    ax5, ...
    sprintf('ROC Curve (AUC = %.4f)',AUC), ...
    'FontSize',16, ...
    'FontWeight','bold');

xlabel(ax5,'False Positive Rate');
ylabel(ax5,'True Positive Rate');

xlim(ax5,[0 1]);
ylim(ax5,[0 1]);

legend( ...
    ax5, ...
    {'ROC Curve','Chance'}, ...
    'Location','southeast');

grid(ax5,'on');

set(ax5, ...
    'FontSize',10, ...
    'Box','off', ...
    'Color','white', ...
    'XColor','black', ...
    'YColor','black');

%% =========================================================
% 6. FINAL RESULTS PANEL
% ==========================================================

ax6 = nexttile(t);

axis(ax6,'off');

title( ...
    ax6, ...
    'Final Model Performance', ...
    'FontSize',16, ...
    'FontWeight','bold');

results_text = {
    sprintf('Accuracy              %.2f%%',accuracy)
    sprintf('Precision             %.2f%%',precision)
    sprintf('Recall / Sensitivity  %.2f%%',recall)
    sprintf('Specificity           %.2f%%',specificity)
    sprintf('F1-score              %.2f%%',F1)
    sprintf('Balanced Accuracy     %.2f%%',balanced_accuracy)
    sprintf('ROC-AUC               %.4f',AUC)
    ''
    sprintf('Decision threshold    %.2f',threshold)
    sprintf('Stress detected       %d / 160',TP)
    sprintf('Subjects              15')
    sprintf('60-sec windows        445')
    };

text( ...
    ax6, ...
    0.04, ...
    0.90, ...
    results_text, ...
    'Units','normalized', ...
    'VerticalAlignment','top', ...
    'FontSize',12, ...
    'FontName','Consolas', ...
    'Color','black');

%% =========================================================
% SAVE
% ==========================================================

dashboard_file = fullfile( ...
    figures_folder, ...
    'FINAL_Project_Dashboard.png');

exportgraphics( ...
    fig, ...
    dashboard_file, ...
    'Resolution',200);

fprintf('\n============================================\n');
fprintf('FINAL PROJECT DASHBOARD CREATED\n');
fprintf('============================================\n');

fprintf('\nSaved to:\n%s\n',dashboard_file);

fprintf('\nFinal metrics:\n');
fprintf('Accuracy          : %.2f %%\n',accuracy);
fprintf('Precision         : %.2f %%\n',precision);
fprintf('Recall            : %.2f %%\n',recall);
fprintf('Specificity       : %.2f %%\n',specificity);
fprintf('F1-score          : %.2f %%\n',F1);
fprintf('Balanced Accuracy : %.2f %%\n',balanced_accuracy);
fprintf('ROC-AUC           : %.4f\n',AUC);

fprintf('\nDONE\n');