#!/usr/bin/python3
# -*- coding: UTF-8 -*-
#
# This is a Python implementation of an API how to tutorial
#
# VM NAT rules
# ============
# Environment: NAT and VDC with NAT IP
#
# Add NAT rules to VM
# -------------------

# Requires:
# * 1 x VM
# * With private IP to add NAT rules

# Steps
# * Get VM with private IP without NAT rules by vmlabel
# * Get first private IP to add to NAT rules JSON
# * Get VDC of VM (use in part 2 also)
# * Get NAT IPs of VDC to add to NAT rules JSON, use first NAT IP
# * Create NAT rules with private IP/NAT IP
#
#
import copy
import json
from abiquo.client import Abiquo
from abiquo.client import check_response
import sys

# For test environment disable SSL warning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants for NAT rules
DNATPORTORIGINAL = 36911
DNATPORTTRANSLATED = 22
DNATPROTOCOL = "TCP"
VMLABEL = "NATADD"
LOCALDOMAINAPI = ".abq.example.com/api"


def main():
    # For test pass in the local system, username and password
    localsystem = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    dnatportorigin = DNATPORTORIGINAL
    API_URL = "https://" + localsystem + LOCALDOMAINAPI
    api = Abiquo(API_URL, auth=(username, password), verify=False)

# Another option:
#   API_URL = input("Enter Abiquo API URL,
#    e.g 'https://abq.example.abiquo.com/api': ")
#   username = input("Username: ")
#   password = input("Password: ")
    # Assuming test environment with self-signed certificate
#   api = Abiquo(API_URL, auth=(username, password), verify=False)

# Get VMs with VM to add NAT rules, use vmlabel filter
    code, virtualmachines = api.cloud.virtualmachines.get(
        headers={'Accept': 'application/vnd.abiquo.virtualmachines+json'},
        params={'vmlabel': VMLABEL})
    check_response(201, code, virtualmachines)
    print("Get VM, Response code is: ", code)

# Check that there is only one VM with the label,
# that there are no existing NAT rules, and that the VM has a NIC
    if virtualmachines.totalSize > 1:
        print("Warning! Multiple VMs with same label!")
    for vm in virtualmachines:
        dnatportorigin = dnatportorigin + 1
        print("NATADD VM: ", str(vm.label))
        if vm.natrules:
            print("Warning! VM already has NAT Rules!")
            continue
        if not vm.nic0:
            print("Warning! VM has no NICs")
            break
        else:
            # Get link to any private IPs in the VM to use in NAT rules
            privateIPLinks = list(filter(
                lambda vmlink: "privateip" in vmlink["type"],
                vm.json["links"]))

            # Use the first private IP
            pipLink = privateIPLinks[0]
            print("Private IP link:", json.dumps(pipLink, indent=2))

            # Get VDC of VM (use in part 2 also)
            code, vdc = vm.follow('virtualdatacenter').get(
                headers={'accept': 'application/vnd.abiquo.virtualdatacenter+json'})
            print("Response code is: ", code)
            print("VM belongs to VDC: ", vdc.name)

            # Get NAT IPs of VDC to use in NAT rules
            code, natips = vdc.follow('natips').get(
                headers={'accept': 'application/vnd.abiquo.natips+json'},
                params={'usable': True})
            print("Response code is: ", code)

            # Filter natips to get the NAT IPs that are not the default SNAT
            nonDefaultSNATIPs = list(filter(
                lambda nsnatip: nsnatip.json["defaultSnat"] == False,
                natips))

            # Get first NAT IP of VDC that is not the default SNAT
            ndsnaip = nonDefaultSNATIPs[0]
            print("ndsnaip: ", json.dumps(ndsnaip.json, indent=2))

            # Get the self link of the NAT IP
            natipLinks = list(filter(lambda link: link["rel"] == "self",
                                     ndsnaip.json["links"]))
            natipLink = natipLinks[0]
            print("natipLink: ", json.dumps(natipLink, indent=2))

            # Create NAT rules with private IP/NAT IP
            addnatrules = []

            # Create snat rule
            snatrule = {}
            snatrule["snat"] = True
            snatrule["links"] = []
            snatruleOriginalLink = copy.deepcopy(pipLink)
            snatruleOriginalLink["rel"] = "original"
            snatrule["links"].append(snatruleOriginalLink)
            snatruleTranslatedLink = copy.deepcopy(natipLink)
            snatruleTranslatedLink["rel"] = "translated"
            snatrule["links"].append(snatruleTranslatedLink)
            print("snatrule: ", json.dumps(snatrule, indent=2))
            addnatrules.append(snatrule)

            # Create dnat rule
            dnatrule = {}
            dnatrule["snat"] = False
            dnatrule["originalPort"] = DNATPORTORIGINAL
            dnatrule["translatedPort"] = DNATPORTTRANSLATED
            dnatrule["protocol"] = DNATPROTOCOL
            dnatruleOriginalLink = copy.deepcopy(natipLink)
            dnatruleOriginalLink["rel"] = "original"
            dnatrule["links"] = []
            dnatrule["links"].append(dnatruleOriginalLink)
            dnatruleTranslatedLink = copy.deepcopy(pipLink)
            dnatruleTranslatedLink["rel"] = "translated"
            dnatrule["links"].append(dnatruleTranslatedLink)
            print("dnatrule: ", json.dumps(dnatrule, indent=2))
            addnatrules.append(dnatrule)

            # Get edit link of VM to use for put request
            vmEditLinks = list(filter(
                lambda link: link["rel"] == "edit", vm.json["links"]))
            vmEditLink = vmEditLinks[0]
            print("vm edit link: ", json.dumps(vmEditLink, indent=2))

            # Add the nat rules to the original VM object
            vm.json["natrules"] = addnatrules[:]

            # Send a PUT request to the VM edit link and update the VM
            code, vmaddnr = vm.follow('edit').put(
                headers={'accept': 'application/vnd.abiquo.acceptedrequest+json',
                         'content-type': 'application/vnd.abiquo.virtualmachine+json'},
                data=json.dumps(vm.json))

            # Response code should be 2XX depending on deployed/undeployed VM
            print("Update VM, response code is: ", code)


# Calls the main() function
if __name__ == '__main__':
    main()
