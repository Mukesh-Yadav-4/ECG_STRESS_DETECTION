clear;
clc;
close all;

%% =========================================================
% WESAD FEATURE ABLATION / COMPARISON
% Leave-One-Subject-Out Logistic Regression
% ==========================================================

%% Project paths

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
results_folder = fullfile(project_root, 'results');

%% Load dataset

load(fullfile(results_folder, 'WESAD_HRV_features.mat'));

Subject = string(HRV_Table.Subject);
Condition = string(HRV_Table.Condition);

%% Target
% Baseline = 0
% Stress   = 1

y = double(Condition == "Stress");

%% Complete feature matrix

X_all = [ ...
    HRV_Table.MeanHR, ...
    HRV_Table.SDNN * 1000, ...
    HRV_Table.RMSSD * 1000, ...
    HRV_Table.pNN50];

feature_sets = {
    [1], ...
    [1 2], ...
    [1 3], ...
    [1 4], ...
    [1 2 3 4]
};

model_names = {
    'HR only'
    'HR + SDNN'
    'HR + RMSSD'
    'HR + pNN50'
    'All features'
};

subjects = unique(Subject);
nSubjects = length(subjects);

%% Logistic regression parameters

learning_rate = 0.05;
iterations = 3000;

%% Result storage

results = zeros(length(feature_sets), 6);

%% =========================================================
% RUN EACH FEATURE SET
% ==========================================================

for m = 1:length(feature_sets)

    feature_idx = feature_sets{m};

    X = X_all(:, feature_idx);

    fprintf('\n============================================\n');
    fprintf('%s\n', model_names{m});
    fprintf('============================================\n');

    all_true = [];
    all_pred = [];

    %% LOSO

    for s = 1:nSubjects

        test_subject = subjects(s);

        test_mask = Subject == test_subject;
        train_mask = ~test_mask;

        X_train = X(train_mask,:);
        X_test  = X(test_mask,:);

        y_train = y(train_mask);
        y_test  = y(test_mask);

        %% Normalize using training subject data only

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

        %% Logistic regression

        for iter = 1:iterations

            z = X_train * w;

            % Numerical safety
            z = max(min(z,50),-50);

            p = 1 ./ (1 + exp(-z));

            gradient = ...
                (X_train' * (p - y_train)) / size(X_train,1);

            w = w - learning_rate * gradient;

        end

        %% Test

        z = X_test * w;

        z = max(min(z,50),-50);

        probability = 1 ./ (1 + exp(-z));

        prediction = probability >= 0.5;

        all_true = [all_true; y_test];
        all_pred = [all_pred; double(prediction)];

    end

    %% =====================================================
    % Metrics
    % ======================================================

    TP = sum(all_true == 1 & all_pred == 1);
    TN = sum(all_true == 0 & all_pred == 0);
    FP = sum(all_true == 0 & all_pred == 1);
    FN = sum(all_true == 1 & all_pred == 0);

    accuracy = (TP + TN) / ...
        (TP + TN + FP + FN);

    precision = TP / max(TP + FP, eps);

    recall = TP / max(TP + FN, eps);

    specificity = TN / max(TN + FP, eps);

    F1 = 2 * precision * recall / ...
        max(precision + recall, eps);

    results(m,:) = [ ...
        accuracy ...
        precision ...
        recall ...
        specificity ...
        F1 ...
        TP];

    fprintf('Accuracy    : %.2f %%\n', accuracy*100);
    fprintf('Precision   : %.2f %%\n', precision*100);
    fprintf('Recall      : %.2f %%\n', recall*100);
    fprintf('Specificity : %.2f %%\n', specificity*100);
    fprintf('F1-score    : %.2f %%\n', F1*100);

end

%% =========================================================
% DISPLAY COMPARISON
% ==========================================================

ComparisonTable = table( ...
    model_names, ...
    results(:,1)*100, ...
    results(:,2)*100, ...
    results(:,3)*100, ...
    results(:,4)*100, ...
    results(:,5)*100, ...
    'VariableNames', { ...
    'Model', ...
    'Accuracy', ...
    'Precision', ...
    'Recall', ...
    'Specificity', ...
    'F1'});

fprintf('\n============================================\n');
fprintf('FEATURE SET COMPARISON\n');
fprintf('============================================\n');

disp(ComparisonTable);

%% =========================================================
% Plot F1 score
% ==========================================================

figure;

bar(results(:,5)*100);

xlabel('Feature set');
ylabel('F1-score (%)');

title('Feature Set Comparison - F1 Score');

xticks(1:length(model_names));
xticklabels(model_names);

grid on;

%% Plot Accuracy

figure;

bar(results(:,1)*100);

xlabel('Feature set');
ylabel('Accuracy (%)');

title('Feature Set Comparison - Accuracy');

xticks(1:length(model_names));
xticklabels(model_names);

grid on;

%% Save

writetable( ...
    ComparisonTable, ...
    fullfile(results_folder, ...
    'Feature_Set_Comparison.csv'));

save( ...
    fullfile(results_folder, ...
    'Feature_Set_Comparison.mat'), ...
    'ComparisonTable');

fprintf('\nComparison results saved.\n');