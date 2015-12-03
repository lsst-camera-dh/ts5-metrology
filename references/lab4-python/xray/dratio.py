from numpy import *
from utils import *
from scipy.stats import gaussian_kde
from scipy.special import erf, erfinv
from scipy.optimize import fmin

def dratio(boxes):
    pairs = concatenate([sum(boxes,1), sum(boxes,2)])
    return abs(subtract.reduce(pairs,1) / sum(pairs,1))

def sigma_max(dratio):
    #Units of pixels
    k = gaussian_kde(dratio)
    peak = asscalar(fmin(lambda x: -k(x), 1., disp=0))
    return 1 / (erfinv(peak)*sqrt(8))

def sigma_min(dratio):
    #Tricky - this is actually a lower bound on sigma_max
    #Units of pixels
    k = gaussian_kde(concatenate([dratio, -dratio]))
    return asscalar(k(0))

def dratio_sim(x, sigma):
    return erf(x / (sigma*sqrt(2)))

class Image:
    def __init__(self, pixels, ka_guess=505.):
        self.pixels = pixels
        self.totals = totals(self.pixels)
        self.maxima = maxima(self.totals)
        self.k_alpha = k_alpha(self.totals, self.maxima, ka_guess)
        self.good = ((abs(self.totals - self.k_alpha[0]) < self.k_alpha[1])
                     & self.maxima)
        self.boxes = boxes(self.good, self.pixels)
        self.dratio = dratio(self.boxes)
        self.sigma_max = sigma_max(self.dratio)
        self.sigma_min = sigma_min(self.dratio)
    def __repr__(self):
        return ("Image of shape {0}\n".format(self.pixels.shape) +
                ("k_alpha peak at {0[0]} with tolerance {0[1]}\n"
                 .format(self.k_alpha)) +
                "{0} usable events found\n".format(self.good.sum()) +
                ("sigma_max is between {0} and {1}\n"
                 .format(self.sigma_min, self.sigma_max)))
