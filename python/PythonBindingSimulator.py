"""
PythonBinding simulator for executing ccsTools.ccsProducer(...).
Sensor data for each test are copied from a directory containing a
simulated (or real) dataset for each CCS data acquistion script, which
have names "ccseo<dataset_name>.py"
"""
import os
import subprocess

class AcqSim(object):
    dataset_mapping = dict([('dark', 'dark'),
                            ('fe55', 'fe55'),
                            ('flat', 'flat'),
                            ('qe', 'lambda'),
                            ('sflat', 'sflat_500'),
                            ('xtalk', 'spot'),
                            ('ppump', 'trap'),
                            ('persist', 'persistence')])
    def __init__(self, rootdir):
        self.rootdir = rootdir
    def getData(self, dataset):
        if dataset not in self.dataset_mapping:
            raise RuntimeError("Invalid dataset name: " + dataset)
        testtype = self.dataset_mapping[dataset]
        command = "cp %s ." % os.path.join(self.rootdir, testtype, '*.fits')
        subprocess.check_call(command, shell=True)

class CcsResult(object):
    def __init__(self, scriptname):
        self.scriptname = scriptname
    def getOutput(self):
        return "Output from %s" % self.scriptname

class CcsJythonInterpreter(object):
    def __init__(self, name=None, host=None, port=4444):
        self.acq = AcqSim(os.environ['SIMDIR'])
    def syncExecution(self, command):
        pass
    def syncScriptExecution(self, filename, setup_commands=(), verbose=False):
        dataset = os.path.basename(filename)[len('ccseo'):-3]
        self.acq.getData(dataset)
        status_output = open('status.out', 'w')
        for flag in 'stat volt curr pres temp'.split():
            status_output.write('0\n')
        status_output.close()
        return CcsResult(filename)

if __name__ is '__main__':
    os.environ['SIMDIR'] = '../data'
    ccs = CcsJythonInterpreter()

    result = ccs.syncScriptExecution('ccseofe55.py')
    print result.getOutput()

    result = ccs.syncScriptExecution('ccseodark.py')
    print result.getOutput()
