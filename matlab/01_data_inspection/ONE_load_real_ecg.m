clear;
clc;
close all;

%% File location
project_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));

filename = fullfile( ...
    project_root, ...
    'data', ...
    'raw', ...
    'WESAD', ...
    'S2', ...
    'S2_respiban.txt');

%% ECG settings
Fs = 700;              % Sampling frequency
duration = 30;         % Seconds to load
N = Fs * duration;     % Number of samples

%% Open file
fid = fopen(filename, 'r');

if fid == -1
    error('Could not open the file.');
end

%% Skip the three header lines
fgetl(fid);
fgetl(fid);
fgetl(fid);

%% Read first N rows
data = textscan(fid, ...
    '%f %f %f %f %f %f %f %f %f %f', ...
    N, ...
    'Delimiter', {' ', '\t'}, ...
    'MultipleDelimsAsOne', true);

fclose(fid);

%% Extract ECG
ecg = data{3};         % CH1 = ECG

%% Create time vector
t = (0:length(ecg)-1) / Fs;

%% Display basic information
fprintf('Sampling frequency: %d Hz\n', Fs);
fprintf('Samples loaded: %d\n', length(ecg));
fprintf('Duration: %.2f seconds\n', length(ecg)/Fs);

%% Plot raw ECG
figure;

plot(t, ecg);

xlabel('Time (seconds)');
ylabel('ECG amplitude');

title('WESAD S2 - Raw ECG (First 30 Seconds)');

grid on;


%% Remove DC offset

ecg_centered = ecg - mean(ecg);

%% Plot centered ECG

figure;

plot(t, ecg_centered);

xlabel('Time (seconds)');
ylabel('Amplitude');

title('WESAD S2 - ECG After DC Offset Removal');

grid on;

%% Band-pass filter

low_cutoff = 0.5;
high_cutoff = 40;

[b, a] = butter(4, ...
    [low_cutoff high_cutoff] / (Fs/2), ...
    'bandpass');

ecg_filtered = filtfilt(b, a, ecg_centered);

%% Plot filtered ECG

figure;

plot(t, ecg_filtered);

xlabel('Time (seconds)');
ylabel('Amplitude');

title('WESAD S2 - Filtered ECG');

grid on;

%% Compare raw and filtered ECG

figure;

subplot(2,1,1);
plot(t, ecg);
xlabel('Time (seconds)');
ylabel('Amplitude');
title('Raw ECG');
grid on;

subplot(2,1,2);
plot(t, ecg_filtered);
xlabel('Time (seconds)');
ylabel('Amplitude');
title('Filtered ECG');
grid on;

%% R-peak detection

% Minimum distance between heartbeats
minPeakDistance = round(0.4 * Fs);

% Detect positive ECG peaks
[peakValues, peakLocations] = findpeaks( ...
    ecg_filtered, ...
    'MinPeakDistance', minPeakDistance, ...
    'MinPeakProminence', 3000);

% Convert sample locations to time
peakTimes = peakLocations / Fs;

%% Plot ECG with detected R-peaks

figure;

plot(t, ecg_filtered);
hold on;

plot(peakTimes, peakValues, 'ro');

xlabel('Time (seconds)');
ylabel('Amplitude');

title('WESAD S2 - R-Peak Detection');

legend('Filtered ECG', 'Detected R-peaks');

grid on;


%% Calculate RR intervals

RR = diff(peakTimes);          % seconds between consecutive R-peaks

% Heart rate from each RR interval
HR = 60 ./ RR;

%% Display results

fprintf('\nNumber of detected R-peaks: %d\n', length(peakTimes));
fprintf('Mean RR interval: %.4f seconds\n', mean(RR));
fprintf('Mean heart rate: %.2f BPM\n', mean(HR));

%% Plot RR intervals

figure;

plot(peakTimes(2:end), RR, 'o-');

xlabel('Time (seconds)');
ylabel('RR interval (seconds)');

title('WESAD S2 - RR Intervals');

grid on;

%% Plot instantaneous heart rate

figure;

plot(peakTimes(2:end), HR, 'o-');

xlabel('Time (seconds)');
ylabel('Heart Rate (BPM)');

title('WESAD S2 - Instantaneous Heart Rate');

grid on;
