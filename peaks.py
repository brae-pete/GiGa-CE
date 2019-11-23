# -*- coding: utf-8 -*-
"""
Peak Calculations class
Created on Tue Jul 12 13:17:55 2016

@author: Alyssa
"""
import numpy as np
from scipy.interpolate import UnivariateSpline
import database as db
import peakutils


def noise_calc(rfu, time, coords):
    """ Calcualtes the noise from a  rfu array"""
    startind, stopind = get_indices(time, coords[0], coords[1])
    rms = np.std(rfu[startind:stopind])
    return rms


def get_indices(time, value1, value2):
    """ returns the incices from two coordinate values from the time array"""
    dt = time[1] - time[0]
    startind = time.index(round(value1 / dt) * dt)
    stopind = time.index(round(value2 / dt) * dt)
    return [startind, stopind]


class baseline():
    """Corrected baseline stored as correctedRFU calculated from correct
    If a separate method for baseline is needed to be called you can change
    the correct function, or add another method/function. Just call the function
    in the GUI to call you function.

    Additionally you can use lower_median which takes a value from a specified portion of the
    all the numbers sorted as the baseline. This method also corrects for negative
    y values. Preferential for UV analysis"""

    def __init__(self, rfu):
        self.rfu = rfu
        self.correctedrfu = []
        self.lower_median()

    def firstlast50(self, x=50):
        first = np.average(self.rfu[:x])
        last = np.average(self.rfu[-x:])
        self.linecalc(first, last)

    def lower_median(self, lower_value=0.2):
        try:
            sortedRfu = self.rfu[:]
            sortedRfu.sort()
            #print(sortedRfu[0:1], lower_value, len(sortedRfu) * lower_value)
            medianIndex = len(sortedRfu) * lower_value
            medianIndex = int(medianIndex)
            #print(type(medianIndex), "IS ", print(medianIndex))
            self.correctedrfu = [i - sortedRfu[medianIndex] for i in self.rfu]
            lowest_value = min(self.correctedrfu)

            if lowest_value < 0:
                #print("Correction")
                new_correctedrfu = [i - lowest_value for i in self.correctedrfu]
            #print("Finished", len(new_correctedrfu))
            self.correctedrfu = new_correctedrfu
            return new_correctedrfu
        except Exception as e:
            print("Did not correct baseline")
            print(str(e))

    def peakutils_baseline(self, polynomial, skip=0):
        """Requires corrected RFU to be run first"""

        # If polynomial is too large GigaCE freezes, this is a catch to prevent freezing
        if polynomial > 10:
            print("Polynomial too large")
            return self.correctedrfu

        base = peakutils.baseline(np.array(self.correctedrfu[skip:]), polynomial)
        #print(base)
        #print(len(base))
        Xtotal = np.linspace(0, len(base) + skip, len(base) + skip)
        #print(len(Xtotal))
        #print(Xtotal)
        fit = np.polyfit(Xtotal[skip:], base, polynomial)
        #print(fit)
        p = np.poly1d(fit)
        base = p(Xtotal)
        baseline = list(base)
        return baseline

    def peakutils_indexes(self, thresh=3, min_dist=1):
        self.peak_indexes = peakutils.indexes(self.rfu, thresh, min_dist)
        return self.peak_indexes

    def linecalc(self, y1, y2):
        xt = len(self.rfu)
        self.m = (y2 - y1) / xt
        self.b = y1

    def subtract(self, x, y):
        y1 = self.m * x + self.b
        return y - y1

    def correct(self):
        correctedrfu = []
        for x, y in enumerate(self.rfu):
            correctedrfu.append(self.subtract(x, y))
        return correctedrfu


class allpeakcalculations():
    """in contrst to peakcalculations, all peak calculations makes the changes
    directly to the database, thus it needs the run_id and a session object for
    SQLAlchemy"""

    def __init__(self, sep_id, session):
        self.sep_id = sep_id

        self.session = session
        self.calculate_mobility()
        self.calculate_twopeaks()

    def calculate_mobility(self):
        for instance in self.session.query(db.Peak).filter(db.Peak.run_id == self.sep_id,
                                                           db.Peak.active.isnot(False)). \
                order_by(db.Peak.m1):
            # Calculate mobility
            mobility = round(self.get_mobility(instance.m1), 6)
            instance.apparentmobility = mobility
            self.session.commit()

    def calculate_twopeaks(self):
        """Cycle through all peaks in a separation
        # for each peak calculate A %, CA %, Resolution (with the next peak), plates
        """
        First = True
        old_plates = 0

        Area, CArea = self.get_total()
        for instance in self.session.query(db.Peak).filter(db.Peak.run_id == self.sep_id,
                                                           db.Peak.active.isnot(False)). \
                order_by(db.Peak.m1):

            # Calculate area percents
            instance.areapercent = float(instance.area) / Area * 100
            instance.correctedpercent = float(instance.correctedarea) / CArea * 100
            # Calculate plates, replace old plates if new plates is greater
            new_plates = round(self.get_plates(float(instance.m1), float(instance.fwhm)), 2)
            instance.plates = new_plates
            # Calulate resolution, set new values
            new_m1 = instance.m1
            new_fwhm = instance.fwhm

            if not First:  # Requires at least 2 peaks
                resolution = self.get_resolution(old_m1, old_fwhm, new_m1, new_fwhm)
                resolution = self.get_resolution(old_m1, old_fwhm, new_m1, new_fwhm)
                old_instance.resolution = round(resolution, 2)
                instance.resolution = round(resolution,
                                            2)  # if this is the last peak, use resolution from previous peak
            # Set old values for next resolution calculation
            old_m1 = new_m1
            old_fwhm = new_fwhm
            old_instance = instance
            # Save all changes to the database
            self.session.commit()
            # make sure First is false, we've been here at least once
            First = False

    def get_plates(self, m1, fwhm):
        """Theoretical plates from Harris 8ed. (p552)"""
        P = 5.55 * (m1 ** 2) / (fwhm ** 2)
        return P

    def get_resolution(self, old_m1, old_fwhm, new_m1, new_fwhm):
        """Resolution from Harris 8ed. (p549)"""
        wavg = (old_fwhm + new_fwhm) / 2
        dtr = new_m1 - old_m1
        R = 0.589 * dtr / wavg
        return R

    def get_mobility(self, m1):
        """Apparent mobility from Weinberger 2ed. (p31)"""
        # Retrieve Values from database

        instance_separation = self.session.query(db.Separation).filter(db.Separation.id == self.sep_id)
        instance_separation = instance_separation.first()
        kwds = eval(instance_separation.kwds)
        try:
            V = eval(kwds["V"])
            Ld = eval(kwds["Ld"])
        except:
            print("USING DEFALUT: 15 kV and 20 cm distance to detector")
            V = 15
            Ld = 20
        try:

            Lt = eval(kwds["Lc"])
        except:
            print("USING DEFAULT: 30 cm Column Length")
            Lt = 30
        m1 = m1
        # Calculate
        uep = (Ld / m1) / (V / Lt)
        return uep

    def get_total(self):
        """Calculate the toatal AREA and Corrected AREA for all peaks in a separation"""
        area = 0
        carea = 0
        for instance in self.session.query(db.Peak).filter(db.Peak.run_id == self.sep_id, db.Peak.active.isnot(False)):
            area += float(instance.area)
            carea += float(instance.correctedarea)
        return area, carea


class peakcalculations():
    """ Requires time, rfu arrays and the start and stop values for the peak
    
    Need to account for RFU Baseline!"""

    def __init__(self, time, RFU, value1, value2, distance2detector=20, poly=False, skip=0):
        self.time = time
        self.rfu = RFU

        #print(self.rfu[0], "Before correction", len(self.rfu))
        new_baseline = baseline(self.rfu)
        self.rfu = new_baseline.correctedrfu
        #print(self.rfu[0], "After Correction", len(self.rfu))
        if poly != False:
            self.rfu = np.array(self.rfu)
            self.baseline = new_baseline.peakutils_baseline(poly, skip)
            self.rfu = list(self.rfu - self.baseline)
        self.rnrfu, self.rntime = self.getindexes(value1, value2)
        self.distance2detector = distance2detector
        self.start = value1
        self.stop = value2
        # if len(self.rnrfu)<1:
        #   print(time, "Time \n" , RFU, "RFU\n", value1,value2)

    # print(self.rnrfu)
    def peakutil_baseline(self, polynomial=3):
        self.rfu = np.array(self.rfu)
        self.baseline = peakutils.baseline(self.rfu, polynomial)
        return self.baseline

    def getindexes(self, value1, value2):
        # retrieve indexes that correspond to where we selected widths on the graph
        startind, stopind = get_indices(self.time, value1, value2)
        self.stopind = stopind  # use this for resolution helps
        self.startind = startind
        return [self.rfu[startind:stopind], self.time[startind:stopind]]

    def get_starttime(self):
        return self.start

    def get_stoptime(self):
        return self.stop

    def get_area(self):
        # Calculate area using a trapazoid approximation
        area = np.trapz(self.rnrfu, self.rntime)
        return area

    def get_m1(self):
        # Get the First moment, or tr
        rn3 = np.multiply(self.rnrfu, self.rntime)
        m1 = sum(rn3) / sum(self.rnrfu)
        return m1

    def get_m2(self):
        # get the second moment
        m1 = self.get_m1()
        rn3 = np.multiply(((self.rntime - m1) ** 2), self.rnrfu)
        m2 = np.sum(rn3) / np.sum(self.rnrfu)
        return m2

    def get_m3(self):
        # get the third moment
        m1 = self.get_m1()
        rn3 = np.multiply(((self.rntime - m1) ** 3), self.rnrfu)
        m3 = np.sum(rn3) / np.sum(self.rnrfu)
        return m3

    def get_m4(self):
        # get the fourth moment
        m1 = self.get_m1()
        rn3 = np.multiply(((self.rntime - m1) ** 4), self.rnrfu)
        m4 = np.sum(rn3) / np.sum(self.rnrfu)
        return m4

    def get_max(self):
        return max(self.rnrfu)

    def get_maxtime(self):
        # get the tr at Max height
        tr = self.rntime[self.rnrfu.index(max(self.rnrfu))]
        return tr

    def get_fwhm(self):
        """uses a 3rd degree smoothing spline to model the peak. All half max is subtracted from
        all the rfu data. """
        maxrfu = max(self.rnrfu)
        halfmax = maxrfu / 2
        # create a spline of x and blue-np.max(blue)/2 
        #print(len(self.rntime), len(self.rnrfu), len(np.subtract(self.rnrfu, halfmax)))
        spline = UnivariateSpline(np.asarray(self.rntime), np.subtract(self.rnrfu, halfmax), s=0)
        # find the roots
        roots = spline.roots()
        #print(len(roots))
        # if we don't have our peaks separated all the way and cant reach half max
        if len(roots) < 2:
            r2 = self.rntime[-1]
            r1 = self.rntime[0]

        else:
            r2 = roots[-1]
            r1 = roots[0]
            #print(r2, r1, "were r's", self.rntime[self.rnrfu.index(maxrfu)])
            if r2 < self.rntime[self.rnrfu.index(maxrfu)]:
                r2 = self.rntime[-1]
            if r1 > self.rntime[self.rnrfu.index(maxrfu)]:
                r1 = self.rntime[0]
        fwhm = np.abs(r2 - r1)
        #print(fwhm, " is the FWHM")
        self.spline = spline
        return fwhm

    def get_correctedarea(self):
        """ Area needs to be corrected or normalized for diffent mobilities
        CA = A * velocity
        CA = A * Ldetector / retention time or
        CA = A / retention time, this cant be compared between instruments
        """
        m1 = self.get_m1()
        area = self.get_area()
        correctedarea = area / m1
        print(correctedarea, " is the CA")
        return correctedarea

    def get_snr(self, noise):
        """
        Max signal (baseline corrected) divided by the noise RMS of the chromatogram (portion defined by user)
        :param noise: float noise RMS value
        :return: float Signal to Noise ratio
        """
        sig = max(self.rnrfu)
        # return s/n calculation
        return sig/noise

