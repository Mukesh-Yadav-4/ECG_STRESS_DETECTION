function result = process_ecg_window(ecg_window, Fs)
% PROCESS_ECG_WINDOW Preprocesses an ECG window and extracts HR/HRV features.
%
% Inputs:
%   ecg_window - 1D array containing raw ECG amplitude samples
%   Fs         - Sampling frequency in Hz (e.g. 700 Hz for WESAD RespiBAN)
%
% Outputs:
%   result     - Struct containing filtered signal, peak indices, and extracted features

    ecg_window = double(ecg_window(:));
    Fs = double(Fs);

    % 1. Bandpass filter (0.5 - 40 Hz Butterworth) to eliminate DC baseline wander & HF noise
    [b, a] = butter(4, [0.5, 40] / (Fs / 2), 'bandpass');
    filtered_ecg = filtfilt(b, a, ecg_window);

    % 2. Adaptive peak threshold via Median Absolute Deviation (MAD)
    noise_level = 1.4826 * median(abs(filtered_ecg - median(filtered_ecg)));
    min_prominence = 3.0 * noise_level;

    % 3. QRS R-peak detection (refractory period >= 350 ms)
    [peak_values, peak_locations] = findpeaks(filtered_ecg, ...
        'MinPeakDistance', round(0.35 * Fs), ...
        'MinPeakProminence', min_prominence);

    peak_times = (peak_locations - 1) / Fs;
    RR = diff(peak_times);

    % 4. Physiological interval filtering (300 ms - 1500 ms / 40 - 200 BPM)
    valid_mask = (RR >= 0.30 & RR <= 1.50);
    RR_clean = RR(valid_mask);

    % 5. Data sufficiency check
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

    % 6. Heart rate calculation
    HR = 60 ./ RR_clean;

    % 7. Time-domain HRV feature extraction
    diff_RR = diff(RR_clean);
    SDNN = std(RR_clean);
    RMSSD = sqrt(mean(diff_RR .^ 2));
    pNN50 = 100 * sum(abs(diff_RR) > 0.050) / numel(diff_RR);
    mean_RR = mean(RR_clean);

    % Robust dispersion metrics (IQR)
    RR_sorted = sort(RR_clean);
    RR_IQR = RR_sorted(max(1, round(0.75 * numel(RR_sorted)))) - ...
             RR_sorted(max(1, round(0.25 * numel(RR_sorted))));

    HR_sorted = sort(HR);
    HR_IQR = HR_sorted(max(1, round(0.75 * numel(HR_sorted)))) - ...
             HR_sorted(max(1, round(0.25 * numel(HR_sorted))));

    % 8. Package results
    result.valid = true;
    result.filtered_ecg = filtered_ecg;
    result.peak_locations = peak_locations;
    result.peak_values = peak_values;
    result.peak_times = peak_times;
    result.RR = RR;
    result.RR_clean = RR_clean;
    result.HR = HR;

    result.MeanHR = mean(HR);
    result.MedianHR = median(HR);
    result.StdHR = std(HR);
    result.MinHR = min(HR);
    result.MaxHR = max(HR);

    result.MeanRR = mean_RR;
    result.MedianRR = median(RR_clean);
    result.SDNN = SDNN;
    result.RMSSD = RMSSD;
    result.pNN50 = pNN50;
    result.RR_CV = SDNN / mean_RR;
    result.RR_IQR = RR_IQR;
    result.HR_IQR = HR_IQR;
end