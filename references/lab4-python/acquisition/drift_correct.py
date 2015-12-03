import numpy
from scipy.interpolate import splrep, splev
from lsst.analysis import utils

class DriftCorrector:
    def __init__(self, xy=numpy.empty((0,2)), reps=0):
        """Create a drift corrector object."""
        self.xy, self.reps = xy, reps
        self.t = numpy.empty((self.reps, len(self.xy)))
        self.z = numpy.empty((self.reps, len(self.xy)))
        self.count = 0
        self.splines = None
    
    def cycle(self, func):
        """Measure one complete cycle of the drift correction points.
        
        'func' is a function that accepts a parameter 'pt' and returns
        the time and z-value as measured at 'pt'."""
        for index, point in enumerate(self.xy):
            self.t[self.count, index], self.z[self.count, index] = func(point)
        self.count += 1
        if self.count == self.reps:
            self.count == 0
            self.calc()
    
    def calc(self):
        """Calculate the position-over-time splines.

        This function is called internally after all data has been
        acquired.  It is never called if reps=0."""
        planes = numpy.empty((self.reps, 3))
        for i in xrange(self.reps):
            planes[i] = utils.fitplane(self.xy, self.z[i])
        avgtimes = numpy.average(self.t, axis=1)
        self.splines = [splrep(avgtimes, planes[:,n]) for n in range(3)]
    
    def error(self, t, pt):
        """Return the error due to drift at time 't' and point 'pt'."""
        return (utils.evalplane([splev(t, spl) for spl in self.splines], pt)
                if self.splines else 0)
    
    def apply(self, data):
        """Apply this correction profile to 'data'."""
        for index in data:
            data.z[index] -= self.error(data.t[index], data.xy[index])
