from numpy import *
from scipy.stats import gaussian_kde
from scipy.optimize import fmin, fminbound

def totals(pixels, n=2):
    """Find the sums of all n-by-n boxes in pixels.
    
    The return array is smaller than pixels by (n-1) in
    the two final dimensions."""
    totals = zeros(concatenate([pixels.shape[:-2],
                                array(pixels.shape[-2:])-n+1]))
    slices = [slice(i, (1-n+i if i<n-1 else None)) for i in range(n)]
    for x in slices:
        for y in slices:
            totals += pixels[...,x,y]
    return totals

def maxima(totals, n=2):
    """Find totals that are higher than all other totals within an n-by-n box.
    
    The return array has the same shape as totals."""
    good = ones(totals.shape, dtype=bool)
    slices = [slice(i if i>0 else 0, i if i<0 else None) for i in range(1-n, n)]
    for x, xp in zip(slices, reversed(slices)):
        for y, yp in zip(slices, reversed(slices)):
            good[...,x,y] &= totals[...,xp,yp] <= totals[...,x,y]
    return good

def k_alpha(totals, maxima, guess):
    """Use an optimization routine to locate the k-alpha peak.
    
    Returns a tuple (a,b), where a is k-alpha and b is the
    distance from the k-alpha peak to the minimum between the
    alpha and beta peaks."""
    sums = totals[maxima]
    k = gaussian_kde(sums[abs(sums - guess) < .2*guess])
    #Find the top of the alpha peak
    k_alpha = asscalar(fmin(lambda x: -k(x), guess, disp=0))
    #Find the minimum between the alpha and beta peaks
    k_alpha_min = asscalar(fminbound(k, k_alpha, k_alpha*1.07))
    return k_alpha, (k_alpha_min - k_alpha)

def boxes(places, pixels, n=2):
    ix = array(where(places))[...,None,None]
    return pixels[tuple(ix + mgrid[:n,:n][:,None])]

