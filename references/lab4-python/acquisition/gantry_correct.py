from numpy import argsort, sum, square
from lsst.analysis import utils

class GantryCorrector:
    def __init__(self, data=None): self.data = data
    def error(self, pt):
        if self.data is None: return 0.
        xy, z = self.data.points.reshape((-1, 2)), self.data.data['z'].ravel()
        closest = argsort(sum(square(xy - pt), axis=-1))[:3]
        plane = utils.fitplane(xy[closest], z[closest])
        return utils.evalplane(plane, pt)
