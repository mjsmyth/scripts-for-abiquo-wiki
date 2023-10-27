#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*
'''#
# This script reads files from the input_files directory:
# - Copy privileges from Abiquo UI and save with headers and privileges indented 1 space
# - UI labels file (get from /UI/app/lang/lang_en_US_labels.json from current
#  branch in your platform/ui repo
# - privileges from Abiquo API
# - an extra text file (process_privileges_extratext.txt)
# - It uses a mustache template (pystache module) 
# It creates privileges_out_DATE.txt - a wiki storage format table 
# and updates the Abiquo wiki for the version
# NB: check that the privileges in Abiquo UI file is equal to
# the number of rows in privilege table in Abiquo DB
# select * from privilege where ROLE = 1 (cloud admin has all privileges);
#
'''

import re
import json
import os
import collections
import codecs
import sys
import pystache
import requests
from datetime import datetime
import abqdoctools as adt

# reload(sys)
# sys.setdefaultencoding('utf-8')


class rolec:
    '''Role data structure with no methods left'''
    def __init__(self, akey, aname, ainitials, aformat):
        self.rkey = akey
        self.rname = aname
        self.rinitials = ainitials
        self.rformat = aformat


def open_if_not_existing(filename):
    '''Open file if it doesn't exist already'''
    try:
        file_def = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except:
        print(f"File {filename} already exists")
        return None
    file_object = os.fdopen(file_def, "w")
    return file_object


def get_extra_text(input_subdir, extfile):
    '''Read extra text file'''
    with open(os.path.join(input_subdir, extfile), encoding='UTF-8') as extratextfile:
        extlines = (extline.rstrip() for extline in extratextfile)
        extratext = {}
        for ext_orig in extlines:
            # print (ext_orig)
            extlist = ext_orig.split("|")
            extkey = extlist[0]
            extkey = extkey.strip()
            exttext = extlist[1]
            exttext = exttext.strip()
            extratext[extkey] = exttext
    return extratext


def create_roles():
    '''create role objects'''
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


def create_role_header(rollers):
    '''create role headers'''
    roleheading = []
    for rrr in rollers:
        rhd = {}
        rhd["roleheadform"] = rollers[rrr].rformat
        rhd["rolename"] = rollers[rrr].rname
        roleheading.append(rhd)
    return roleheading


def do_api_request(api_auth, api_url, api_accept):
    '''Make a request to Abiquo API'''
    # print (api_url)
    api_headers = {}
    api_headers['Accept'] = api_accept
    api_headers['Authorization'] = api_auth
    api_data = requests.get(api_url, headers=api_headers, verify=False, timeout=60).json()
    # print (api_data)
    return api_data


def get_api_privs(api_auth, api_ip):
    '''Get privileges from Abiquo API'''
    # Get role data from the API of a fresh Abiquo
    # First get roles and IDs, then get privileges of each role
    # rol_data = {}
    roles_data = {}
    # get all base role names and ID numbers
    api_url = 'https://' + api_ip + '/api/admin/roles/'
    api_accept = 'application/vnd.abiquo.roles+json'
    default_roles_response = do_api_request(api_auth, api_url, api_accept)
    default_roles_list = []
    default_roles = {}
    default_roles_list = default_roles_response['collection']
    # create a dictionary with the roles and their IDs
    for def_role in default_roles_list:
        default_roles[def_role['name']] = def_role['id']
    # run through the dictionary and get the privileges for each role
    for def_rolename, def_roleid in iter(default_roles.items()):
        api_url = 'https://' + api_ip + '/api/admin/roles/' + \
            str(def_roleid) + '/action/privileges'
        print (api_url)
        api_accept = 'application/vnd.abiquo.privileges+json'
        default_privileges_response = do_api_request(api_auth,
                                                     api_url, api_accept)
        # create a list like the sql list, which is a privilege
        # with a list of roles
        default_privileges_list = []
        default_privileges_list = default_privileges_response['collection']
        for def_priv in default_privileges_list:
            pname = def_priv['name']
            if pname in roles_data:
                roles_data[pname].append(def_rolename)
            else:
                roles_data[pname] = [def_rolename]
    #            for rrr in roles_data:
    #                print ("rrr: %s" % rrr)
    return roles_data


def get_gui_labels(input_gitdir, ui_label_file):
    '''Get Abiquo UI labels'''
    privlabels = {}
    privnames = {}
    privdescs = {}
    privgroups = {}
    json_data = open(os.path.join(input_gitdir, ui_label_file))
    data = json.load(json_data)
#   labelkeys = sorted(data.keys())
#   remove sort
    labelkeys = data.keys()
    for labelkey_orig in labelkeys:
        labelkey = labelkey_orig.split(".")
        pri_group = labelkey[0]
        if pri_group == "privilegegroup":
            pri_group_key = labelkey[1]
            if pri_group_key != "allprivileges":
                privgroups[pri_group_key] = data[labelkey_orig]
                # print ("privilege group: ", labelkey)
        elif pri_group == "privilege":
            pri_desc = labelkey[1]
            if pri_desc == "description":
                pri_desc_key= labelkey[2]
                privdescs[pri_desc_key] = data[labelkey_orig]
                # print("privilege description: ", labelkey)
            elif pri_desc != "details":
                privlabels[pri_desc] = pri_desc
                privnames[pri_desc] = data[labelkey_orig]
                # print("privilege: ", labelkey)
    return (privlabels, privnames, privdescs, privgroups)


def new_order_by_ui_text_file(todays_date):
    '''Order privileges from text file of UI list'''
    ui_order = collections.OrderedDict()
    ui_cat = ""
    order_file = codecs.open('input_files/privilege_ui_order_'
                            + todays_date 
                            + ".txt", 'r', 'utf-8')
    for line in order_file:
        if not re.match(r"\s", line):
            ui_cat = line.strip()
            if ui_cat not in ui_order:
                ui_order[ui_cat] = []
        else:
            if not re.match(" All privileges", line):
                privilege = line.strip()
                ui_order [ui_cat].append(privilege)
    return ui_order 


def process_roles(todays_date, input_gitdir, input_subdir, output_subdir):
    '''Get roles from API and format into table'''
    #From the API get a list of privileges with roles
    # api_privs = {} 
    api_auth = input("Enter API authorization, e.g. Basic XXXXXX: ")
    api_ip = input("Enter API address, e.g. api.abiquo.com: ")

    sqlroles = get_api_privs(api_auth, api_ip)

    # From the UI get the privilege names and descriptions,
    # with privilege appLabel as key
    ui_label_file = 'lang_en_US_labels.json'
    (privlabels, privnames, privdescs, privgroups) = \
        get_gui_labels(input_gitdir, ui_label_file)

    # From a list of roles that we set, create roles and role headers
    rollers = create_roles()
    rheaders = create_role_header(rollers)

    # From the extra text file, get extra text
    extfile = 'process_privileges_extratext.txt'
    extratext = {}
    extratext = get_extra_text(input_subdir, extfile)

    # Create a dictionary of privileges
    ppdict = {}
    name_label_dict = {}

    # From a text file grabbed from the UI screen, get the groups and the order
    ui_order_er = collections.OrderedDict()
    ui_order_er = new_order_by_ui_text_file(todays_date)

    priv_full_descs = {}
    priv_full_roles = {}
    # Use the roles retrieved from the API to create a privilege data object
    for pri in sqlroles:
        # create a privilege data object
        if pri in extratext:
            priv_full_descs[pri] = privdescs[pri] + ". " + extratext[pri]
        # roleslist = []
        for rol in rollers:
            if rol in sqlroles[pri]:
                if pri not in priv_full_roles:
                    priv_full_roles[pri] = []
                priv_full_roles[pri].append(rol)
        # info = ""

    # For each privilege from the UI files
    for plabel in privlabels:
        # create a privilege names key dictionary for priv labels
        # because everything else is keyed on priv labels
        name_label_dict[privnames[plabel]] = plabel

    # Process the privileges and create a privilege json
    for plabel in privlabels:
        privi = {}
        privi["guiLabel"] = privnames[plabel]
        privi["appTag"] = plabel
        privi["privilege"] = privdescs[plabel]
        privi["roles"] = []
        for rox in rollers:
            role = {}
            role['role'] = {}
            rolex = {}
            rolex["roleformat"] = rollers[rox].rformat
            role_mark = {}
            if plabel in priv_full_roles:
                if rox in priv_full_roles[plabel]:
                    role_mark["roleMark"] = "X"
                    rolex["rolehas"] = role_mark
                role['role'] = rolex
                privi["roles"].append(role)
        privi["info"] = {}
        ppdict[plabel] = privi

    # Working in order through the groups and the privileges,
    # get all the info together to print it out
    categories = []
    for group in ui_order_er:
        category = {}
        category["category"] = group
        category["roleheader"] = rheaders
        category["entries"] = []
        for priv in ui_order_er[group]:
            if priv in name_label_dict:
                privlabel = name_label_dict[priv]
            else:
                print("error with UI label: ", priv)
            category["entries"].append(ppdict[privlabel])
        categories.append(category)

    privilege_out = {}
    privilege_out["categories"] = categories
    return privilege_out


def main():
    # todays_date = datetime.today().strftime('%Y-%m-%d')
    todays_date = "2023-10-26"
    input_gitdir = '../../platform/ui/app/lang'
    input_subdir = 'input_files'
    output_subdir = 'output_files'
    operation = "replacetable"
    privs_out_file = "privileges_out_" + todays_date + ".txt"
    ef = open_if_not_existing(os.path.join(output_subdir,
                                           privs_out_file))
    use_existing_file = ""
    if ef is None:
        use_existing_file = input("Use existing file = default (y) "
                                   "or overwrite file (o) or quit (q): ")
        if use_existing_file == "q":
            sys.exit()
        elif use_existing_file == "o":
            ef = open(os.path.join(output_subdir,privs_out_file), 'w')

    if ef:
        privilege_out = process_roles(todays_date, input_gitdir, input_subdir, output_subdir)
        with open(os.path.join(output_subdir,
                "privtestout" + todays_date + ".txt"), 'w') \
                as ofile:
            for cpr in privilege_out["categories"]:
                ofile.write(json.dumps(cpr))
        # do the mustache render
        # mustache_template = codecs.open("wiki_privileges_template_"
        #     + td + ".mustache", 'r', 'utf-8').read()
        mustache_template = codecs.open("wiki_privileges_template.mustache",
                                       'r', 'utf-8').read()
        # mustache_template = open("wiki_privileges_template.mustache", "r").read()
        #    efo = pystache.render(mustache_template, privilege_out).encode('utf-8',
        #        'xmlcharrefreplace')
        efo = pystache.render(mustache_template, privilege_out)
        # efo = pystache.render(mustache_template, privilege_out)

        ef.write(efo)
        ef.close()

    wiki_content = ""

    with open(os.path.join(output_subdir, privs_out_file), 'r') as f_wiki:
        wiki_content = f_wiki.read()

    # Get user credentials and space
    site_url = input("Confluence Cloud site URL, with protocol,"
                     + " and wiki, and exclude final slash, "
                     + "e.g. https://abiquo.atlassian.net/wiki: ")
    cloud_username = input("Cloud username: ")
    pwd = input("Cloud token string: ")
    spacekey = input("Space key: ")

    release_version = input("Release version, e.g. v463: ")
    print_version = input("Release print version, e.g. 4.6.3: ")
    wiki_format = False
    update_page_title = "Privileges"
    table_replace_string = r'<table(.*?)</table>'

# def updateWiki(update_page_title, wiki_content, wiki_format, 
#                site_url,cloud_username, pwd, spacekey, 
#                table_replace_string,
#                release_version, print_version, operation):


    status = adt.updateWiki(update_page_title, wiki_content, wiki_format,
                            site_url, cloud_username, pwd, spacekey,
                            release_version, print_version, operation)
    if status is True:
        print("Page ", update_page_title,
              " for in the draft documentation was updated sucessfully!")
    else:
        print("Page ", update_page_title,
              " for this version's draft was not updated successfully!")


# Calls the main() function
if __name__ == '__main__':
    main()
