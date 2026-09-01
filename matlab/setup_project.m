%% =========================================================
% ECG STRESS DETECTION - PROJECT SETUP
% ==========================================================

% Determine the MATLAB folder containing this script
matlab_root = fileparts(mfilename('fullpath'));

% Project root is one level above the MATLAB folder
project_root = fileparts(matlab_root);

% Add all MATLAB subfolders to the MATLAB path
addpath(genpath(matlab_root));

% Display confirmation
fprintf('\n============================================\n');
fprintf('ECG STRESS DETECTION PROJECT SETUP\n');
fprintf('============================================\n');

fprintf('Project root:\n%s\n\n', project_root);

fprintf('MATLAB root:\n%s\n\n', matlab_root);

fprintf('MATLAB subfolders added to path.\n');
fprintf('Project setup complete.\n');
