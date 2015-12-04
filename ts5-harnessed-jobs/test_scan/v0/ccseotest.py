###############################################################################
# test_scan
#
###############################################################################

from org.lsst.ccs.scripting import *
from java.lang import Exception
import sys
import time

CCS.setThrowExceptions(True);

cdir = tsCWD
cdir = "/tmp/"

posx = 0.0
posy = 0.0
posz = 0.0

try:
#attach CCS subsystem Devices for scripting
    print "Attaching TS5 subsystems"
    aerosub   = CCS.attachSubsystem("ts5app/Positioner");

    print "getting version"
    result = aerosub.synchCommand(10,"getVersion")
    aerover = result.getResult()
    print "Returned Aerotech Controller version = %s" % aerover

    print "Enable Axes"
    result = aerosub.synchCommand(10,"enableAxes")
    rply = result.getResult()

    fpfiles = open("%s/scan_results.DAT" % cdir,"w");

    print "go to home position"
    result = aerosub.synchCommand(10,"goHome")
    rply = result.getResult()

    time.sleep(3.)    

    print "Move an increment of 5.0 in x"
    result = aerosub.synchCommand(10,"moveInc_x",5.0)
    rply = result.getResult()

    print "Move an increment of 5.0 in y"
    result = aerosub.synchCommand(10,"moveInc_y",5.0)
    rply = result.getResult()

    print "Move an increment of 5.0 in z"
    result = aerosub.synchCommand(10,"moveInc_y",5.0)
    rply = result.getResult()

    time.sleep(3.)    

    print "Move an increment of -5.0 in x"
    result = aerosub.synchCommand(10,"moveInc_x",-5.0)
    rply = result.getResult()

    print "Move an increment of -5.0 in y"
    result = aerosub.synchCommand(10,"moveInc_y",-5.0)
    rply = result.getResult()

    print "Move an increment of -5.0 in z"
    result = aerosub.synchCommand(10,"moveInc_y",-5.0)
    rply = result.getResult()

    fpfiles.write("%s %s %s %f\n" % (posx,posy,posz,time.time()))

    fpfiles.close();
    fp.close();

    fp = open("%s/status.out" % (cdir),"w");

    fp.write("%s\n" % aerover);

    fp.close();


except Exception, ex:

    print "Exception at " % time.time()


except ScriptingTimeoutException, exx:

    print "ScriptingTimeoutException at %f " % time.time()


print "TEST: END"
