from numpy import *
import os, sys, textwrap, inspect

""" TO DO (from list of requirements)

- add support for acquiring and subtracting calibration flats
- add alternate scan positioning methods (manual/NView or from file)
- outlier removal (use new nearest neighbor algorithm)
- smoothing?  ...if outliers are removed is this still helpful?
- generation of output report with tip tilt piston rms pv

"""

code_enabled = True

# This script only works in ipython 0.11 (because of GUI background thread)

def print_code(func):
    """
    This decorator prints the source of a function before executing
    that function.  Only the body of the function is printed.
    "global" statements are not printed.
    """
    def newfunc(*args, **kwargs):
        if code_enabled:
            try:
                lines = inspect.getsource(func).splitlines()
                while not (lines[0] and lines[0][0].isspace()): del lines[0]
                for line in textwrap.dedent('\n'.join(lines)).splitlines():
                    if not line.startswith('global'): print(' > ' + line) 
            except: print(' # error displaying code')
        func(*args, **kwargs)
    return newfunc

@print_code
def initialize():
    global a3200, keyence
    from lsst.drivers import a3200, keyence
    a3200.open()
    a3200.x.enable()
    a3200.y.enable()
    keyence.open()

@print_code
def home():
    a3200.xyhome()

@print_code
def setup_raster(xmin, xmax, xstep, ymin, ymax, ystep):
    global data, scan, mydata, myscan
    from lsst.acquisition import data, scan
    mydata = data.raster_data(arange(xmin, xmax, xstep),
                              arange(ymin, ymax, ystep))
    myscan = scan.Scan(mydata)

@print_code
def setup_tiled(tile_orig, points):
    global data, scan, mydata, myscan
    from lsst.acquisition import data, scan
    mydata = data.tiled_data(tile_orig, points)
    myscan = scan.Scan(mydata)

@print_code
def run_scan():
    myscan.run()

@print_code
def close():
    a3200.close()
    keyence.close()

@print_code
def process_data():
    mydata.remove_dark()
    mydata.remove_outliers()
    mydata.planarize()
    mydata.plot()

@print_code
def save_results(path):
    myscan.write(open(path, 'w'))

def script():
    print('\nWelcome to interactive object scanner')
    print('Direct questions to dmlawrence@gmail.com\n')
    print('Please power on XYZ stage and Keyence sensor')
    raw_input('Press enter when finished\n')
    print('Initializing system...')
    initialize()
    print('Initialization finished.\n')
    if raw_input('Would you like to home the X & Y axes? (Y/n) ') in ['N','n']:
        print('XY coordinates may not be consistent.\n')
    else:
        print('Homing axes...')
        home()
        print('Axes homed.\n')
    print('Opening NView for you to set up the stage:')
    print('- determine XY location of object to be scanned')
    print('- move Z-axis in range')
    print('Press F3 for controls; exit when finished.')
    a3200.z.enable()
    os.system('NViewMMI')
    a3200.z.relmove(keyence.measure() or 0)
    a3200.z.disable()
    print('NView finished executing.\n')
    params = ['minimum x', 'maximum x', 'x increment',
              'minimum y', 'maximum y', 'y increment']
    read = lambda: [float(raw_input('{0: >12}: '.format(p))) for p in params]
    def to_points(raster):
        return dstack(meshgrid(arange(*raster[:3]),
                               arange(*raster[3:]))).reshape((-1,2))
    if raw_input('Is this to be a tiled scan? (y/N) ').lower() == 'y':
        print('Please enter these parameters to describe the tile origins:')
        tiles = to_points(read())
        print('Please enter these parameters for points relative to tiles:')
        points = to_points(read())
        setup_tiled(tiles, points)
    else:
        print('Please enter these parameters to describe point locations:')
        values = read()
        print('\nSetting up scan...')
        setup_raster(*values)
        print('Ready to scan.\n')
    raw_input('Press enter to scan.')
    print('Scanning... ')
    run_scan()
    print('Scan finished.\n')
    print('Closing hardware...')
    close()
    print('Hardware closed.\n')
    a = raw_input('Would you like to analyze the data now? (Y/n) ')
    if a.lower() != 'n':
        process_data()
        print('Plot is in background window.\n')
    path = raw_input('Path to save data: {0}\\'.format(os.getcwd()))
    print('Saving data...')
    save_results(path)
    print('Data saved.\n')

if __name__ == '__main__':
    try:
        script()
        while raw_input('Run another scan? (y/N) ') in ['y','Y']: script()
    except:
        print('\n\nAn unexpected error occurred.')
        if raw_input('Drop to IPython shell? (y/N) ').lower() == 'y':
            from IPython.core.iplib import InteractiveShell # ipython >=
            InteractiveShell(user_ns=globals()).mainloop()  # 0.11 req'd
