clear;
clc;
close all;

%% Load WESAD S2 ECG and labels

project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));

data_file = fullfile( ...
    project_root, ...
    'data', ...
    'processed', ...
    'S2_ECG_labels.mat');

load(data_file);

%% Basic information

fprintf('Sampling frequency: %d Hz\n', Fs);
fprintf('Number of ECG samples: %d\n', length(ecg));
fprintf('Number of labels: %d\n', length(labels));
fprintf('Recording duration: %.2f minutes\n', length(ecg)/Fs/60);

%% Find unique labels and their number of samples

uniqueLabels = unique(labels);

fprintf('\nLabel distribution:\n');

for i = 1:length(uniqueLabels)

    currentLabel = uniqueLabels(i);
    count = sum(labels == currentLabel);

    fprintf('Label %d: %d samples (%.2f%%)\n', ...
        currentLabel, ...
        count, ...
        100 * count / length(labels));

end

%% Create time vector

t = (0:length(labels)-1) / double(Fs);

%% Create time vector

t = (0:length(labels)-1) / double(Fs);

%% Plot labels over time

figure;

stairs(t/60, labels, 'LineWidth', 1);

xlabel('Time (minutes)');
ylabel('WESAD Label');

title('WESAD S2 - Label Timeline');

yticks([0 1 2 3 4 6 7]);
ylim([-0.5 7.5]);

grid on;
