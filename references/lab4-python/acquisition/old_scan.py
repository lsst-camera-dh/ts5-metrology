from __future__ import division

from lsst.drivers import a3200, keyence
from lsst.acquisition import drift_correct, gantry_correct
import numpy, time, sys

class Scan:
    def __init__(self, data, drift=drift_correct.DriftCorrector(),
                 gantry=gantry_correct.GantryCorrector()):
        """Create a scan object."""
        self.data, self.drift, self.gantry = data, drift, gantry
        self.dfreq = len(self.data) / (self.drift.reps - 1)
    
    def step(self, pt):
        """Measure one point and return (time, z-value)."""
        a3200.xymove(pt, velocity=600, blocking=True)
        z = keyence.measure(blocking=True)
        if self.gantry and z: z -= self.gantry.error(pt)
        return (time.time(), z if z else numpy.nan)
    
    def run(self):
        """Run this scan, including drift correction and gantry correction."""
        sys.stdout.write('00%')
        for num, index in enumerate(self.data):
            sys.stdout.write('\b\b\b{0:02d}%'.format(
                    (100*num)//len(self.data)))
            if num % self.dfreq < 1: self.drift.cycle(self.step)
            self.data.data['t'][index], self.data.data['z'][index] = \
                self.step(self.data.points[index])
        self.drift.cycle(self.step)
        sys.stdout.write('\b\b\b100%')
    
    def write(self, out):
        out.write(time.strftime('# Scan of {0} points'.format(len(self.data))
                                + ' from %Y-%m-%d at %H:%M:%S\n'))
        self.data.write(out)
