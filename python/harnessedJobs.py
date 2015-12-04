import os
import subprocess

def getVersion():
    """
    Return harnessed-jobs package version, either from git tag or from
    tarball install directory name.
    """
    import harnessedJobs as hj
    try:
        package_dir = os.path.split(hj.__file__)[0]
        command = 'cd %s; git describe --tags' % package_dir
        tag = subprocess.check_output(command, shell=True,
                                      stderr=subprocess.STDOUT)
        return tag.strip()
    except subprocess.CalledProcessError:
        # Not in a git repository, so assume this is an installation
        # from a versioned tarball.
        for item in hj.__file__.split(os.path.sep):
            if item.startswith('ts5-metrology-'):
                return item[len('ts5-metrology-'):]
    return 'unknown'
