"""SNMP communicator for networked NetBotz unit.

Properties:
path -- The location of the snmpget binary from netsnmp.
host -- The address of the NetBotz.
community -- Used for SNMP authentication.

Functions:
raw_get -- Send a message and receive a response from the NetBotz.
temperature -- Get the current temperature.
humidity -- Get the current humidity.
audio -- Get the current audio level.
particle -- Get the current particle level.
dewpoint -- Get the current dewpoint.
"""

import subprocess

path = r"C:\Program Files\netsnmp\bin\snmpget.exe"
host = "chewbacca.inst.bnl.gov"
community = "bnlio"

def raw_get(oid):
    command = '"'+path+'" -c '+community+' -v 2c '+host+' '+oid
    query = subprocess.Popen(command, stdout=subprocess.PIPE)
    query.wait()
    return float(query.communicate()[0].split('"')[1]) #Extract the number

def temperature():
    return raw_get('.1.3.6.1.4.1.5528.100.4.1.1.1.7.1095346743')

def humidity():
    return raw_get('.1.3.6.1.4.1.5528.100.4.1.2.1.7.1094232622')

def audio():
    return raw_get('.1.3.6.1.4.1.5528.100.4.1.4.1.7.1092397166')

def particle():
    return raw_get('.1.3.6.1.4.1.5528.100.4.1.10.1.7.1688855941')

def dewpoint():
    return raw_get('.1.3.6.1.4.1.5528.100.4.1.5.1.7.1092459120')

def airflow():
    return raw_get('.1.3.6.1.4.1.5528.100.4.1.3.1.7.2634294963')
