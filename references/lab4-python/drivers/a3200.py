"""Wrapper class for the Aerotech A3200, connected via the FireWire bus.

Classes:
Axis -- Represents a single axis of the gantry.
A3200Exception -- Raised when an A3200 DLL call returns an error.

Properties:
x, y, z -- The three axes of the gantry.
cmplr, sys -- Objects representing the two Aerotech DLL files.
haerctrl -- A handle representing the current connection to the gantry.

Functions:
mask -- Return the axis mask for a list of axes.
rawdllfunc -- Execute the specified function from a given DLL file.
dllfunc -- Execute a function from the "sys" DLL and pass it "haerctrl".
dllmove -- Execute a multi-axis move command from the "sys" DLL file.
wait -- Wait for all actions on the given list of axes to complete.
xy*** -- Convenience functions that operate on x and y simultaneously.
"""

import ctypes

def initialized():
    temp = ctypes.c_int()
    rawdllfunc(sys, 'SysIsSystemInitialized', ctypes.pointer(temp))
    result = temp.value==0
    del temp
    return result

def open(path=r"C:\A3200\Ini\Default.prm"):
    if not initialized():
        rawdllfunc(cmplr, "SysInitialize", 0, path, 0,
                   ctypes.pointer(haerctrl), *[ctypes.c_void_p()]*8)
    else: rawdllfunc(sys, "SysOpen", 0, 0, ctypes.pointer(haerctrl))
    for axis in [x, y]: axis.enable()

def close():
    dllfunc('SysClose')

def mask(axes):
    """Return the axis mask for the specified list of axes.
    
    Parameters:
    axes -- A list of axis objects.
    
    Returns an integer.
    """
    return sum([axis.mask for axis in axes])

def rawdllfunc(dll, name, *params):
    """Execute a function from a DLL library and catch errors accordingly.
    
    Parameters:
    dll -- Either the "sys" or "cmplr" objects.
    name -- The name of the function to call.
    All remaining arguments are passed to the DLL.
    
    The function name is automatically prefixed with "Aer".
    """
    result = getattr(dll, "Aer"+str(name))(*params)
    if result != 0 and name != "ErrGetMessageEx": #Prevent infinite recursion
        raise A3200Exception(result)

def dllfunc(name, *params):
    """Execute a function from the "sys" DLL library.
    
    Parameters:
    name -- The name of the function to call.
    All remaining arguments are passed to the DLL.
    
    The function name is automatically prefixed with "Aer".
    The "haerctrl" parameter is automatically passed to the DLL.
    """
    rawdllfunc(sys, name, haerctrl, *params)

def wait(axes, timeout=0):
    """Wait for all actions on the specified axes to complete.
    
    Parameters:
    axes -- The list of axes to wait for.
    timeout -- Maximum number of seconds to wait. 0 means wait forever.
    """
    dllfunc("MoveMWaitDone", mask(axes), timeout*100, 0)

def faultack():
    dllfunc("SysFaultAck", mask([x, y, z]), 0, True)

def xymove(destination, velocity=100, blocking=True):
    """Move to the specified position in the XY plane.
    
    Parameters:
    destination -- A tuple containing the X and Y coordinates in um.
    velocity -- The speed at which each axis should move in um/sec.
    blocking -- Whether to wait for the procedure to finish.
    """
    x.move(destination[0], velocity, blocking=False)
    y.move(destination[1], velocity, blocking=False)
    if blocking: wait([x, y])

def xyrelmove(destination, velocity=100, blocking=True):
    x.relmove(destination[0], velocity, blocking=False)
    y.relmove(destination[1], velocity, blocking=False)
    if blocking: wait([x, y])

def xyposition():
    return x.position(), y.position()

def xyhome(blocking=True):
    x.home(blocking=False)
    y.home(blocking=False)
    if blocking: wait([x, y])

class Axis:
    """Wrapper class for one axis of the Aerotech A3200.
    
    Instance variables:
    index -- The index of this axis (starting from 0).
    mask -- The axis mask for this axis only.
    
    Methods:
    dist -- Convert a measurement from microns to machine steps.
    dllmove -- Execute a single-axis move command on this axis.
    position -- Get the current position in um.
    wait -- Wait for all actions to complete on this axis.
    enable -- Enable this axis.
    disable -- Disable this axis.
    home -- Home this axis.
    move -- Move this axis to the specified position.
    """
    
    def __init__(self, index, steps_per_mm=1000):
        """Create a new axis.
        
        Parameters:
        index -- The index of this axis.
        step -- The number of machine steps in 1 mm.
        """
        self.index = index
        self.mask = 2**self.index
        self.steps = steps_per_mm
    
    def dist(self, mm):
        """Convert a measurement from mm to machine steps."""
        return int(mm*self.steps)
    
    def dllmove(self, name, blocking, *params):
        """Execute a single-axis move function from the "sys" DLL library.
        
        Parameters:
        name -- The name of the function to call.
        blocking -- Whether to wait for the procedure to finish.
        All remaining arguments are passed to the DLL.
        
        The function name is automatically prefixed with "AerMove".
        The "haerctrl" parameter is automatically passed to the DLL.
        The axis index is automatically generated and passed to the DLL.
        """
        #2.6: dllfunc("Move{0}".format(name), self.index, *params)
        dllfunc("Move"+str(name), self.index, *params)
        if blocking: self.wait()
    
    def position(self):
        """Get the current position of this axis in mm."""
        temp = ctypes.c_double()
        dllfunc("StatusGetAxisInfoPosition", self.mask, 0,
            ctypes.pointer(temp), *[ctypes.c_void_p()]*8)
        position = temp.value/self.steps
        del temp
        return position
    
    def wait(self, timeout=0):
        """Wait for all actions on this axis to complete.
        
        Parameters:
        timeout -- Maximum number of seconds to wait. 0 means forever.
        """
        self.dllmove("WaitDone", False, timeout*100, 0)
    
    def enable(self, blocking=True):
        """Enable this axis.
        
        Parameters:
        blocking -- Whether to wait for the procedure to finish,
        """
        self.dllmove("Enable", blocking)
    
    def disable(self, blocking=True):
        """Enable this axis.
        
        Parameters:
        blocking -- Whether to wait for the procedure to finish,
        """
        self.dllmove("Disable", blocking)
    
    def home(self, blocking=True):
        """Home this axis.
        
        Parameters:
        blocking -- Whether to wait for the procedure to finish,
        """
        self.dllmove("Home", blocking)
    
    def move(self, dest, vel=100, blocking=True):
        """Move this axis to the specified destination position.
        
        Parameters:
        dest -- The desired destination position, in mm.
        vel -- The desired speed in mm/sec.
        blocking -- Whether to wait for the procedure to finish,
        """
        self.dllmove("Absolute", blocking, self.dist(dest), self.dist(vel))
    
    def relmove(self, disp, vel=100, blocking=True):
        """Move this axis by the specified displacement.
        
        Parameters:
        disp -- The distance to move, in mm.
        vel -- The desired speed in mm/sec.
        blocking -- Whether to wait for the procedure to finish,
        """
        self.dllmove("Incremental", blocking, self.dist(disp), self.dist(vel))
    
    def freerun(self, vel=3000):
        """Move this axis at the specified velocity until halt() is called.
        
        The sign of 'vel' indicates direction.
        """
        self.dllmove("Freerun", False, (2 * (vel>0) - 1), abs(self.dist(vel)))
    
    def halt(self, blocking=True):
        self.dllmove("Halt", blocking)

class A3200Exception(Exception):
    def __init__(self, errornum):
        """Create a new exception.
        
        Parameters:
        errornum -- The number of the error.
        """
        temp = ctypes.create_string_buffer(76)
        rawdllfunc(sys, "ErrGetMessageEx", errornum, temp, len(temp), 0)
        self.errormsg = temp.value
        del temp
    
    def __str__(self):
        return self.errormsg

cmplr, sys = ctypes.windll.A32CMPLR, ctypes.windll.A32SYS
haerctrl = ctypes.c_int()
x, y, z = Axis(0), Axis(1), Axis(2, 2)
