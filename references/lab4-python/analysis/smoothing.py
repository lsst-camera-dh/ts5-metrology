import numpy
from lsst.acquisition import data

def laplacian(d, numpoints=10):
    """
    Smoothing by nearest-neighbor averaging.
    
    See Google for more information on "Laplacian smoothing".
    """
    xy = d.points.reshape((-1, 2))
    xnew = xy[:,0].copy()
    ynew = xy[:,1].copy()
    znew = d.z.copy()
    for index, pt in enumerate(xy):
        dists = numpy.sum((xy-pt)**2, axis=-1)
        closest = []
        for i in range(numpoints):
            imin = numpy.argmin(dists)
            closest.append(imin)
            dists[imin] = numpy.inf
        xnew[index] = numpy.average(xy[:,0][closest])
        ynew[index] = numpy.average(xy[:,1][closest])
        znew[index] = numpy.average(d.data["z"][closest])
    return data.Data(numpy.column_stack([xnew, ynew]), z=znew)
