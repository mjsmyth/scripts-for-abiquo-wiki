#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*
#
# This script reads files from the input_files directory:
# - UI labels file (get from /UI/app/lang/lang_en_US_labels.json from current branch in your platform/ui repo
# - database privileges information (run process_privileges.sql on the latest Abiquo DB to create process_privileges_sql.txt)
# - an extra text file (process_privileges_extratext.txt)
# It creates wiki_privileges.txt - a wiki storage format table for pasting into Privileges page of the wiki
# NB: check that privs_processed which is written to standard out is equal to 
# the number of rows in privilege table in Abiquo DB
# select * from privilege;
#


import re
import json
import os
import collections
import pystache
import codecs
import requests
from datetime import datetime
import abqdoctools as adt

# reload(sys)
# sys.setdefaultencoding('utf-8')


class rolec:
    def __init__(self, akey, aname, ainitials, aformat):
        self.rkey = akey
        self.rname = aname
        self.rinitials = ainitials
        self.rformat = aformat


def open_if_not_existing(filename):
    try:
        fd = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except:
        print ("File: %s already exists" % filename)
        return None
    fobj = os.fdopen(fd, "w")
    return fobj


def get_extra_text(input_subdir, extfile):
    extlines = (extline.rstrip() for extline in open(
        os.path.join(input_subdir, extfile)))
    extratext = {}
    for ext_orig in extlines:
        # print (ext_orig)
        extlist = ext_orig.split("|")
        extkey = extlist[0]
        extkey = extkey.strip()
        exttext = extlist[1]
        exttext = exttext.strip()
        extratext[extkey] = exttext
    return(extratext)


def createRoles():
    # This could be read in from a file
    rollers = collections.OrderedDict()
    # r = role(akey,aname,ainitials,aformat)
    rollers["CLOUD_ADMIN"] = rolec("CLOUD_ADMIN", "Cloud Admin", "CA", "red")
    rollers["ENTERPRISE_ADMIN"] = rolec("ENTERPRISE_ADMIN",
                                        "Ent Admin", "EA", "yellow")
    rollers["USER"] = rolec("USER", "Ent User", "EU", "green")
    rollers["ENTERPRISE_VIEWER"] = rolec("ENTERPRISE_VIEWER",
                                         "Ent Viewer", "EV", "blue")
    return rollers


def createRoleHeader(rollers):
    roleheading = []
    for rrr in rollers:
        rhd = {}
        rhd["roleheadform"] = rollers[rrr].rformat
        rhd["rolename"] = rollers[rrr].rname
        roleheading.append(rhd)
    return roleheading


def do_api_request(apiAuth, apiIP, apiUrl, apiAccept):
    print (apiUrl)
    apiHeaders = {}
    apiHeaders['Accept'] = apiAccept
    apiHeaders['Authorization'] = apiAuth
    r = requests.get(apiUrl, headers=apiHeaders, verify=False).json()
    print (r)
    return r


def get_api_privs(apiAuth, apiIP):
    # Get role data from the API of a fresh Abiquo
    # First get roles and IDs, then get privileges of each role
    # rol_data = {}
    roles_data = {}
    # get all base role names and ID numbers
    apiUrl = 'https://' + apiIP + '/api/admin/roles/'
    apiAccept = 'application/vnd.abiquo.roles+json'
    default_roles_response = do_api_request(apiAuth, apiIP, apiUrl, apiAccept)
    default_roles_list = []
    default_roles = {}
    default_roles_list = default_roles_response['collection']
    # create a dictionary with the roles and their IDs
    for dr in default_roles_list:
        default_roles[dr['name']] = dr['id']
    # run through the dictionary and get the privileges for each role
    for drname, drid in iter(default_roles.items()):
        apiUrl = 'https://' + apiIP + '/api/admin/roles/' + \
            str(drid) + '/action/privileges'
        print (apiUrl)
        apiAccept = 'application/vnd.abiquo.privileges+json'
        default_privileges_response = do_api_request(apiAuth, apiIP,
                                                     apiUrl, apiAccept)
        # create a list like the sql list, which is a privilege
        # with a list of roles
        default_privileges_list = []
        default_privileges_list = default_privileges_response['collection']
        for rp in default_privileges_list:
            pname = rp['name']
            if pname in roles_data:
                roles_data[pname].append(drname)
            else:
                roles_data[pname] = [drname]
    #            for rrr in roles_data:
    #                print ("rrr: %s" % rrr)
    return roles_data


def get_gui_labels(input_gitdir, UIlabelfile):
    privlabels = {}
    privnames = {}
    privdescs = {}
    privgroups = {}
    json_data = open(os.path.join(input_gitdir, UIlabelfile))
    data = json.load(json_data)
#   labelkeys = sorted(data.keys())
#   remove sort
    labelkeys = data.keys()
    for labelkey_orig in labelkeys:
        labelkey = labelkey_orig.split(".")
        pg = labelkey[0]
        if pg == "privilegegroup":
            pgk = labelkey[1]
            if pgk != "allprivileges":
                privgroups[pgk] = data[labelkey_orig]
                # print ("privilege group: ", labelkey)
        elif pg == "privilege":
            pd = labelkey[1]
            if pd == "description":
                pdk = labelkey[2]
                privdescs[pdk] = data[labelkey_orig]
                # print("privilege description: ", labelkey)
            elif pd != "details":
                privlabels[pd] = pd
                privnames[pd] = data[labelkey_orig]
                # print("privilege: ", labelkey)
    return (privlabels, privnames, privdescs, privgroups)


def newOrderByUItextFile(td):
    uiOrd = collections.OrderedDict()
    uiCat = ""
    orderFile = codecs.open('input_files/privilege_ui_order_' + td
                            + ".txt", 'r', 'utf-8')
    for line in orderFile:
        if not re.match(r"\s", line):
            uiCat = line.strip()
            if uiCat not in uiOrd:
                uiOrd[uiCat] = []
        else:
            if not re.match(" All privileges", line):
                privilege = line.strip()
                uiOrd[uiCat].append(privilege)
    return uiOrd


def main():
    todaysDate = datetime.today().strftime('%Y-%m-%d')
    # td = "2022-08-17"
    input_gitdir = '../../platform/ui/app/lang'
    input_subdir = 'input_files'
    output_subdir = 'output_files'

    # From the API get a list of privileges with roles
    # api_privs = {}
    apiAuth = input("Enter API authorization, e.g. Basic XXXXXX: ")
    apiIP = input("Enter API address, e.g. api.abiquo.com: ")

    sqlroles = get_api_privs(apiAuth, apiIP)

    # From the UI get the privilege names and descriptions,
    # with privilege appLabel as key
    UIlabelfile = 'lang_en_US_labels.json'
    (privlabels, privnames, privdescs, privgroups) = \
        get_gui_labels(input_gitdir, UIlabelfile)

    # From a list of roles that we set, create roles and role headers
    rollers = createRoles()
    rheaders = createRoleHeader(rollers)

    # From the extra text file, get extra text
    extfile = 'process_privileges_extratext.txt'
    extratext = {}
    extratext = get_extra_text(input_subdir, extfile)

    # Create a dictionary of privileges
    ppdict = {}
    nameLabelDict = {}

    # From a text file grabbed from the UI screen, get the groups and the order
    uiOrder = collections.OrderedDict()
    uiOrder = newOrderByUItextFile(todaysDate)

    privFullDescs = {}
    privFullRoles = {}
    # Use the roles retrieved from the API to create a privilege data object
    for pp in sqlroles:
        # create a privilege data object
        if pp in extratext:
            privFullDescs[pp] = privdescs[pp] + ". " + extratext[pp]
        # roleslist = []
        for ro in rollers:
            if ro in sqlroles[pp]:
                if pp not in privFullRoles:
                    privFullRoles[pp] = []
                privFullRoles[pp].append(ro)
        # info = ""

    # For each privilege from the UI files
    for plabel in privlabels:
        # create a privilege names key dictionary for priv labels
        # because everything else is keyed on priv labels
        nameLabelDict[privnames[plabel]] = plabel

    # Process the privileges and create a privilege json
    for plabel in privlabels:
        privi = {}
        privi["guiLabel"] = privnames[plabel]
        privi["appTag"] = plabel
        privi["privilege"] = privdescs[plabel]
        privi["roles"] = []
        for rx in rollers:
            role = {}
            role['role'] = {}
            rolex = {}
            rolex["roleformat"] = rollers[rx].rformat
            roleMark = {}
            if plabel in privFullRoles:
                if rx in privFullRoles[plabel]:
                    roleMark["roleMark"] = "X"
                    rolex["rolehas"] = roleMark
                role['role'] = rolex
                privi["roles"].append(role)
        privi["info"] = {}
        ppdict[plabel] = privi

    # Working in order through the groups and the privileges,
    # get all the info together to print it out
    categories = []
    for group in uiOrder:
        category = {}
        category["category"] = group
        category["roleheader"] = rheaders
        category["entries"] = []
        for priv in uiOrder[group]:
            if priv in nameLabelDict:
                privlabel = nameLabelDict[priv]
            else:
                print("error with UI label: ", priv)
            category["entries"].append(ppdict[privlabel])
        categories.append(category)

    privilege_out = {}
    privilege_out["categories"] = categories

    with open(os.path.join(output_subdir,
                           "privtestout" + todaysDate + ".txt"), 'w') \
            as ofile:
        for cpr in privilege_out["categories"]:
            ofile.write(json.dumps(cpr))
    # do the mustache render
    # mustacheTemplate = codecs.open("wiki_privileges_template_"
    #     + td + ".mustache", 'r', 'utf-8').read()
    mustacheTemplate = codecs.open("wiki_privileges_template.mustache",
                                   'r', 'utf-8').read()
    # mustacheTemplate = open("wiki_privileges_template.mustache", "r").read()
    #    efo = pystache.render(mustacheTemplate, privilege_out).encode('utf-8',
    #        'xmlcharrefreplace')
    efo = pystache.render(mustacheTemplate, privilege_out)
    # efo = pystache.render(mustacheTemplate, privilege_out)
    privilegesOutFile = "privileges_out_" + todaysDate + ".txt"
    ef = open_if_not_existing(os.path.join(output_subdir,
                                           privilegesOutFile))
    if ef:
        ef.write(efo)
        ef.close()

    wikiContent = ""

    with open(os.path.join(output_subdir, privilegesOutFile), 'r') as f:
        wikiContent = f.read()

    # Get user credentials and space
    site_URL = input("Confluence Cloud site URL, with protocol,"
                     + " and wiki, and exclude final slash, "
                     + "e.g. https://abiquo.atlassian.net/wiki: ")
    cloud_username = input("Cloud username: ")
    pwd = input("Cloud token string: ")
    spacekey = input("Space key: ")

    release_version = input("Release version, e.g. v463: ")
    print_version = input("Release print version, e.g. 4.6.3: ")
    wikiFormat = False
    updatePageTitle = "Privileges"
    tableReplaceString = r'<table(.*?)</table>'
    status = adt.updateWiki(updatePageTitle, wikiContent, wikiFormat,
                            site_URL, cloud_username, pwd, spacekey,
                            tableReplaceString,
                            release_version, print_version)
    if status is True:
        print("Page ", updatePageTitle,
              " for this version's draft was updated sucessfully!")
    else:
        print("Page ", updatePageTitle,
              " for this version's draft was not updated successfully!")


# Calls the main() function
if __name__ == '__main__':
    main()
