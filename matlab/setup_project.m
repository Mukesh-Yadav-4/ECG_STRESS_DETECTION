% setup_project.m
% Initializes paths for the WESAD ECG Stress Detection MATLAB pipeline.

matlab_root = fileparts(mfilename('fullpath'));
project_root = fileparts(matlab_root);

% Add all project subdirectories to search path
addpath(genpath(matlab_root));

fprintf('=== ECG Stress Detection Pipeline Initialized ===\n');
fprintf('Project root: %s\n', project_root);
fprintf('MATLAB paths added successfully.\n\n');
