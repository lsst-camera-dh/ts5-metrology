import numpy

def emptynan(shape):
    temp = numpy.empty(shape, dtype='float')
    temp[:] = numpy.nan
    return temp

def from_file(path):
    arr = numpy.loadtxt(path)
    return Data(arr[:,1:3], z= arr[:,3], t=arr[:,0])

def gantry_file(path):
    arr = numpy.loadtxt(path)
    return Data(arr[:,0:2], z= arr[:,2])

def raster_data(x, y, **kwargs):
    assert len(x.shape) == 1
    assert len(y.shape) == 1
    return Data(numpy.dstack(numpy.meshgrid(x, y)), **kwargs)

def tiled_data(tile_orig, points, **kwargs):
    assert len(tile_orig.shape) == 2
    assert tile_orig.shape[1] == 2
    assert points.shape[-1] == 2
    return Data(tile_orig + points[...,None,:],
                tiles=numpy.tile(numpy.arange(tile_orig.shape[0]),
                                 points.shape[:-1]+(1,)))

class Data:
    def __init__(self, points=numpy.empty((0,2)), tiles=None, z=None,
                 t=None, smartiter=True):
        """Create the necessary empty arrays to hold data.
        
        Parameter 'points' is an array with shape (..., 2).
        Parameter 'tiles' is an array with shape (...).
        """
        self.data = {}
        self.points = numpy.array(points)
        self.data["tiles"] = (numpy.zeros(self.shape, dtype='int') if tiles
                              is None else numpy.array(tiles, dtype='int'))
        self.data["z"] = emptynan(self.shape) if z is None else numpy.array(z)
        self.data["t"] = emptynan(self.shape) if t is None else numpy.array(t)
        self.smartiter = smartiter
        
        #Make sure everything looks reasonable
        assert self.points.shape[-1] == 2
        for obj in self.data:
            assert self.data[obj].shape == self.shape
    
    #Pythonic methods
    def __getattr__(self, name): # shortcuts to access time and z
        if name == "shape": return self.points.shape[:-1]
        elif name in ['z', 't']: return self.data[name]
        else: raise AttributeError, name
    def __setattr__(self, name, value):
        if name in ['z', 't']: self.data[name] = value
        else: self.__dict__[name] = value
    def __len__(self): return int(numpy.prod(self.shape))
    def __iter__(self):
        """Iterate over points in an approximately optimal order.
        
        Algorithm: at each iteration, go to the closest point remaining.
        """
        curpt, done = [0,0], numpy.zeros(self.shape, dtype='bool')
        while not done.all():
            #The following line computes the nearest remaining point...
            closest = numpy.unravel_index((numpy.where(done, numpy.inf,
                (numpy.sum((self.points - curpt)**2, axis=-1))) if
                self.smartiter else done).argmin(), self.shape)
            #...but only if self.smartiter is true.
            done[closest] = True
            curpt = self.points[closest]
            yield closest
    def __getitem__(self, key):
        import copy
        dnew = copy.copy(self)
        dnew.data = copy.copy(dnew.data)
        dnew.decimate(key)
        return dnew
    def __add__(self, other):
        dnew = Data()
        dnew.points = numpy.vstack([self.points.reshape((-1,2)),
                                    other.points.reshape((-1,2))])
        for obj in self.data:
            if obj in other.data:
                dnew.data[obj] = numpy.hstack([self.data[obj].ravel(),
                                               other.data[obj].ravel()])
        return dnew
    
    #Data structuring
    def decimate(self, valid):
        """Remove all indices not in 'valid' from this object."""
        self.points = self.points[valid]
        for obj in self.data: self.data[obj] = self.data[obj][valid]
    def copy(self):
        import copy
        dnew = copy.copy(self)
        dnew.data = copy.deepcopy(dnew.data)
        return dnew
    def tile(self, tile):
        return self[self.data["tiles"] == tile]
    def tiles(self):
        return [self.tile(tile) for tile in numpy.unique(self.data["tiles"])]
    
    #Data manipulation
    def remove_dark(self):
        """Remove points that contain a dark measurement."""
        self.decimate(numpy.isfinite(self.z))
    def plane(self):
        """Return the best-fit plane to this data."""
        from lsst.analysis import utils
        return utils.fitplane(self.points, self.z)
    def planarize(self):
        """Subtract the best-fit plane from this data."""
        from lsst.analysis import utils
        assert numpy.isfinite(self.z).all()
        self.z -= utils.evalplane(self.plane(), self.points)
    def spline(self, smoothing=None):
        """Return the best-fit spline to this data."""
        from lsst.analysis import utils
        return utils.fitspline(self.points, self.z, smoothing)
    def remove_outliers(self, std_tol=1.5):
        """Remove the most extreme points"""
        from lsst.analysis import outlier
        for tnum in numpy.unique(self.data["tiles"]):
            self.decimate(outlier.valid(self, self.data["tiles"]==tnum, std_tol=std_tol))
    
    #Data visualization
    def raw_plot(*args, **kwargs): #self intentionally omitted from args
        """Plot as a single surface."""
        from lsst.analysis import plot
        if 'scalarbar' not in kwargs: kwargs['scalarbar'] = True
        return plot.Plot(*args, **kwargs)
    def plot(self, scene=None, **kwargs):
        """Plot intelligently, splitting into tiles and scaling."""
        result = []
        for tile in self.tiles():
            result.append(tile.raw_plot(scene, self.z.min(), self.z.max(),
                                        scalarbar=(result==[]), **kwargs))
            if scene is None: scene = result[0].scene
        return result
    
    #Data storage
    def format_pt(self, i):
        return ('{0:13.2f} {1[0]:06.2f} {1[1]:06.2f} {2:+06.2f} {3:02d}\n'
                .format(self.t[i], self.points[i], self.z[i],
                        self.data["tiles"][i]))
    def write(self, out):
        """Write this data to a file."""
        out.write('# {0:<11} {1:<6} {2:<6} {3:<6} {4}\n'
                  .format('Time(s)', 'X(mm)', 'Y(mm)', 'Z(um)', 'Tile'))
        for i in self: out.write(self.format_pt(i))
    def as_vtk(self, warp=1):
        from enthought.tvtk.api import tvtk
        return tvtk.PolyData(points=numpy.column_stack(
                [self.points.reshape((-1,2)), self.z.ravel()*warp]))
