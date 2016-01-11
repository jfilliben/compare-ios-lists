# Automates check of 3rd party prefix-list
#
from contextlib import contextmanager
import netmiko
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException
import getpass
import argparse
#
#use variables for constants
router_list = ["riUSlynchburg005", "riUSlynchburg006", \
               "riUSblythewoo005", "riUSblythewoo006", \
              ]
pl_name = "PL_in_from_ThirdParty_"
lyn_pl = "LYN"
bly_pl = "BLY"
global_verbose = False
#
@contextmanager
def ssh_manager(net_device):
    '''
    args -> network device mappings
    returns -> ssh connection ready to be used
    '''
    try:
        SSHClient = netmiko.ssh_dispatcher(
                        device_type=net_device["device_type"])
        try:
            conn = SSHClient(**net_device)
            connected = True
        except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
            print("could not connect to {}, due to {}".format(
                        net_device["ip"], e))
            connected = False
    except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
        print("could not connect to {}, due to {}".format(
                        net_device["ip"], e))
        connected = False
    try:
        if connected:
            yield conn
        else:
            yield False
    finally:
        if connected:
            conn.disconnect()
#
def build_router_dict(router_name, ssh_username, ssh_password):
#
# Builds dictionary to be passed to netmiko
#
#    detect IOS type or read it from somewhere?
#
    routerDict = {
        'device_type': 'cisco_ios',
        'ip': router_name,
        'username': ssh_username,
        'password': ssh_password,
        'verbose': global_verbose,
#        'global_delay_factor': 3,
    }
    return routerDict
#
def get_prefix_lists(routerDict):
#
# Returns dictionary of interfaces and IP addresses
#
# get first prefix-list
    command = "show ip prefix-list %s%s" % (pl_name, lyn_pl)
    command2 = "show ip prefix-list %s%s" % (pl_name, bly_pl)
    with ssh_manager(routerDict) as netConnect:
        try:
            output = netConnect.send_command(command)
            output2 = netConnect.send_command(command2)
        except Exception as e:
            print("Encountered a non setup/teardown error", e)
            return {}
    if global_verbose: print "%s" % output
    if global_verbose: print "%s" % output2
    if not output:
        print "'%s' output empty... too slow?" % (command)
    if not output2:
        print "'%s' output empty... too slow?" % (command2)
    pl_one = output.splitlines()
    pl_two = output2.splitlines()
    return pl_one, pl_two
#
# MAIN
#
# Handle arguments
parser = argparse.ArgumentParser(
                                description = 'verifies prefix-lists for 3rd parties')
parser.add_argument('--verbose', action='store_true',
                   help='provide additional output for verification')
parser.add_argument('--username', help='username for SSH connections')
parser.add_argument('--password', help='password for SSH username')
args = parser.parse_args()
if args.verbose:
    global_verbose = args.verbose
if args.username:
    ssh_username = args.username
else:
    ssh_username = raw_input("Enter Username> ")
if args.password:
    ssh_password = args.password
else:
    ssh_password = getpass.getpass("Enter Password> ")
#
# Get output
outputDict = {}
for router in router_list:
    routerDict = build_router_dict(router, ssh_username, ssh_password)
    outputDict[router] = get_prefix_lists(routerDict)
#
# Remove blank lines
#for router in outputDict:
#    for output in outputDict:
#        outputDict[router][output].remove("")
#
# Check for inconsistencies between routers
pl_index = 0
for x in outputDict[router_list[0]]:
    pl_reference = x
    for router in outputDict:
        missing = list(set(pl_reference) - set(outputDict[router][pl_index]))
        extra = list(set(outputDict[router][pl_index]) - set(pl_reference))
        print "Router %s:  %s" % (router, pl_reference[1].split(":")[0])
        if not(missing) and not(extra):
            print " Prefix-list is Correct"
        if missing:
            missing.sort()
            print "Missing Entries:"
            for entry in missing:
                print entry
        if extra:
            extra.sort()
            print "Extra Entries:"
            for entry in extra:
                print entry
    pl_index += 1
#
# Check for duplicated prefixes between two ACLs in a single router
for router in outputDict:
    list1 = []
    for x in range(2, len(outputDict[router][0])):
        list1.append(outputDict[router][0][x].split()[3])
    list2 = []
    for x in range(2, len(outputDict[router][1])):
        list2.append(outputDict[router][1][x].split()[3])
    dup_entries = list(set(list1).intersection(list2))
    print "Router %s" % (router)
    if dup_entries:
        dup_entries.sort()
        print "Duplicate Entries:"
        for entry in dup_entries:
            print entry
    else:
        print " No duplicates"
