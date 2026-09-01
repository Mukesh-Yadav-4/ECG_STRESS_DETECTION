clear;
clc;
close all;

%% Data from SEVEN_extract_hrv

baseline_HR = [81.716 70.929 75.761 72.396 74.146];
stress_HR   = [83.253 79.534 77.945 83.716 74.948];

baseline_SDNN = [0.11324 0.074361 0.095967 0.051419 0.098092];
stress_SDNN   = [0.073625 0.073358 0.078651 0.091105 0.1141];

baseline_RMSSD = [0.07544 0.052618 0.08727 0.05383 0.092787];
stress_RMSSD   = [0.067307 0.047263 0.034785 0.092325 0.077099];

baseline_pNN50 = [26.58 31.88 43.24 38.03 36.11];
stress_pNN50   = [18.52 23.08 13.16 14.63 23.29];

window = 1:5;

%% Plot Mean HR

figure;

plot(window, baseline_HR, 'o-');
hold on;
plot(window, stress_HR, 'o-');

xlabel('60-second window');
ylabel('Heart Rate (BPM)');
title('S2 Mean Heart Rate: Baseline vs Stress');

legend('Baseline','Stress');

grid on;

%% Plot SDNN

figure;

plot(window, baseline_SDNN*1000, 'o-');
hold on;
plot(window, stress_SDNN*1000, 'o-');

xlabel('60-second window');
ylabel('SDNN (ms)');
title('S2 SDNN: Baseline vs Stress');

legend('Baseline','Stress');

grid on;

%% Plot RMSSD

figure;

plot(window, baseline_RMSSD*1000, 'o-');
hold on;
plot(window, stress_RMSSD*1000, 'o-');

xlabel('60-second window');
ylabel('RMSSD (ms)');
title('S2 RMSSD: Baseline vs Stress');

legend('Baseline','Stress');

grid on;

%% Plot pNN50

figure;

plot(window, baseline_pNN50, 'o-');
hold on;
plot(window, stress_pNN50, 'o-');

xlabel('60-second window');
ylabel('pNN50 (%)');
title('S2 pNN50: Baseline vs Stress');

legend('Baseline','Stress');

grid on;