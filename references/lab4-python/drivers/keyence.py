"""Wrapper module for the Keyence LT-9501, connected via the serial port.

Properties:
port -- Serial port object that is connected to the sensor.

Functions:
raw_command -- Send a specified string to the sensor.
set_samples -- Set the number of samples to be averaged.
measure -- Return the value reported by the sensor.
"""

import serial
import time

port = serial.Serial(baudrate=115200)
port.port = 0

def open():
    port.open()

def raw_command(command):
    """Send a command to the sensor over the serial port.
    
    Commands are terminated by carriage returns, but they should not be
    included in the parameter.
    
    'command' is the message to be sent.
    For command=['SR', 'OA', '2'], the message sent is 'SR,OA,2\r'.
    
    Returns a list.  If the data received back is 'SD,OA\r', the return
    value is ['SD', 'OA'].
    """
    port.write(','.join(command) + "\r")
    chars = [port.read()]
    while chars[-1] != "\r": chars.append(port.read())
    result = ''.join(chars[:-1]).split(',')
    if result[0] != 'ER': return result
    else: raise KeyenceException(result[2], command)

#Convert between the integers 0-15 and uppercase hexadecimal characters
def hexcode(num): return hex(num)[2].upper()
def intcode(str): return int(str, 16)

#Different scan modes, in format (width, spacing)
scan_modes = [None,     (120, 2),
              (120, 4), (120, 8),
              (240, 2), (240, 4),
              (240, 8), (400, 2),
              (400, 4), (400, 8),
              (560, 2), (560, 4),
              (560, 8), (4  , 1)]

#Time to make one scan, in ms
scan_times = {None:     0.64,
              (120, 2): 43.6,
              (120, 4): 23.1,
              (120, 8): 19.2,
              (240, 2): 84.6,
              (240, 4): 42.3,
              (240, 8): 28.2,
              (400, 2): 143.,
              (400, 4): 67.9,
              (400, 8): 41.0,
              (560, 2): 188.,
              (560, 4): 93.6,
              (560, 8): 53.8,
              (4  , 1): 2.6}

def get_scan_mode():
    """Get the scan mode.  See the manual for more information.
    
    Returns a tuple (width, pitch)."""
    return scan_modes[intcode(raw_command(['SR', 'SC'])[2])]

def set_scan_mode(mode):
    """Set the scan mode.  See the manual for more information.
    
    'mode' is a tuple (width, pitch)."""
    raw_command(['SD','SC', hexcode(scan_modes.index(mode))])

def get_samples(out=1):
    """Get the number of samples to be averaged.
    
    Parameters:
    out -- 1 for output channel 1, 2 for output channel 2, 0 for both.
    """
    return intcode(raw_command(['SR', 'OA', str(out)])[3])
    
def set_samples(num_samples, out=1):
    """Set the number of samples to be averaged.
    
    Parameters:
    num_samples -- The base-2 log of the number of samples to average.
    out -- 1 for output channel 1, 2 for output channel 2, 0 for both.
    """
    raw_command(['SD', 'OA', str(out), hexcode(num_samples)])

def get_time():
    """Calculate the time required to take a measurement, in seconds.
    
    See pages 7-14 and 9-6 in the Keyence manual for more information.
    """
    s = get_samples()
    return 1.3 * (scan_times[get_scan_mode()]*
                  (2**s+2**(s-6 if s>6 else 0))+0.64)/1000

def measure(out=1, blocking=False):
    """Return the currently measured value from the sensor.
    
    Parameters:
    out -- 1 for output channel 1, 2 for output channel 2, 0 for both.
    blocking -- Whether to wait for new data to be acquired, or return
        data from the instrument's buffer.
    
    Returns the distance in um if only one output is specified, or a tuple
    of values if both outputs are desired.  'None' is returned if no surface
    is visible.
    """
    if blocking: time.sleep(get_time())
    #2.6 data = raw_command("M{0},0".format(out))[3:11]
    data = raw_command(["M"+str(out),'0'])
    val = float(data[1])
    if abs(val) > 5000: val = None
    if out != 0: return val
    val2 = float(data[2])
    if abs(val2) > 5000: val2 = None
    return val, val2

def close():
    """Close the serial port."""
    port.close()

#Serial port error codes
errors = {'00': 'Command',
          '01': 'Status',
          '02': 'Parity',
          '03': 'Receive buffer full',
          '04': 'Send buffer full',
          '05': 'Framing',
          '20': 'Command length',
          '21': 'Parameter count',
          '22': 'Invalid parameter',
          '88': 'Timeout',
          '99': 'Other'}

class KeyenceException(Exception):
    def __init__(self, errornum, badcommand):
        self.errormsg = errors[errornum]
        self.cmd = ','.join(badcommand)
    
    def __str__(self):
        return self.errormsg + ' error: ' + self.cmd
