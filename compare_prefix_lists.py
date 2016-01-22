# compare_prefix_lists.py
#
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

#
def build_router_dict(router_name, ssh_username, ssh_password, global_verbose):
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
#            if routerDict.verbose:
#                print("could not connect to {}, due to {}".format(
#                                net_device["ip"], e))
            connected = False
    except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
#        if routerDict.verbose:
#            print("could not connect to {}, due to {}".format(
#                            net_device["ip"], e))
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
def get_prefix_lists(routerDict, pl_list, global_verbose):
#
# Returns dictionary of prefix-lists; each dict item is a list of prefix-list lines
#
    return_lists = {}
    with ssh_manager(routerDict) as netConnect:
        for pl_name in pl_list:
            command = "show ip prefix-list %s" % (pl_name)
            try:
                output = netConnect.send_command(command)
            except Exception as e:
                print("Encountered a non setup/teardown error", e)
                return {}
            if global_verbose: print "%s" % output
            if not output:
                print "'%s' output empty... too slow?" % (command)
            return_lists[pl_name] = output.splitlines()
    return return_lists

def parse_args():
    parser = argparse.ArgumentParser(
                                    description = 'verifies prefix-lists for 3rd parties')
    parser.add_argument('--verbose', action='store_true',
                       help='provide additional output for verification')
    parser.add_argument('--username', help='username for SSH connections')
    parser.add_argument('--password', help='password for SSH username')
    parser.add_argument('--routerfile', help='source file for list of routers',
                        required = True)
    parser.add_argument('--prefixlistfile', help='source file for list of prefix-list to check against routers', required = True)
    args = parser.parse_args()
    if args.verbose:
        global_verbose = True
    else:
        global_verbose = False

    if args.username:
        ssh_username = args.username
    else:
        ssh_username = raw_input("Enter Username> ")
    if args.password:
        ssh_password = args.password
    else:
        ssh_password = getpass.getpass("Enter Password> ")

    try:
        with open(args.routerfile) as f:
            router_list = f.read().splitlines()
    except:
        quit("router file cannot be found")

    router_list = [x for x in router_list if x[0] != "#" and x[0] != " "]

    try:
        with open(args.prefixlistfile) as f:
            pl_list = f.read().splitlines()
    except:
        quit("router file cannot be found")

    pl_list = [x for x in pl_list if x[0] != "#" and x[0] != " "]

    return global_verbose, ssh_username, ssh_password, router_list, pl_list
#
# MAIN
#
# Handle arguments
def main():
# Get arguments / global variables
    global_verbose, ssh_username, ssh_password, router_list, pl_list = parse_args()
    #
    # Get output
    outputDict = {}
    for router in router_list:
        routerDict = build_router_dict(router, ssh_username, ssh_password, global_verbose)
        outputDict[router] = get_prefix_lists(routerDict, pl_list, global_verbose)
    #
    # Remove blank lines
    #for router in outputDict:
    #    for output in outputDict:
    #        outputDict[router][output].remove("")
    #
    # Check for inconsistencies between routers
    for pl_name in outputDict[router_list[0]].iterkeys():
        for router in outputDict:
            missing = list(set(outputDict[router_list[0]][pl_name]) - set(outputDict[router][pl_name]))
            extra = list(set(outputDict[router][pl_name]) - set(outputDict[router_list[0]][pl_name]))
            print "Router %s:  %s" % (router, pl_name)
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
    #
    # Check for duplicated prefixes between two ACLs in a single router
#    for router in outputDict:
#        list1 = []
#        for x in range(2, len(outputDict[router][0])):
#            list1.append(outputDict[router][0][x].split()[3])
#        list2 = []
#        for x in range(2, len(outputDict[router][1])):
#            list2.append(outputDict[router][1][x].split()[3])
#        dup_entries = list(set(list1).intersection(list2))
#        print "Router %s" % (router)
#        if dup_entries:
#            dup_entries.sort()
#            print "Duplicate Entries:"
#            for entry in dup_entries:
#                print entry
#        else:
#            print " No duplicates"

# __main__
if __name__ == '__main__':
    main()

