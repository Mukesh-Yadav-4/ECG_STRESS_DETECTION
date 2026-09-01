function result = process_ecg_window(ecg_window, Fs)
%PROCESS_ECG_WINDOW Process one ECG window and extract HR/HRV features.

    %% Input preparation
    ecg_window = double(ecg_window(:));
    Fs = double(Fs);

    %% 1. Band-pass filtering
    low_cutoff = 0.5;
    high_cutoff = 40;

    [b, a] = butter(4, ...
        [low_cutoff high_cutoff] / (Fs/2), ...
        'bandpass');

    filtered_ecg = filtfilt(b, a, ecg_window);

    %% 2. Adaptive peak threshold
    noise_level = 1.4826 * ...
        median(abs(filtered_ecg - median(filtered_ecg)));

    min_prominence = 3 * noise_level;

    %% 3. R-peak detection
    [peak_values, peak_locations] = findpeaks( ...
        filtered_ecg, ...
        'MinPeakDistance', round(0.35 * Fs), ...
        'MinPeakProminence', min_prominence);

    %% 4. Peak times
    peak_times = (peak_locations - 1) / Fs;

    %% 5. RR intervals
    RR = diff(peak_times);

    %% 6. Basic RR quality control
    valid = RR >= 0.30 & RR <= 1.50;

    RR_clean = RR(valid);

    %% 7. Minimum-data check
    if numel(RR_clean) < 5

        result.valid = false;

        result.filtered_ecg = filtered_ecg;
        result.peak_locations = peak_locations;
        result.peak_values = peak_values;
        result.peak_times = peak_times;

        result.RR = RR;
        result.RR_clean = RR_clean;

        result.MeanHR = NaN;
        result.MedianHR = NaN;
        result.StdHR = NaN;
        result.MinHR = NaN;
        result.MaxHR = NaN;

        result.MeanRR = NaN;
        result.MedianRR = NaN;
        result.SDNN = NaN;
        result.RMSSD = NaN;
        result.pNN50 = NaN;
        result.RR_CV = NaN;
        result.RR_IQR = NaN;
        result.HR_IQR = NaN;

        return;
    end

    %% 8. Heart-rate series
    HR = 60 ./ RR_clean;

    %% 9. HR features
    mean_HR = mean(HR);
    median_HR = median(HR);
    std_HR = std(HR);
    min_HR = min(HR);
    max_HR = max(HR);

    %% 10. RR features
    mean_RR = mean(RR_clean);
    median_RR = median(RR_clean);

    %% SDNN
    SDNN = std(RR_clean);

    %% RMSSD
    successive_diff = diff(RR_clean);

    RMSSD = sqrt(mean(successive_diff.^2));

    %% pNN50
    pNN50 = 100 * ...
        sum(abs(successive_diff) > 0.050) / ...
        numel(successive_diff);

    %% RR coefficient of variation
    RR_CV = SDNN / mean_RR;

    %% RR interquartile range
    RR_sorted = sort(RR_clean);

    Q1_RR = RR_sorted( ...
        max(1, round(0.25 * numel(RR_sorted))));

    Q3_RR = RR_sorted( ...
        max(1, round(0.75 * numel(RR_sorted))));

    RR_IQR = Q3_RR - Q1_RR;

    %% HR interquartile range
    HR_sorted = sort(HR);

    Q1_HR = HR_sorted( ...
        max(1, round(0.25 * numel(HR_sorted))));

    Q3_HR = HR_sorted( ...
        max(1, round(0.75 * numel(HR_sorted))));

    HR_IQR = Q3_HR - Q1_HR;

    %% 11. Return results

    result.valid = true;

    result.filtered_ecg = filtered_ecg;

    result.peak_locations = peak_locations;
    result.peak_values = peak_values;
    result.peak_times = peak_times;

    result.RR = RR;
    result.RR_clean = RR_clean;

    result.HR = HR;

    result.MeanHR = mean_HR;
    result.MedianHR = median_HR;
    result.StdHR = std_HR;
    result.MinHR = min_HR;
    result.MaxHR = max_HR;

    result.MeanRR = mean_RR;
    result.MedianRR = median_RR;
    result.SDNN = SDNN;
    result.RMSSD = RMSSD;
    result.pNN50 = pNN50;
    result.RR_CV = RR_CV;
    result.RR_IQR = RR_IQR;
    result.HR_IQR = HR_IQR;

end