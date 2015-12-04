export STACK_DIR=/opt/lsst/redhat6-x86_64-64bit-gcc44/DMstack/Winter2015/
source ${STACK_DIR}/loadLSST.bash
export EUPS_PATH=/opt/lsst/redhat6-x86_64-64bit-gcc44/test/jh_inst/LSSTCCSTS-100-0.2.1/eups:${EUPS_PATH}
setup eotest
setup mysqlpython
export INST_DIR=/opt/lsst/redhat6-x86_64-64bit-gcc44/test/jh_inst/LSSTCCSTS-100-0.2.1
export VIRTUAL_ENV=${INST_DIR}
source ${INST_DIR}/Modules/3.2.10/init/bash
export HARNESSEDJOBSDIR=/home/homer/lsst/ts5-metrology/
export PYTHONPATH=${HARNESSEDJOBSDIR}/python:${INST_DIR}/lib/python2.7/site-packages:${PYTHONPATH}
export PATH=${INST_DIR}/bin:${PATH}
export SITENAME=BNL
export LCATR_DATACATALOG_FOLDER=/LSST/Dev/mirror/SLAC
PS1='[ts5_jh \u@\h \W]$ '
