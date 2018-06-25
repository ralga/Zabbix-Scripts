#!/usr/bin/env python
#
# import needed modules.
# pyzabbix is needed, see https://github.com/lukecyca/pyzabbix
#
import argparse
import ConfigParser
import os
import os.path
import distutils.util
import cmd
import traceback
import sys
from pprint import pprint
from pyzabbix import ZabbixAPI
####Custom####
import json

# define config helper function
def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
                dict1[option] = Config.get(section, option)
                if dict1[option] == -1:
                        DebugPrint("skip: %s" % option)
        except:
                print("exception on %s!" % option)
                dict1[option] = None
    return dict1


# set default vars
defconf = os.getenv("HOME") + "/.zbx.conf"
username = ""
password = ""
api = ""
noverify = ""

# Define commandline arguments
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,description='Interactive Zabbix API commandline client.', epilog="""
This program can use .ini style configuration files to retrieve the needed API connection information.
To use this type of storage, create a conf file (the default is $HOME/.zbx.conf) that contains at least the [Zabbix API] section and any of the other parameters:

 [Zabbix API]
 username=johndoe
 password=verysecretpassword
 api=https://zabbix.mycompany.com/path/to/zabbix/frontend/
 no_verify=true

""")
parser.add_argument('-u', '--username', help='User for the Zabbix api')
parser.add_argument('-p', '--password', help='Password for the Zabbix api user')
parser.add_argument('-a', '--api', help='Zabbix API URL')
parser.add_argument('--no-verify', help='Disables certificate validation when using a secure connection',action='store_true')
parser.add_argument('-c','--config', help='Config file location (defaults to $HOME/.zbx.conf)')
parser.add_argument('-k','--key',help='Key to select items')
parser.add_argument('-T','--trigger',help='Triggers name to disable. Can be incomplete')
parser.add_argument('-N','--no-run',help='Print what will be done without doing any modification //NOT IMPLEMENTED YET',action='store_true')
parser.add_argument('-t','--tag',help='Define the tag next #PythonScript in trigger\'s title')
parser.add_argument('-v','--threshold',help='Threshold of the calculated value, can be a MACRO.')
parser.add_argument('-O','--override',help='Will override current mean trigger if already exist.',action='store_true')
args = parser.parse_args()

# load config module
Config = ConfigParser.ConfigParser()
Config

# if configuration argument is set, test the config file
if args.config:
 if os.path.isfile(args.config) and os.access(args.config, os.R_OK):
  Config.read(args.config)

# if not set, try default config file
else:  Config.read(defconf)

# try to load available settings from config file
try:
 username=ConfigSectionMap("Zabbix API")['username']
 password=ConfigSectionMap("Zabbix API")['password']
 api=ConfigSectionMap("Zabbix API")['api']
 noverify=bool(distutils.util.strtobool(ConfigSectionMap("Zabbix API")["no_verify"]))
except: pass

# override settings if they are provided as arguments
if args.username:
 username = args.username

if args.password:
 password = args.password

if args.api:
 api = args.api

if args.no_verify:
 noverify = args.no_verify

# test for needed params
if not username:
 print("Error: API User not set")
 exit()

if not password:
 print("Error: API Password not set")
 exit()

if not api:
 print("Error: API URL is not set")
 exit()

if not args.key:
    print ("Error: Should have the item's key (-k)")
    exit()

if not args.trigger:
    print ("Error: No trigger specified (-T)")
    exit()
if not args.threshold:
    print ("Error: No threshold specified (-v)")
    exit()

if not args.tag:
    print ("Warning : No tag specified (-t), each tag should be unique, may become messy very fast.")
    tag=""
else:
    tag= args.tag

# Setup Zabbix API connection
zapi = ZabbixAPI(api)

if noverify is True:
 zapi.session.verify = False

# Login to the Zabbix API
print("Logging in on '" + api + "' with user '" + username +"'.")
zapi.login(username, password)

##################################
# Start actual API logic
##################################


def selectHosts(hosts):
    aux = []
    itemaux=[]
    for host in hosts:
        items = zapi.item.get(filter={'host':host},search={'key_':key})
        if (len(items) > 1):
            aux.append(host)
            itemaux.append(items)
            print ('Found match for host : ' + host)
    return aux,itemaux

def getHosts():
    hosts = zapi.host.get()
    aux = []
    for host in hosts:
        aux.append(host['host'])
    return aux

def override(host):
    trigger = (zapi.trigger.get(filter={'host': host},search={'description':'#PythonScript' + tag+": "}))
    if trigger != []:
        print ("Already existing trigger, will override.")
        if(not args.no_run):
            zapi.trigger.delete(trigger[0]['triggerid'])

def modifyHost(host, triggers, final):
    print "Create trigger"
    zapi.trigger.create(
        {'status':0,
         'description':'#PythonScript'+tag+': '+ triggerName +' : {ITEM.LASTVALUE}',
         'priority': 3,
         'comments': 'Last value: {ITEM.LASTVALUE1}.',
         'expression': final})
    print ("Done\nDisabling 'High memory utilization triggers for "+ host)
    for j in range(len(triggers)):
        zapi.trigger.update(triggerid=triggers[j]['triggerid'],status=1)
    print "Done"

key = args.key
if (args.no_run):
    print ("\n\nNo run, will simulate but won't modify\n\n")
print "Starting research for " + key
hosts=getHosts()
triggerName = args.trigger
hosts,items = selectHosts(hosts)
print "End of research"

for i in range(len(hosts)):
    print "About " + hosts[i]
    if (args.override) :
        override(hosts[i])
    if (zapi.trigger.get(filter={'host': hosts[i]},search={'description':'#PythonScript' + tag+": "}) == [] or (args.no_run and args.override)):
        triggers = zapi.trigger.get(filter={'host': hosts[i]},search={'description':triggerName})
        final = "("
        for j in range(len(items[i])-1):
            final = final + "{"+hosts[i]+":"+items[i][j]['key_']+".avg(5m)} +"

        final = final +  "{"+hosts[i]+":"+items[i][len(items[i])-1]['key_']+".avg(5m)})/"+str(len(items[i]))+">"+str(args.threshold)
        print "Trigger will be :"
        print final + "\n"
        if (not args.no_run):
            modifyHost(hosts[i],triggers,final)
    else:
        print "Already has trigger.\n"
