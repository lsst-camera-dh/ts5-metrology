import os
import sys
import subprocess
import socket
import fnmatch
import ConfigParser
import lcatr.schema
import lcatr.harness.helpers
import harnessedJobs as hj

def cast(value):
    if value == 'None':
        return None
    try:
        if value.find('.') == -1 and value.find('e') == -1:
            return int(value)
        else:
            return float(value)
    except ValueError:
        # Cannot cast as either int or float so just return the
        # value as-is (presumably a string).
        return value

def getUnitId():
    return os.environ['LCATR_UNIT_ID']

def getUnitType():
    return os.environ['LCATR_UNIT_TYPE']

def getCcdVendor():
    unit_id = getUnitType()
    vendor = unit_id.split('-')[0]
    if vendor not in ('ITL', 'E2V', 'e2v'):
        raise RuntimeError("Unrecognized CCD vendor for unit id %s" % unit_id)
    return vendor

def getJobName():
    """
    The name of the harnessed job.
    """
    return os.environ['LCATR_JOB']

def getProcessName(jobName=None):
    if jobName is None:
        myJobName = getJobName()
    else:
        myJobName = jobName
    if os.environ.has_key('ET_PROCESS_NAME_PREFIX'):
        return '_'.join((os.environ['ET_PROCESS_NAME_PREFIX'], myJobName))
    else:
        return myJobName

def getJobDir(jobName=None):
    """
    Full path of the harnessed job scripts.
    """
    if jobName is None:
        jobName = getJobName()
    return os.path.join(os.environ['LCATR_INSTALL_AREA'], jobName,
                        os.environ['LCATR_VERSION'])

def jobDirPath(fileName, jobName=None):
    """
    Prepend the job directory to the script filename, thereby giving
    the full path to that script.
    """
    return os.path.join(getJobDir(jobName), fileName)

def getSiteName():
    """
    Return the site or laboratory name
    """
    return os.environ['SITENAME']

def pythonDir():
    """
    Return directory containing the python scripts for this package.
    """
    return os.path.join(os.environ['HARNESSEDJOBSDIR'], 'python')

def configDir():
    """
    Return the full path to the directory containing the site-specific
    configuration files.
    """
    return os.path.join(os.environ['HARNESSEDJOBSDIR'], 'config', getSiteName())

def datacatalog_query(query, folder=None, site=None):
    from DataCatalog import DataCatalog
    if folder is None:
        folder = os.environ['LCATR_DATACATALOG_FOLDER']
    if site is None:
        site = getSiteName()
    datacat = DataCatalog(folder=folder, site=site)
    return datacat.find_datasets(query)

def print_file_list(description, file_list, use_basename=False):
    if description is not None:
        print description
    for item in file_list:
        if use_basename:
            print "  ", os.path.basename(item)
        else:
            print "  ", item
    sys.stdout.flush()

def datacatalog_glob(pattern, testtype=None, imgtype=None, description=None,
                     sort=False):
    sensor_id = getUnitId()
    if testtype is None or imgtype is None:
        raise RuntimeError("Both testtype and imgtype values must be provided.")
    query = ' && '.join(('LSST_NUM=="%(sensor_id)s"',
                         'TESTTYPE=="%(testtype)s"',
                         'IMGTYPE=="%(imgtype)s"')) % locals()
    datasets = datacatalog_query(query)
    file_list = []
    for item in datasets.full_paths():
        if fnmatch.fnmatch(os.path.basename(item), pattern):
            file_list.append(item)
    if sort:
        file_list = sorted(file_list)
    print_file_list(description, file_list)
    return file_list

def dependency_glob(pattern, jobname=None, paths=None, description=None,
                    sort=False):
    file_list = lcatr.harness.helpers.dependency_glob(pattern, jobname=jobname,
                                                      paths=paths)
    if sort:
        file_list = sorted(file_list)
    print_file_list(description, file_list)
    return file_list

def packageVersions():
    # Not all harnessed jobs will use eotest and/or the LSST Stack, so
    # set 'none' as the default for each.
    try:
        import lsst.eotest
        eotest_version = lsst.eotest.getVersion()
    except ImportError:
        eotest_version = 'none'

    try:
        import lsst.afw
        LSST_stack_version = lsst.afw.__version__
    except ImportError:
        LSST_stack_version = 'none'

    import lcatr.harness.version
    lcatr_harness_version = lcatr.harness.version.__version__

    import lcatr.schema.version
    lcatr_schema_version = lcatr.schema.version.__version__
        
    result = lcatr.schema.valid(lcatr.schema.get('package_versions'),
                                eotest_version=eotest_version,
                                LSST_stack_version=LSST_stack_version,
                                lcatr_harness_version=lcatr_harness_version,
                                lcatr_schema_version=lcatr_schema_version,
                                harnessedJobs_version=hj.getVersion(),
                                hostname=socket.getfqdn())
    return result

class Parfile(dict):
    def __init__(self, infile, section):
        super(Parfile, self).__init__()
        parser = ConfigParser.ConfigParser()
        parser.read(infile)
        for key, value in parser.items(section):
            self[key] = cast(value)
