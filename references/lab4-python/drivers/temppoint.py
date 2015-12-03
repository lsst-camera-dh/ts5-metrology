"""Interface to TempPoint executable.

Properties:
path -- The location of the executable.
"""

import subprocess

path = r"C:\tp_get_rtd.exe"

def get(chan = 0):
    query = subprocess.Popen(path+' '+str(chan+1), stdout=subprocess.PIPE)
    query.wait()
    result = float(query.communicate()[0])
    return result if result < 80000 else None
