import pandas as pd
import numpy as np
import peakutils
from scipy import signal
from scipy.interpolate import UnivariateSpline
from scipy.stats import moment


class Separation:
    """
    Data frame will always hold the raw data and filtered data will not be updated to it.
    """
    row_id = 0

    def __init__(self, dataframe: pd.DataFrame):
        self.data = dataframe
        self.rfu = self.get_raw_rfu()
        self.time = self.data.time.values
        self.current = self.data.current.values
        self.voltage = self.data.voltage.values
        self.peaks = {}
        self.id = self.row_id
        self.data['id'] = self.id
        self.row_id += 1

    def get_raw_rfu(self):
        """
        Returns the raw RFU from the data frame (no background, no filtering)
        :return:
        """
        return self.data.rfu.values


class Peak:
    """
    Created from a separation
    """

    def __init__(self, separation: Separation, start_time: float, stop_time: float, name="pk"):
        """
        Creates a peak from a separation object.

        :param separation: Separation that the peak resides in
        :param start_time: where to start the peak (seconds)
        :param stop_time: where to stop the peak (seconds)
        :param name: peaks name
        """

        self.start = start_time
        self.stop = stop_time
        self.separation = separation
        self.name = name

    def get_peak_region(self):
        """retrieve portion of the electropherogram that correspond to where we selected widths on the graph
        :return : returns [ peak_rfu, peak_time]
        """
        start_idx, stop_idx = self.get_indices(self.separation.time, self.start, self.stop)
        return [self.separation.rfu[start_idx:stop_idx], self.separation.time[start_idx:stop_idx]]

    @staticmethod
    def get_indices(time, value1, value2):
        """ returns the incices from two coordinate values from the time array"""
        dt = time[1] - time[0]
        start_idx = time.index(round(value1 / dt) * dt)
        stop_idx = time.index(round(value2 / dt) * dt)
        return [start_idx, stop_idx]


def background_median(separation: Separation, percentile=30):
    """
    Returns the user sepcified percentile background subtracted electropherogram
    :param separation: Separation object
    :param percentile: which percentile to use for background
    :return: (rfu, baseline)
    :rtype: tuple
    """
    lower_median = np.percentile(separation.rfu, percentile=percentile)
    rfu = np.subtract(separation.rfu, lower_median)

    return rfu, [lower_median] * len(rfu)


def background_poly(separation: Separation, poly_order=3, skip_start=0, skip_end=0):
    """
    Calculates a polynomial fit of the electropherogram
    :param separation: separation to analyze
    :param poly_order: polynomial order to use for the background
    :param skip_start: number of points to skip at start of separation
    :param skip_end: number of points to skip at the end of the separation
    :return: rfu_adjusted background, baseline
    :rtype: tuple
    """
    # If polynomial is too large GigaCE freezes, this is a catch to prevent freezing
    assert poly_order < 10, "Poly Order to Large, please select reasonable polynomial"
    assert skip_end >= 0 and skip_start >= 0, "Skip parameters must be greater than 0"

    if skip_end == 0:
        skip_end_neg = None
    else:
        skip_end_neg = -skip_end

    base = peakutils.baseline(np.array(separation.rfu[skip_start:skip_end_neg]), poly_order)
    x_total = np.linspace(0, len(base) + skip_start + skip_end, len(base) + skip_end + skip_start)
    fit = np.polyfit(x_total[skip_start:skip_end_neg], base, poly_order)
    p = np.poly1d(fit)
    base = p(x_total)
    baseline = list(base)
    return np.subtract(separation.rfu, baseline), baseline


def filter_butter(separation: Separation, cutoff: float, order: int):
    """
    Butterworth digital filter, applies the filter forwards and backwards so the end result
    won't have a phase shift. Order will be multiplied by 2 (once for each pass of the filter).

    :param separation: Separation to filter
    :param cutoff: Digital filter cutoff
    :param order: Order for the single pass of the filter
    :return: filtered RFu
    """

    # Filtering Functions
    # noinspection PyTupleAssignmentBalance
    def butter_lowpass():
        nyq = 0.5 * dt
        normal_cutoff = cutoff / nyq
        b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
        return b, a

    dt = 1 / np.median(np.diff(separation.time))
    b, a = butter_lowpass()
    rfu_filtered = signal.filtfilt(b, a, separation.rfu, padlen=24, padtype='constant')

    return rfu_filtered


def filter_savgol(separation: Separation, window_size: int, poly_order: int):
    """
    Performs a savintsky-golay filter of the dataset, applying a gaussian window of the specified size across
    the dataset.

    :param separation:
    :param window_size: must be odd number, size of window
    :param poly_order:  Polynomial to apply for fit
    :return:
    """

    mode = 'mirror'
    return signal.savgol_filter(separation.rfu, window_size, poly_order, mode=mode)


def peak_corrected_area(peak, gram):
    """
     Area needs to be corrected or normalized for diffent mobilities
        CA = A * velocity
        CA = A * Ldetector / retention time or
        CA = A / retention time, this cant be compared between instruments.
        Integrates the peak area using a trapezoidal approximation.
    :param peak: Peak to be analyzed
    :return: corrected area
    """

    #m1, _, _, _ = peak_moments(peak)
    area = peak_area(peak, gram)
    corrected_area = area / peak['m1']
    return corrected_area


def peak_area(peak, gram):
    """
    Peak area provided by integrating using trapezoidal approximation
    :param peak: Peak to be integrated
    :return: area of the peak
    :rtype: float
    """
    peak_rfu, peak_time = get_peak_portions(peak, gram)
    area = np.trapz(peak_rfu, peak_time)
    return area


def peak_moments(peak, gram):
    """
    Returns the first four statistical moments of the peak.
    :param peak: Peak to analyze
    :return : m1, m2, m3, m4
    :rtype : tuple
    """
    peak_rfu, peak_time = get_peak_portions(peak, gram)
    # Get the First moment, or tr
    rn3 = np.multiply(peak_rfu, peak_time)
    m1 = sum(rn3) / sum(peak_rfu)

    # get the second moment
    rn3 = np.multiply(((peak_time - m1) ** 2), peak_rfu)
    m2 = np.sum(rn3) / np.sum(peak_rfu)

    # get the third moment
    rn3 = np.multiply(((peak_time - m1) ** 3), peak_rfu)
    m3 = np.sum(rn3) / np.sum(peak_rfu)

    # get the fourth moment
    rn3 = np.multiply(((peak_time - m1) ** 4), peak_rfu)
    m4 = np.sum(rn3) / np.sum(peak_rfu)

    return m1, m2, m3, m4


def peak_max(peak: Peak):
    """
    Returns the maximum signal of the peak
    :param peak:
    :return: max
    :rtype : float
    """
    peak_rfu, _ = peak.get_peak_region()
    return max(peak_rfu)


def peak_max_time(peak: Peak):
    """
    Returns the time where the peak is at max height
    :param peak:
    :return:
    """
    peak_rfu, peak_time = peak.get_peak_region()
    tr = peak_time[peak_rfu.index(max(peak_rfu))]
    return tr

def get_indices(peak_time, value1, value2):
    """ returns the incices from two coordinate values from the time array"""
    peak_time = list(peak_time)
    dt = np.median(np.diff(peak_time))
    value1 *= dt
    value2 *= dt
    start_idx = (np.abs(peak_time - value1)).argmin()
    stop_idx = (np.abs(peak_time - value2)).argmin()
    return start_idx, stop_idx, value1, value2

def get_peak_portions(peak, gram):
    peak_rfu = gram['rfu'].values[peak['start_idx']:peak['stop_idx']]
    peak_time = gram['time'].values[peak['start_idx']:peak['stop_idx']]
    return peak_rfu, peak_time

def peak_fwhm(peak, gram):
    """
    Returns the full width half max of the peak.
    Calculates FWHM using a 3rd degree spline of the peak and determining the width at exactly 1/2 of the max signal.
    :param peak: Peak to analzye
    :return: full width half max
    :rtype : float
    """
    peak_rfu, peak_time = get_peak_portions(peak, gram)
    maxrfu = max(peak_rfu)
    halfmax = maxrfu / 2
    # create a spline of x and blue-np.max(blue)/2
    spline = UnivariateSpline(np.asarray(peak_time), np.subtract(peak_rfu, halfmax), s=0)
    # find the roots
    roots = spline.roots()
    # if we don't have our peaks separated all the way and cant reach half max
    if len(roots) < 2:
        r2 = peak_time[-1]
        r1 = peak_time[0]
    else:
        r2 = roots[-1]
        r1 = roots[0]
        if r2 < peak_time[peak_rfu.index(maxrfu)]:
            r2 = peak_time[-1]
        if r1 > peak_time[peak_rfu.index(maxrfu)]:
            r1 = peak_time[0]
    fwhm = np.abs(r2 - r1)
    return fwhm


def peak_noise(separation: Separation, skip_start=0, noise_length=30):
    """
    Determines the flattest portion of the electropherogram and uses that to calculate noise. Noise is
    calculated as the standard deviation of 30 points.

    :param separation: separation to find noise
    :param noise_length: number of points to use to calculate noise
    :param skip_start_points: portion of e_gram at the start to ignore
    :return: noise
    """
    max_noise = 1E8  # set default noise to ridiculous value
    max_avg = 1
    max_indx = [0, skip_start]
    for i in range(5, len(separation.rfu) - skip_start):
        noise_st = i
        noise_end = noise_st + skip_start
        noise = np.std(separation.rfu[noise_st:noise_end])
        if max_noise > noise != 0:
            max_noise = noise
            max_indx = [noise_st, noise_end]
            max_avg = np.mean(separation.rfu[noise_st:noise_end])
    noise = max_noise
    noise_st, noise_end = max_indx
    return noise, max_avg, noise_st, noise_end


def peak_snr(peak: Peak):
    """
    Max signal (baseline corrected) divided by the noise RMS of the chromatogram (portion defined by user)
    :param peak: Peak to analyze
    :return:  Signal to Noise ratio
    :rtype: float
    """
    peak_rfu, peak_time = peak.get_peak_region()
    sig = max(peak_rfu)
    noise, _, _, _ = peak_noise(peak.separation)
    # return s/n calculation
    return sig / noise
