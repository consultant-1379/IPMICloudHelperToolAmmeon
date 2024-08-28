#!/usr/bin/env python
####################################################################
# COPYRIGHT Ericsson AB 2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
####################################################################

import argparse
import urllib2
import sys
import time
import netaddr


def pretend_import_is_used():
    return time.time()


class IPMICloudAdapter(object):
    ip_name = {
            42: "ms-1",
            43: "sc-1",
            44: "sc-2",
            235: "sc-3",
            241: "sc-4",
            45: "pl-3",
            46: "pl-4",
            193: "topology",
            194: "pmstream",
            195: "csl-eps1",
            196: "csl-eps2",
            202: "svc1",
            203: "svc2",
            204: "db1",
            205: "db2",
        }

    def __init__(self, host):
        try:
            node_addr = netaddr.IPAddress(host)
        except netaddr.core.AddrFormatError as ex:
            raise ValueError(ex)

        try:
            self.vmname = self.ip_name[node_addr.words[-1]]
        except KeyError:
            raise ValueError("VApp node IP {0} is not valid".format(node_addr))

    def set_bootdev_pxe(self):
        return self._set_boot_device('net')

    def set_bootdev_hd(self):
        return self._set_boot_device('hd')

    def _set_boot_device(self, dev):
        apistr = "Vms/set_boot_device_api/boot_devices:{0}/vm_name:{1}.xml".\
                format(dev, str(self.vmname))
        if dev == 'hd':
            return self._call_cloud_api(apistr, "Set Boot Device to disk")
        else:
            apistr = "{0}:{1}/vm_name:{2}.xml".format(
                    'Vms/set_boot_device_api/boot_devices',
                    'net',
                    str(self.vmname)
                    )
            return self._call_cloud_api(apistr, "Set Boot Device to pxe")

    def set_poweroff(self):
        apistr = "Vms/poweroff_api/vm_name:%s.xml" % (str(self.vmname))
        return self._call_cloud_api(apistr, "Chassis Power Control: Down/Off")

    def set_poweron(self):
        apistr = "Vms/poweron_api/vm_name:%s.xml" % (str(self.vmname))
        # Wait a bit before making the node boot from drive
        return_code = self._call_cloud_api(apistr, "")

        print "Chassis Power Control: Up/On"
        return return_code

    def _call_cloud_api(self, apistr, msg):
        url = "https://10.42.34.79/" + apistr
        req = urllib2.Request(url)
        try:
            urllib2.urlopen(req)
            print msg
            return 0
        except urllib2.HTTPError as e:
            print "Error sending command - response code " + str(e.code)
            print e.read()
            print str(type(e))
            return 1
        except urllib2.URLError as e:
            print "Error sending command '%s'" % url
            print e.reason
            print "Exception Type:", str(type(e))
            return 1

    def run_cmd(self, args):
        if args.subcmd == "bootdev":
            if args.arg == "pxe":
                return self.set_bootdev_pxe()
            elif args.arg == "disk":
                return self.set_bootdev_hd()
            else:
                print "Unknown boot device: " + str(args.arg)
                return 1
        elif args.subcmd == "power":
            if args.arg == "off":
                return self.set_poweroff()
            elif args.arg == "on":
                return self.set_poweron()
            else:
                print "Unknown power state: " + str(args.arg)
                return 1
        else:
            print "Unknown subcommand: " + str(args.subcmd)
            return 1


def run_ipmitool():
    desc = '''
    Ericsson IPMI Tool for the cloud. Implements just enough of the required
    "ipmitool" commands to allow a cloud VM to be treated as a regular
    server. Specifically, you can poweroff, poweron and change the boot device.

    We map the last two characters of the given hostname / IP address
    to the requisite vApp IP address, and use this to map to the relevant
    vApp name to reboot. These characters should match the last two digits of
    the primary IP address of that node.
    '''

    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-H', dest='host', nargs='?',
            help='IP of the VM to effect')
    parser.add_argument('-U', dest='username', nargs='?',
            help='Cloud username (ignored)')
    parser.add_argument('-P', dest='password', nargs='?',
            help='Cloud password (ignored)')
    parser.add_argument('-I', dest='interface', nargs='?',
            help='IPMI interface (ignored)')

    parser.add_argument('command', help='The IPMI command')
    parser.add_argument('subcmd', help='The IPMI subcommand')
    parser.add_argument('arg', help='The subcommand argument')
    parser.add_argument(
        'options',
        help='Any subcommand options (ignored)',
        nargs='*'
        )

    args = parser.parse_args()
    ipmi = IPMICloudAdapter(args.host)

    sys.exit(ipmi.run_cmd(args))


if '__main__' == __name__:
    run_ipmitool()
