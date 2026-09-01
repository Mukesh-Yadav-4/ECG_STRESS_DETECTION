clear;
clc;
close all;

%% =========================================================
% WESAD FEATURE-GROUP ABLATION
%
% Purpose:
% Determine which groups of ECG/HRV features contribute
% to subject-independent stress classification.
%
% Validation:
% Leave-One-Subject-Out (LOSO)
%
% Classifier:
% Logistic regression implemented using base MATLAB
% ==========================================================

%% =========================================================
% 1. PROJECT PATHS
% ==========================================================

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));

results_folder = fullfile(project_root, 'results');

%% =========================================================
% 2. LOAD EXPANDED DATASET
% ==========================================================

feature_file = fullfile( ...
    results_folder, ...
    'WESAD_HRV_features_expanded.mat');

if ~isfile(feature_file)
    error('Expanded feature file not found:\n%s', feature_file);
end

load(feature_file);

%% =========================================================
% 3. DATA PREPARATION
% ==========================================================

Subject = string(HRV_Table.Subject);
Condition = string(HRV_Table.Condition);

% Baseline = 0
% Stress   = 1
y = double(Condition == "Stress");

%% =========================================================
% 4. FEATURE MATRIX
% ==========================================================

% Feature columns:
%
% 1  MeanHR
% 2  MedianHR
% 3  StdHR
% 4  MinHR
% 5  MaxHR
% 6  MeanRR
% 7  MedianRR
% 8  SDNN
% 9  RMSSD
% 10 pNN50
% 11 RR_CV
% 12 RR_IQR
% 13 HR_IQR

X_all = [ ...
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

%% =========================================================
% 5. DEFINE FEATURE GROUPS
% ==========================================================

feature_sets = {

    [1], ...
    
    [1 2 3 4 5], ...
    
    [6 7 8 9 10], ...
    
    [11 12 13], ...
    
    [1 2 3 4 5 6 7 8 9 10], ...
    
    [1 2 3 4 5 6 7 8 9 10 11 12 13]

};

model_names = {

    'Mean HR only'
    
    'HR statistics'
    
    'Classical HRV'
    
    'Distribution features'
    
    'HR + Classical HRV'
    
    'All 13 features'

};

%% =========================================================
% 6. CLASSIFIER SETTINGS
% ==========================================================

learning_rate = 0.05;
iterations = 3000;

%% =========================================================
% 7. SUBJECT LIST
% ==========================================================

subjects = unique(Subject);

nSubjects = length(subjects);

%% =========================================================
% 8. STORAGE
% ==========================================================

comparison_results = zeros( ...
    length(feature_sets), 7);

%% =========================================================
% 9. RUN FEATURE-GROUP EXPERIMENT
% ==========================================================

for m = 1:length(feature_sets)

    feature_idx = feature_sets{m};

    X = X_all(:, feature_idx);

    fprintf('\n============================================\n');
    fprintf('%s\n', model_names{m});
    fprintf('============================================\n');

    %% Prediction storage

    all_true = [];
    all_pred = [];

    %% -----------------------------------------------------
    % Leave-One-Subject-Out
    % ------------------------------------------------------

    for s = 1:nSubjects

        test_subject = subjects(s);

        test_mask = Subject == test_subject;
        train_mask = ~test_mask;

        X_train = X(train_mask,:);
        X_test  = X(test_mask,:);

        y_train = y(train_mask);
        y_test  = y(test_mask);

        %% -------------------------------------------------
        % Standardize using training subjects ONLY
        % --------------------------------------------------

        mu = mean(X_train,1);
        sigma = std(X_train,0,1);

        sigma(sigma == 0) = 1;

        X_train = ...
            (X_train - mu) ./ sigma;

        X_test = ...
            (X_test - mu) ./ sigma;

        %% -------------------------------------------------
        % Add intercept
        % --------------------------------------------------

        X_train = ...
            [ones(size(X_train,1),1) X_train];

        X_test = ...
            [ones(size(X_test,1),1) X_test];

        %% -------------------------------------------------
        % Initialize weights
        % --------------------------------------------------

        w = zeros(size(X_train,2),1);

        %% -------------------------------------------------
        % Logistic regression
        % --------------------------------------------------

        for iter = 1:iterations

            z = X_train * w;

            % Numerical protection
            z = max(min(z,50),-50);

            p = 1 ./ (1 + exp(-z));

            gradient = ...
                (X_train' * (p - y_train)) ...
                / size(X_train,1);

            w = w - learning_rate * gradient;

        end

        %% -------------------------------------------------
        % Predict test subject
        % --------------------------------------------------

        z = X_test * w;

        z = max(min(z,50),-50);

        probability = ...
            1 ./ (1 + exp(-z));

        prediction = probability >= 0.5;

        %% Store

        all_true = [all_true; y_test];

        all_pred = [ ...
            all_pred;
            double(prediction)];

    end

    %% =====================================================
    % PERFORMANCE
    % ======================================================

    TP = sum(all_true == 1 & all_pred == 1);
    TN = sum(all_true == 0 & all_pred == 0);
    FP = sum(all_true == 0 & all_pred == 1);
    FN = sum(all_true == 1 & all_pred == 0);

    accuracy = ...
        (TP + TN) / ...
        (TP + TN + FP + FN);

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

    %% Store

    comparison_results(m,:) = [ ...
        accuracy, ...
        precision, ...
        recall, ...
        specificity, ...
        F1, ...
        balanced_accuracy, ...
        length(feature_idx)];

    fprintf('Accuracy          : %.2f %%\n', ...
        accuracy*100);

    fprintf('Precision         : %.2f %%\n', ...
        precision*100);

    fprintf('Recall            : %.2f %%\n', ...
        recall*100);

    fprintf('Specificity       : %.2f %%\n', ...
        specificity*100);

    fprintf('F1-score          : %.2f %%\n', ...
        F1*100);

    fprintf('Balanced Accuracy : %.2f %%\n', ...
        balanced_accuracy*100);

end

%% =========================================================
% 10. CREATE COMPARISON TABLE
% ==========================================================

ComparisonTable = table( ...
    string(model_names(:)), ...
    comparison_results(:,1)*100, ...
    comparison_results(:,2)*100, ...
    comparison_results(:,3)*100, ...
    comparison_results(:,4)*100, ...
    comparison_results(:,5)*100, ...
    comparison_results(:,6)*100, ...
    comparison_results(:,7), ...
    'VariableNames', { ...
    'Model', ...
    'Accuracy', ...
    'Precision', ...
    'Recall', ...
    'Specificity', ...
    'F1', ...
    'BalancedAccuracy', ...
    'NumberOfFeatures'});

%% =========================================================
% 11. DISPLAY
% ==========================================================

fprintf('\n============================================\n');
fprintf('FEATURE GROUP COMPARISON\n');
fprintf('============================================\n');

disp(ComparisonTable);

%% =========================================================
% 12. F1 PLOT
% ==========================================================

figure;

bar(comparison_results(:,5)*100);

xlabel('Feature group');

ylabel('F1-score (%)');

title('Feature Group Comparison - F1 Score');

xticks(1:length(model_names));

xticklabels(model_names);

grid on;

%% =========================================================
% 13. ACCURACY PLOT
% ==========================================================

figure;

bar(comparison_results(:,1)*100);

xlabel('Feature group');

ylabel('Accuracy (%)');

title('Feature Group Comparison - Accuracy');

xticks(1:length(model_names));

xticklabels(model_names);

grid on;

%% =========================================================
% 14. SAVE RESULTS
% ==========================================================

writetable( ...
    ComparisonTable, ...
    fullfile(results_folder, ...
    'Feature_Group_Comparison.csv'));

save( ...
    fullfile(results_folder, ...
    'Feature_Group_Comparison.mat'), ...
    'ComparisonTable');

fprintf('\nFeature-group analysis completed.\n');
fprintf('Results saved to:\n');
fprintf('%s\n', fullfile(results_folder, ...
    'Feature_Group_Comparison.csv'));

fprintf('%s\n', fullfile(results_folder, ...
    'Feature_Group_Comparison.mat'));