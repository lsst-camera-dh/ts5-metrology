"""
Use Brian's python client to query the SRS datacatalog.
"""

import os
import subprocess
import datacat
import datacat.error

remote_hosts = {'SLAC' : 'rhel6-64.slac.stanford.edu'}

def _get_job_id(dataset):
    folder = os.path.split(dataset.path)[0]
    return str(os.path.split(folder)[1]) 

def _get_job_name(dataset):
    "Get the name of the harnessed job from the Data Catalog folder name."
    folder = os.path.split(dataset.path)[0]
    return str(folder.split(os.path.sep)[-3])

def _get_filter(**kwds):
    components = ['(True)']
    for key, value in kwds.items():
        if value is not None:
            components.append('(_get_%s(x) == "%s")' % (key, value))
    condition = ' and '.join(components)
    return lambda x : eval(condition)

class DatasetList(list):
    def __init__(self, input_list, datacat_obj, sort_by_name=True,
                 job_id=None, job_name=None):
        accept = _get_filter(job_id=job_id, job_name=job_name)
        my_list = [x for x in input_list if accept(x)]
        if sort_by_name:
            super(DatasetList, self).__init__(sorted(my_list,
                                                     key=lambda x : x.name))
        else:
            super(DatasetList, self).__init__(my_list)
        self.folder = datacat_obj.folder
        self.login = datacat_obj.remote_login
        self.site = datacat_obj.site
    def job_ids(self):
        my_job_ids = []
        for item in self:
            my_job_ids.append(_get_job_id(item))
        return my_job_ids
    def filenames(self, job_id=None, job_name=None):
        accept = _get_filter(job_id=job_id, job_name=job_name)
        return [str(x.name) for x in self if accept(x)]
    def full_paths(self, job_id=None, job_name=None):
        accept = _get_filter(job_id=job_id, job_name=job_name)
        my_full_paths = []
        for dataset in self:
            if not accept(dataset):
                continue
            for location in dataset.locations:
                if location.site == self.site:
                    break
            my_full_paths.append(str(location.resource))
        return my_full_paths
    def download(self, site='SLAC', rootpath='.', nfiles=None, dryrun=True,
                 job_id=None, job_name=None, clobber=False):
        user_host = '@'.join((self.login, remote_hosts[site]))
        if nfiles is not None:
            print "Downloading the first %i files:\n" % nfiles
        if dryrun:
            print "Dry run. The following commands would be executed:\n"
        my_datasets = []
        accept = _get_filter(job_id=job_id, job_name=job_name)
        for dataset in self[:nfiles]:
            if not accept(dataset):
                continue
            for location in dataset.locations:
                if location.site == site:
                    my_datasets.append(dataset)
        for dataset in my_datasets:
            output = os.path.join(rootpath,
                                  dataset.path[len(self.folder)+1:])
            outdir = os.path.split(output)[0]
            if not os.path.isdir(outdir):
                os.makedirs(outdir)
            for location in dataset.locations:
                if location.site == site:
                    command = "scp %s:%s %s" \
                              % (user_host, location.resource, output)
                    print command
                    if not dryrun:
                        if os.path.isfile(output) and clobber:
                            os.remove(output)
                        if not os.path.isfile(output):
                            subprocess.call(command, shell=True)
                        else:
                            print "%s already exists." % output
                    break  # Just need one location at this site.

class DataCatalogException(RuntimeError):
    def __init__(self, value):
        super(DataCatalogException, self).__init__(value)

class DataCatalog(object):
    def __init__(self, folder=None, experiment="LSST",
                 mode="dev", remote_login=None, site='SLAC', config_url=None):
        self.folder = folder
        if remote_login is None:
            self.remote_login = os.getlogin()
        self.site = site
        my_config_url = datacat.config.default_url(experiment, mode=mode)
        if my_config_url is None:
            raise DataCatalogException("Invalid experiment or mode: %s, %s"
                                       % (experiment, mode))
        if config_url is not None:
            # Override the computed value.
            my_config_url = config_url
        self.client = datacat.Client(my_config_url)
    def find_datasets(self, query, folder=None, job_id=None, job_name=None,
                      datacat_search_patterns = (None, '**')):
        """
        Find datasets in the Data Catalog given the self.folder
        attribute or the specified folder.  For the default value of
        datacat_search_patterns, do a recursive search only if no
        files are found in the desired folder.
        """
        my_folder = folder
        if folder is None:
            my_folder = self.folder
        for pattern in datacat_search_patterns:
            if pattern is not None:
                pattern_path = os.path.join(my_folder.rstrip('/'), pattern)
            else:
                pattern_path = my_folder.rstrip('/')
            try:
                resp = self.client.search(pattern_path, query=query)
            except datacat.error.DcException, eobj:
                print "Caught datacat.error.DcException:"
                print eobj.raw
                raise eobj
            if resp:
                # resp has data, so no need to try remaining search patterns.
                break

#        try:
#            if folder is not None:
#                resp = self.client.search(folder, query=query)
#            else:
#                resp = self.client.search(self.folder, query=query)
#        except datacat.error.DcException, eobj:
#            print "Caught datacat.error.DcException:"
#            print eobj.raw
#            raise eobj
        return DatasetList(resp, self, job_id=job_id, job_name=job_name)

if __name__ == '__main__':
    folder = '/LSST/mirror/BNL3'
    query = 'TEMP_SET==-125 && TESTTYPE="DARK"'
    site = 'SLAC'

    datacatalog = DataCatalog(folder=folder, experiment='LSST', site=site)

    datasets = datacatalog.find_datasets(query)
    print "%i datasets found\n" % len(datasets)

    nfiles = 5
    print "File paths for first %i files at %s:" % (nfiles, site)
    for item in datasets.full_paths()[:nfiles]:
        print item

    print

    datasets.download(dryrun=True, clobber=False, nfiles=nfiles)
