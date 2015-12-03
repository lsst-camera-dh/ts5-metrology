import numpy
from scipy.interpolate import bisplrep, bisplev

def fitplane(xy, z):
    """
    Calculate the best fit plane to a set of data.
    
    xy is an array of shape (m, 2).
    z is an array of shape (m,).
    The return value is a tuple (a, b, c) satisfying z=a*xy[:,0]+b*xy[:,1]+c.
    """
    pts = xy.reshape((-1, 2))
    return numpy.linalg.lstsq(numpy.column_stack([pts, numpy.ones(len(pts))]),
                                                 z.ravel())[0]

def evalplane(abc, xy):
    """
    Evaluate the plane given by coefficients abc at a point or array
    of points xy.
    """
    xy = numpy.array(xy) #Allows us to use fancy slicing even if xy is a list
    return abc[0]*xy[...,0] + abc[1]*xy[...,1] + abc[2]

def fitspline(xy, z, smoothing=None):
    """
    Return a tuple (t, c, k) describing the spline as described in the
    Numpy documentation.
    """
    return bisplrep(xy[...,0].ravel(), xy[...,1].ravel(), z.ravel(),
                    s=smoothing)

def evalspline(spline, xy):
    return numpy.apply_along_axis(lambda pt: bisplev(pt[0], pt[1], spline),
                                  len(xy.shape) - 1, xy)
