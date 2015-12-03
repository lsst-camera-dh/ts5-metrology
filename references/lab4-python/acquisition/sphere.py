from lsst.drivers import a3200, keyence
import itertools, numpy, time

def follow_edge(step=1):
    a3200.x.freerun(1)
    while keyence.measure() is not None: time.sleep(.01)
    a3200.x.halt()
    a3200.x.relmove(-step/2)
    origin, xy = a3200.xyposition(), numpy.array([0, 0])
    heading, path, i, dark = 0, [], 0, False
    while tuple(xy) not in path[:-10]:
        ldark, dark = dark, (keyence.measure(blocking=True) is None)
        if dark != ldark: i = 0
        if i%2 or not i: heading = (heading + (-1 if dark else 1)) % 4
        xy += [(1,0),(0,1),(-1,0),(0,-1)][heading]
        a3200.xymove(origin + xy*step)
        path.append(tuple(xy))
        i += 1
    return origin + numpy.array(path, dtype='float')*step

def spiral():
    for s in itertools.count(1):
        for y in range(-s+1, s+1, +1): yield (s,y)
        for x in range(s-1, -s-1, -1): yield (x,s)
        for y in range(s-1, -s-1, -1): yield (-s,y)
        for x in range(-s+1, s+1, +1): yield (x,-s)

def spiral_search(continue_func, step=.01):
    p0 = a3200.xyposition()
    s = spiral()
    while continue_func():
        a3200.xymove(p0+numpy.array(next(s))*step, blocking=True)

def continuous_spiral_search(continue_func, step=.01, vel=.1):
    origin = a3200.xyposition()
    heading = 0
    for r in itertools.count():
        a3200.xyrelmove([(1,0),(0,1),(-1,0),(0,-1)][r%4]*(r//4+1)*step,
                        blocking = False)
        

def find_center(radius=4000):
    keyence.set_samples(4, 1)
    path = follow_edge(.04)
    a3200.xymove(numpy.average(path, 0))
    a3200.z.enable()
    a3200.z.relmove(-radius)
    a3200.z.disable()
    spiral_search((lambda: keyence.measure() is None), 0.005)
    spiral_search((lambda: abs(keyence.measure(1) - keyence.measure(2) < 10)), 0.001)

def value_and_gradient(pt, func, step=.05):
    x, y = pt
    a3200.xymove((x, y+step), blocking=True)
    f_y = func()
    a3200.xymove((x, y), blocking=True)
    f_0 = func()
    a3200.xymove((x+step, y), blocking=True)
    f_x = func()
    return f_0, [(f_x-f_0)/step, (f_y-f_0)/step]

def test_opt():
    from scipy.optimize import fmin_tnc
    x, y = a3200.xyposition()
    fmin_tnc(value_and_gradient, (x,y), None,
             [(lambda: abs(keyence.measure(1, blocking=True) -
                           keyence.measure(2, blocking=False))), 0.001],
             False, [(x-.008,x+.008), (y-.008,y+.008)],)
