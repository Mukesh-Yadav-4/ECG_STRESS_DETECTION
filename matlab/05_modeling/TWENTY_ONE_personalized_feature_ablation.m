clear;
clc;
close all;

%% =========================================================
% PERSONALIZED FEATURE ABLATION
% Leave-One-Subject-Out Logistic Regression
% =========================================================

%% Project paths

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
results_folder = fullfile(project_root, 'results');

%% Load expanded dataset

feature_file = fullfile( ...
    results_folder, ...
    'WESAD_HRV_features_expanded.mat');

load(feature_file);

%% Basic variables

Subject = string(HRV_Table.Subject);
Condition = string(HRV_Table.Condition);

y = double(Condition == "Stress");

subjects = unique(Subject);
nSubjects = length(subjects);

%% =========================================================
% RAW FEATURE MATRIX
% ==========================================================

% Columns:
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

X = [ ...
    HRV_Table.MeanHR, ...
    HRV_Table.MedianHR, ...
    HRV_Table.StdHR, ...
    HRV_Table.MinHR, ...
    HRV_Table.MaxHR, ...
    HRV_Table.MeanRR * 1000, ...
    HRV_Table.MedianRR * 1000, ...
    HRV_Table.SDNN * 1000, ...
    HRV_Table.RMSSD * 1000, ...
    HRV_Table.pNN50, ...
    HRV_Table.RR_CV, ...
    HRV_Table.RR_IQR * 1000, ...
    HRV_Table.HR_IQR];

%% =========================================================
% FEATURE SETS
% ==========================================================

feature_sets = {

    [1]
    
    [1 8]
    
    [1 9]
    
    [1 10]
    
    [1 8 9 10]
    
    [1 8 9 10 11 12 13]
    
    [1 2 3 4 5 6 7 8 9 10 11 12 13]

};

model_names = {

    'Delta HR only'
    
    'Delta HR + Delta SDNN'
    
    'Delta HR + Delta RMSSD'
    
    'Delta HR + Delta pNN50'
    
    'Delta HR + Classical HRV'
    
    'Delta HR + HRV distribution'
    
    'All personalized features'

};

%% =========================================================
% LOGISTIC REGRESSION SETTINGS
% ==========================================================

learning_rate = 0.05;
iterations = 3000;

%% =========================================================
% RESULT STORAGE
% ==========================================================

comparison_results = zeros(length(feature_sets),7);

%% =========================================================
% RUN ABLATION
% ==========================================================

for m = 1:length(feature_sets)

    feature_idx = feature_sets{m};

    fprintf('\n============================================\n');
    fprintf('%s\n', model_names{m});
    fprintf('============================================\n');

    all_true = [];
    all_pred = [];

    %% -----------------------------------------------------
    % LOSO
    % ------------------------------------------------------

    for s = 1:nSubjects

        test_subject = subjects(s);

        test_mask = Subject == test_subject;
        train_mask = ~test_mask;

        X_train_raw = X(train_mask,:);
        X_test_raw  = X(test_mask,:);

        y_train = y(train_mask);
        y_test  = y(test_mask);

        subject_train = Subject(train_mask);
        condition_train = Condition(train_mask);

        %% -------------------------------------------------
        % Build personalized features for training subjects
        % -------------------------------------------------

        X_train_personalized = zeros(size(X_train_raw));

        training_subjects = unique(subject_train);

        for j = 1:length(training_subjects)

            current_subject = training_subjects(j);

            idx_subject = ...
                subject_train == current_subject;

            idx_baseline = ...
                idx_subject & condition_train == "Baseline";

            baseline_mean = ...
                mean(X_train_raw(idx_baseline,:),1);

            baseline_mean(abs(baseline_mean) < eps) = eps;

            X_train_personalized(idx_subject,:) = ...
                (X_train_raw(idx_subject,:) - baseline_mean) ...
                ./ abs(baseline_mean);

        end

        %% -------------------------------------------------
        % Personalized features for TEST subject
        % -------------------------------------------------

        test_condition = Condition(test_mask);

        baseline_test = ...
            X_test_raw(test_condition == "Baseline",:);

        test_baseline_mean = mean(baseline_test,1);

        test_baseline_mean(abs(test_baseline_mean) < eps) = eps;

        X_test_personalized = ...
            (X_test_raw - test_baseline_mean) ...
            ./ abs(test_baseline_mean);

        %% Select feature subset

        X_train_personalized = ...
            X_train_personalized(:,feature_idx);

        X_test_personalized = ...
            X_test_personalized(:,feature_idx);

        %% -------------------------------------------------
        % Standardize using TRAINING data only
        % -------------------------------------------------

        mu = mean(X_train_personalized,1);
        sigma = std(X_train_personalized,0,1);

        sigma(sigma == 0) = 1;

        X_train_personalized = ...
            (X_train_personalized - mu) ./ sigma;

        X_test_personalized = ...
            (X_test_personalized - mu) ./ sigma;

        %% Add intercept

        X_train_aug = ...
            [ones(size(X_train_personalized,1),1), ...
             X_train_personalized];

        X_test_aug = ...
            [ones(size(X_test_personalized,1),1), ...
             X_test_personalized];

        %% -------------------------------------------------
        % Train logistic regression
        % -------------------------------------------------

        w = zeros(size(X_train_aug,2),1);

        for iter = 1:iterations

            z = X_train_aug * w;

            z = max(min(z,50),-50);

            probability = ...
                1 ./ (1 + exp(-z));

            gradient = ...
                (X_train_aug' * ...
                (probability-y_train)) ...
                / size(X_train_aug,1);

            w = w - learning_rate * gradient;

        end

        %% -------------------------------------------------
        % Test
        % -------------------------------------------------

        z = X_test_aug * w;

        z = max(min(z,50),-50);

        probability = ...
            1 ./ (1 + exp(-z));

        prediction = probability >= 0.5;

        all_true = [all_true; y_test];

        all_pred = ...
            [all_pred; double(prediction)];

    end

    %% =====================================================
    % METRICS
    % ======================================================

    TP = sum(all_true == 1 & all_pred == 1);
    TN = sum(all_true == 0 & all_pred == 0);
    FP = sum(all_true == 0 & all_pred == 1);
    FN = sum(all_true == 1 & all_pred == 0);

    accuracy = ...
        (TP+TN) / ...
        (TP+TN+FP+FN);

    precision = ...
        TP / max(TP+FP,eps);

    recall = ...
        TP / max(TP+FN,eps);

    specificity = ...
        TN / max(TN+FP,eps);

    F1 = ...
        2*precision*recall / ...
        max(precision+recall,eps);

    balanced_accuracy = ...
        (recall+specificity)/2;

    comparison_results(m,:) = [
        accuracy
        precision
        recall
        specificity
        F1
        balanced_accuracy
        length(feature_idx)
    ];

    fprintf('Accuracy          : %.2f %%\n', accuracy*100);
    fprintf('Precision         : %.2f %%\n', precision*100);
    fprintf('Recall            : %.2f %%\n', recall*100);
    fprintf('Specificity       : %.2f %%\n', specificity*100);
    fprintf('F1-score          : %.2f %%\n', F1*100);
    fprintf('Balanced Accuracy : %.2f %%\n', balanced_accuracy*100);

end

%% =========================================================
% COMPARISON TABLE
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

fprintf('\n============================================\n');
fprintf('PERSONALIZED FEATURE ABLATION\n');
fprintf('============================================\n');

disp(ComparisonTable);

%% =========================================================
% PLOTS
% ==========================================================

figure;

bar(comparison_results(:,5)*100);

xlabel('Feature set');
ylabel('F1-score (%)');

title('Personalized Feature Comparison - F1');

xticks(1:length(model_names));
xticklabels(model_names);

grid on;


figure;

bar(comparison_results(:,6)*100);

xlabel('Feature set');
ylabel('Balanced accuracy (%)');

title('Personalized Feature Comparison - Balanced Accuracy');

xticks(1:length(model_names));
xticklabels(model_names);

grid on;

%% =========================================================
% SAVE
% ==========================================================

writetable( ...
    ComparisonTable, ...
    fullfile(results_folder, ...
    'Personalized_Feature_Ablation.csv'));

save( ...
    fullfile(results_folder, ...
    'Personalized_Feature_Ablation.mat'), ...
    'ComparisonTable');

fprintf('\nPersonalized feature ablation complete.\n');