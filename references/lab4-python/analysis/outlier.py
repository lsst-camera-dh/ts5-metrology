import numpy
from lsst.analysis import utils

"""
Detection algorithm:
  for every point, select the X closest
  if current point is sufficiently far from local median, throw it out
"""

def valid(d, ix=None, numpoints=10, std_tol=1.5):
    ix = numpy.ones(d.shape, dtype='bool') if ix is None else ix
    valid = numpy.ones(d.shape, dtype='bool')
    max_dev = std_tol * numpy.std(d.z)
    for i in d:
        dists = numpy.where(ix,
                            numpy.sum((d.points-d.points[i])**2, axis=-1),
                            numpy.inf)                
        closest = []
        for j in range(numpoints):
            imin = numpy.argmin(dists)
            closest.append(imin)
            dists[imin] = numpy.inf
        valid[i] = abs(numpy.median(d.z[closest]) - d.z[i]) < max_dev
    return valid
