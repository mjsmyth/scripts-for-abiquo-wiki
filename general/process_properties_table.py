#!/usr/bin/python3 -tt
'''
# This script formats the abiquo.properties file for documentation.
# It creates a storage format version.
# It is also possible to create a wiki markup version
#
# The script requires:
# - the Abiquo Python client installed with pip3
# - access to the Abiquo API (input token and URL)
# - access to platform files (hardcoded location)
# - mustache template file for storage format
# - preformatted text file for abiquo.guest.password.length property
#
# There are some values hardcoded in the functions:
# - main
# - fix_defaults
#
# Good luck!
'''


import re
import copy
from datetime import datetime
import os
import json
import codecs
from collections import Counter
from pathlib import Path
from abiquo.client import Abiquo
from abiquo.auth import TokenAuth
import pystache


# For test environment disable SSL warning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_plugins(api):
    '''Get plugins: hypervisor types, network devices,
                 backup devices, draas devices'''
    code, hypervisor_types_list = api.config.hypervisortypes.get(
        headers={'Accept': 'application/vnd.abiquo.hypervisortypes+json'})
    print("Get hypervisor types. Response code is: ", code)
    hypervisor_types = [ht["name"].lower()
                       for ht in hypervisor_types_list.json["collection"]]

    code, device_types_list = api.config.devicetypes.get(
        headers={'Accept': 'application/vnd.abiquo.devicetypes+json'})
    print("Get device types. Response code is: ", code)
    device_types = [dt["name"].lower()
                   for dt in device_types_list.json["collection"]]

    code, backup_plugin_types_list = api.config.backupplugintypes.get(
        headers={'Accept': 'application/vnd.abiquo.backupplugintypes+json'})
    print("Get backup plugin types. Response code is: ", code)
    backup_plugin_types = [bpt["type"].lower()
                         for bpt in backup_plugin_types_list.json["collection"]]

    code, draas_plugin_types_list = api.config.draasplugintypes.get(
        headers={'Accept': 'application/vnd.abiquo.draasplugintypes+json'})
    print("Get DRaaS device types. Response code is: ", code)
    draas_plugin_types = [drpt["type"].lower()
                        for drpt in draas_plugin_types_list.json["collection"]]
    return (hypervisor_types, device_types, backup_plugin_types, draas_plugin_types)


def sort_for_output(properties_dict):
    ''' When sorting take into consideration sortName
    # For com.abiquo.foo.bar, sortname is abiquo.foo.bar'''
    for p_name in properties_dict.keys():
        if not properties_dict[p_name]["sortName"]:
            properties_dict[p_name]["sortName"] = copy.deepcopy(
                properties_dict[p_name]["property"])
    sorted_prop_dict = dict(sorted(properties_dict.items(),
                                 key=lambda x: x[1]["sortName"].lower()))
    return sorted_prop_dict


def escape_wiki_markup_name(prop_name):
    '''Escape wiki markup chars in property name'''
    if "{" in prop_name:
        prop_name = re.sub(r"\{", r"\\{", prop_name)
    if "[" in prop_name:
        prop_name = re.sub(r"\[", r"\\{", prop_name)
    if "]" in prop_name:
        prop_name = re.sub(r"\]", r"\}", prop_name)
    return prop_name


def escape_wiki_markup_desc(description):
    '''Escape wiki markup chars in property description'''
    if "*" in description:
        description = re.sub(r'\*', r'\\*', description)
    if "-" in description:
        description = re.sub(r'\-', r'\\-', description)
    if "[" in description:
        description = re.sub(r'\[', r'\\-', description)
    if "{" in description:
        description = re.sub(r'\{', r'\\-', description)
    return description


def process_default_wiki(propv, newline, propv_default, 
                         plugin_blank_defaults, default_list):
    '''Process property defaults including dict values'''
    if isinstance(propv["default"], str):
        if "http" in propv["default"] or ("{" or "[") in propv["default"]:
            default_list = newline + "Default: {newcode}" + \
                copy.deepcopy(propv["default"]) + "{newcode}"
        else:
            if re.search(r"\S+", propv["default"]):
                default_list = newline + "_Default: " + copy.deepcopy(
                    propv["default"]) + "_"
                if "*" in default_list:
                    default_list = re.sub(r"\*", r"\\*", default_list)
    if isinstance(propv["default"], dict):
        value, count = Counter(
            propv_default.values()).most_common(1)[0]
        # Count the number of times the most common value occurs
        if count > 1:
            # More than one property has this value
            # If it's not empty, make it the general default
            if re.search(r"\S+", value):
                default_list = newline + "_Default: " + value[:]
        if count == 1:
            # If the most common only occurs once,
            # the properties all have their own values
            # So don't display a general default
            default_list = newline + "_Default: "
        for plugin, defv in propv_default.items():
            if count > 1:
                # If more than one property has the same value,
                # but this property is different, then display it
                if defv != value:
                    if re.search(r"\S+", defv):
                        default_list += newline + "\\- " + plugin + \
                            " = " + defv
            if count == 1:
                # If all properties have different defaults,
                # then display them all
                if re.search(r"\S+", defv) or \
                        plugin in plugin_blank_defaults:
                    # A valid default is not empty or has an exemption
                    default_list += newline + "\\- " + plugin + \
                        " = " + defv
        default_list += "_"
    return default_list


def process_default_storage_format(propv, newline, propv_default, 
                                   plugin_blank_defaults, 
                                   default_general_storage_format,
                                   default_plugins_storage_format):
    '''Process property defaults including dict values'''
    default_plugins_storage_format = [] 
    if isinstance(propv["default"], str):
        default_general_storage_format = copy.deepcopy(propv["default"])
    if isinstance(propv["default"], dict):
        value, count = Counter(
            propv_default.values()).most_common(1)[0]
        # Count the number of times the most common value occurs
        if count == 1:
            # If the most common only occurs once,
            # the properties all have their own values
            # So don't display a general default
            default_general_storage_format = ""
        if count > 1:
            # More than one property has this value
            # If it's not empty, make it the general default
            if re.search(r"\S+", value):
                default_general_storage_format = value[:]
        for plugin, defv in propv_default.items():
            if count > 1:
                # If more than one property has the same value,
                # but this property is different, then display it
                if defv != value:
                    if re.search(r"\S+", defv):
                        plugin_default = plugin + " = <code>" + defv + "</code>"
                        default_plugin_item = "<li>" + plugin_default + "</li>"
                        default_plugins_storage_format.append(
                            {"plugindefault": copy.deepcopy(default_plugin_item)})
            if count == 1:
                # If all properties have different defaults,
                # then display them all
                if re.search(r"\S+", defv) or \
                        plugin in plugin_blank_defaults:
                    # A valid default is not empty or has an exemption
                    plugin_default = plugin + " = <code>" + defv +"</code>"
                    default_plugin_item = "<li>" + plugin_default + "</li>"
                    default_plugins_storage_format.append({"plugindefault": copy.deepcopy(default_plugin_item)})
        if len(default_plugins_storage_format) > 0:
            default_plugins_list_start = "<ul>" + default_plugins_storage_format[0]["plugindefault"]
            default_plugins_storage_format[0]["plugindefault"] = copy.deepcopy(default_plugins_list_start)
            default_plugins_list_end = default_plugins_storage_format[-1]["plugindefault"] + "</ul>"
            default_plugins_storage_format[-1]["plugindefault"] = copy.deepcopy(default_plugins_list_end)
        else:
            default_plugins_storage_format = ""
    return (default_general_storage_format, default_plugins_storage_format)


def prepare_for_wiki(pSDict, profile_columns,
                     profile_images, newline,
                     webrefs, default_profiles,
                     plugin_blank_defaults):
    '''# Prepare a dict with the properties to document'''
    pTPD = {}
    # previousCategory = ""
    anchor = ""
    propv_default = {}
    for pname, propv in pSDict.items():
        pTPD[pname] = {}
        # Prepare the Property entry
        pluginList = ""
        # if propv["category"] != previousCategory:
        #     anchor = " {anchor: " + copy.deepcopy(propv["category"]) + "} "
        # else:
        #     anchor = ""
        # previousCategory = copy.deepcopy(propv["category"])
        property_name = propv["property"]
        property_name = escape_wiki_markup_name(property_name)
        pluginList = ""
        if "default" in propv:
            if type(propv["default"]) is dict:
                propv_default = dict(sorted(propv["default"].items()))
                for plugin in propv_default.keys():
                    pluginList += newline + "\\- " + plugin
        pTPD[pname]["Property"] = anchor + "*" + property_name + "* " + pluginList

        # Prepare the default entry
        default_list = ""
        # Note this is not correct but if anyone is using hyperv, let's
        # hope they know what they are doing
        if "C:" in propv:
            propv = re.sub("\\", "/", propv)
        if "default" in propv:
            default_list =  process_default_wiki(propv,  newline, 
                propv_default, plugin_blank_defaults, default_list)

        # Prepare values
        valuesList = ""
        if "validvalues" in propv:
            valuesList = newline + "_Valid values: " + \
                propv["validvalues"] + "_"

        # Prepare description
        description = ""
        if "description" in propv:
            description = copy.deepcopy(propv["description"])
            if "http" in description:
                # put examples of nonexistent websites in code blocks
                foundWebref = re.search(webrefs, description)
                if foundWebref or "<" in description:
                    description = re.sub(r"((http:|https:)(\S*)?)",
                                         r'{newcode}\1{newcode}',
                                         description)
                else:
                    description = re.sub(r"((http:|https:)(\S*)?)",
                                         r'[\1]',
                                         description)
            else:
                description = escape_wiki_markup_desc(description)
                # todo check if default has actual characters in it
                # todo etc.

        pTPD[pname]["Descripton"] = description + \
            valuesList + default_list

        # Prepare profiles
        if "profiles" in propv:
            for profile in default_profiles:
                pTPD[pname][profile] = " "
            for profileName, profileImage in profile_images.items():
                if profileName in propv["profiles"]:
                    if profileName in profile_columns:
                        column = profile_columns[profileName]
                        pTPD[pname][column] = copy.deepcopy(
                            profile_images[profileName])
    return pTPD


def prepare_for_storage_format(pSDict, profile_columns, newline,
                               webrefs, default_profiles,
                               plugin_blank_defaults,
                               profile_storage_format):
    '''# Prepare a dict with the properties to document'''
    pSFD = {}
    previousCategory = ""
    anchor = ""
    propv_default = {}
    prop_color = "#ffffff"
    print(len(pSDict))
    for pname, propv in pSDict.items():
        pSFD[pname] = {}
        # Prepare the Property entry
        plugin_list = []
        # if propv["category"] != previousCategory:
        #     anchor = " {anchor: " + copy.deepcopy(propv["category"]) + "} "
        # else:
        #     anchor = ""
        # previousCategory = copy.deepcopy(propv["category"])
        if propv["category"] != previousCategory:
            if prop_color == '\"#e6fcff\"':
                prop_color = '\"#ffffff\"'
            else:
                prop_color = '\"#e6fcff\"'
        previousCategory = copy.deepcopy(propv["category"])
        property_name = propv["property"]
        # property_name = escape_wiki_markup_name(property_name)
        plugin_list = []
        ## make a list of plugin names under the property itself ##
        if "default" in propv:
            if isinstance(propv["default"], dict):
                propv_default = dict(sorted(propv["default"].items()))
                for plugin in propv_default.keys():
                    plugin_list.append("<li>" + plugin + "</li>")
                plugin_list_start = "<ul>" + plugin_list[0]
                plugin_list[0] = copy.deepcopy(plugin_list_start)
                plugin_list_end = plugin_list[-1] + "</ul>"
                plugin_list[-1] = copy.deepcopy(plugin_list_end)  
        pSFD[pname]["property"] = anchor + "<strong>" + property_name + "</strong>" 
        pSFD[pname]["propcolor"] = prop_color[:]
        if len(plugin_list) > 0:
            pSFD[pname]["pluginlist"] = [] 
            for plugin_item in plugin_list: 
                pSFD[pname]["pluginlist"].append({"plugin": plugin_item})
        else:
            pSFD[pname]["pluginlist"] = ""
        # Prepare the default entry
        default_general_storage_format = ""
        default_plugins_storage_format = []
        default_general_storage_format, default_plugins_storage_format = \
            process_default_storage_format(propv, newline, 
                                           propv_default, plugin_blank_defaults, 
                                           default_general_storage_format,
                                           default_plugins_storage_format)

        # Prepare description
        description = ""
        if "description" in propv:
            # print("propv[desc] ", propv["description"])
            description = copy.deepcopy(propv["description"])
        if "description" in propv and "usesMarkdown" not in propv:
            # print("description: ", description)
            if "<" in description:
                description = re.sub(r"<((\S)*?)>",r'{$\1}',description)
                # print ("desc no <: ", description)
            if "<" in description:
                description = re.sub(r"<",r"\<",description)
            if ">" in description:
                description = re.sub(r">",r"\>",description)
            if "http" in description:
                # put examples of nonexistent websites in code blocks
                found_web_ref = re.search(webrefs, description)
                if found_web_ref or r"{" in description:
                    print("DESCRIPTION: ", description)
                    description = re.sub(r"((http:|https:)(\S*)?)",
                                         r'<code>\1</code>',
                                         description)
                else:
                    # Process links
                    description = re.sub(r"((http:|https:)(\S*)?)",
                                         r'<a href="\1">\1</a>',
                                         description)

            if "\'\'" in description:
                # print("found a quote, which can contain spaces")
                # print(description)
                description = re.sub(r"\'\'(([\S\s])*?)\'\'", r"<code>\1</code>",
                                     description)
                # print("description without quotes: " description)
                # description = escape_wiki_markup_desc(description)
            if "\'" in description:
                description = re.sub(r"\'(([\S\s])*?)\'", r"<code>\1</code>",
                                     description)
        pSFD[pname]["description"] = copy.deepcopy(description)
       
        pSFD[pname]["validvalues"] = []
        if "validvalues" in propv:
            valid_value_dict = {"validvalue": propv["validvalues"]}
            pSFD[pname]["validvalues"].append(valid_value_dict)
        else:
            pSFD[pname]["validvalues"] = ""

        pSFD[pname]["maindefault"] = copy.deepcopy(default_general_storage_format)
        if len(default_plugins_storage_format) > 0:
            pSFD[pname]["defaultlist"] = default_plugins_storage_format[:]
        else:
            pSFD[pname]["defaultlist"] = ""
        # Prepare profiles
        if "profiles" in propv:
            for profile in default_profiles:
                pSFD[pname][profile] = ""
            for profile_name in profile_storage_format.keys():
                if profile_name in propv["profiles"]:
                    if profile_name in profile_columns:
                        column = profile_columns[profile_name]
                        pSFD[pname][column] = copy.deepcopy(
                            profile_storage_format[profile_name])
    print("Number of properties: ", len(pSFD))
    return pSFD


def fix_default(prop_name, default):
    ''' Some local defaults are replaced on filesystem during install
    # This should be in main() but hey'''
    new_default = default[:]
    if "datacenter.id" in prop_name:
        new_default = re.sub("default", "Abiquo", default)
    if "repositoryLocation" in prop_name:
        new_default = re.sub("127.0.0.1", r"{$REPO_IP_ADDRESS}", default)
    if "localhost" in default:
        new_default = re.sub("localhost", r"127.0.0.1", default)
    if "10.60.1.4" in default:
        new_default = re.sub("10.60.1.4", r"127.0.0.1", default)
    return new_default


def get_category(prop_name, category_dict):
    ''' We use categories to create anchors.
    # They are generally the second part of the name '''
    prop_sort_name = ""
    prop_cat = prop_name.split(".")
    if prop_cat[0] == "abiquo":
        property_cat = prop_cat[1][:]
    else:
        if prop_cat[0] == "com":
            if prop_cat[1] == "abiquo":
                property_cat = prop_cat[2][:]
                prop_sort_name = ".".join(prop_cat[1:])
            else:
                property_cat = prop_cat[2][:]
        else:
            property_cat = prop_cat[0][:]

    if property_cat in category_dict:
        return (copy.deepcopy(category_dict[property_cat]), prop_sort_name)
    return property_cat, prop_sort_name


def get_prop_name_default(currentProp):
    # Split property name into name and default
    # note that default can contain an equals sign
    if "=" in currentProp:
        splitProp = currentProp.split("=")
        defaultJoined = "=".join(splitProp[1:])
        propDefault = defaultJoined.strip()
        property_name = splitProp[0].strip()
        property_name = re.sub(r"^#?\s?", "", property_name)
    else:
        property_name = currentProp.strip()
        propDefault = ""
        property_name = re.sub(r"^#?\s?", "", property_name)
    propDefault = fix_default(property_name, propDefault)
    return property_name, propDefault


def processGroup(propList, group_types):
    # For properties that are in groups e.g. by plugins, metrics
    # Return group name and array of tags (e.g. "amazon") and defaults
    groupWorkList = []
    groupList = []
    groupTagList = []
    propDefDict = {}
    propGroupDefDict = {}
    grouprop_name = ""
    myGroup = ""

    for prop in propList:
        if "--" not in prop:
            property_name, propDefault = get_prop_name_default(prop)
            propDefDict[property_name] = propDefault

    for property_name in propDefDict:
        property_name.strip()
        property_nameList = property_name.split(".")
        # plugins etc are not in first two parts of name
        # filter list of plugins in each list
        # last_prop_nameList = property_nameList[2:]
        groupWorkList.extend(property_nameList[2:])
    reducedSet = set(groupWorkList)
    reducedList = list(reducedSet)

    for group, groupList in group_types.items():
        for x in reducedList:
            if x in groupList:
                groupTagList.append(x)
                myGroup = copy.deepcopy(group)

    if len(groupTagList) > 0:
        # Create a grouprop_name, which is abiquo.foo.{tagType}.bar
        # Store tags in an array
        for tag in groupTagList:
            for name, default in propDefDict.items():
                if tag in name:
                    propGroupDefDict[tag] = default
                    if not grouprop_name:
                        grouprop_name = name.replace(tag, myGroup)
        return grouprop_name, propGroupDefDict
    return "", ""


def get_property_values(propertyList, propertyDict,
                      group_types, category_dict):
    # For a property, get:
    # - Names, including group names with plugin or metric, etc.
    # - Names for sorting (e.g. no "com."),
    # - Categories (for anchors)
    # - and default values, which can be strings or arrays
    initial_prop_name, propDefault = get_prop_name_default(propertyList[0])
    propertyDict["category"], propertyDict["sortName"] = get_category(
        initial_prop_name, category_dict)
    if len(propertyList) == 1:
        propertyDict["property"] = initial_prop_name
        propertyDict["default"] = propDefault
    else:
        propertyDict["property"], propertyDict["default"] = processGroup(
            propertyList, group_types)
    return(propertyDict)


def process_comment(commentList, newline, 
                    usesMarkdown, process_properties_formatted):
    '''# Process the description of the property from the
    # Commented lines that aren't properties'''
    description = ""
    if usesMarkdown:
        # Previously, for Markdown comments, replace newlines
        for comment in commentList[:-1]:
            description += comment.strip("#") + newline
        description += commentList[-1].strip("#")
        file = open(process_properties_formatted, "r")
        content = file.read()
        print(content)
        file.close()
        description = content[:]
    else:
        for comment in commentList:
            description += comment.strip("#")
    return(description.strip())


def process_valid(description):
    # Get the Valid values supplied by devs
    # Remove this from the description
    found_valid = ""
    new_description = description[:]
    search_valid = r"(?<=Valid values)[\s]*?[:]?[\s]*?(.*)$"
    found_valid = re.search(search_valid, description)
    replace_valid = "Valid values" + found_valid.group(0)
    new_description = re.sub(replace_valid, "", description)
    valid_values = found_valid.group(1).strip()
    return(new_description, valid_values)


def writeStorageFormatFile(properties_storage_format_dict, output_subdir, 
                           properties_sf_file, deprecated_to_remove, 
                           properties_test_file):

    properties_mustache_dict = {}
    # add pystache stuff
    # property_mustache_keys = ["property", "pluginlist", "description", "validvalues", "SERVER", "rss", "v2v", "oba"]
    properties_entries = []

    for propToSF in properties_storage_format_dict.values():
        for pluginDeprecated in deprecated_to_remove:
            if not re.search(pluginDeprecated, propToSF["property"]):
                # print (" | ".join(propToSF.values()))
                # prop_line_for_storage_format = dict(zip(property_mustache_keys, propToSF.values()))
                # print("propToSF: ", str(propToSF)) 
                if propToSF not in properties_entries: 
                    properties_entries.append(propToSF)

    properties_mustache_dict = {"propertyentries": properties_entries[:]}

    with open(os.path.join(output_subdir, properties_sf_file), 'w') as ef:
        with open(os.path.join(output_subdir, properties_test_file), 'w') as ofile:
            for cpr in properties_mustache_dict["propertyentries"]:
                ofile.write(json.dumps(cpr))
            # do the mustache render
            # mustache_template = codecs.open("wiki_privileges_template_"
            #     + td + ".mustache", 'r', 'utf-8').read()
            mustache_template = codecs.open("wiki_properties_template.mustache",
                                       'r', 'utf-8').read()
            # mustache_template = open("wiki_privileges_template.mustache", "r").read()
            #    efo = pystache.render(mustache_template, privilege_out).encode('utf-8',
            #        'xmlcharrefreplace')
            efo = pystache.render(mustache_template, properties_mustache_dict)
            # efo = pystache.render(mustache_template, privilege_out)

            ef.write(efo)
            ef.close()
    return True


def readFileGetProperties(input_dir, propertyFile,
                          profile_spaces,
                          propertySearchString,
                          propSearchString,
                          group_types,
                          category_dict,
                          newline,
                          markdown_properties,
                          PLUGIN_SEPARATOR,
                          list_of_dead_properties,
                          process_properties_formatted):
    '''Read the input file and get the properties'''
    inputText = Path(os.path.join(input_dir, propertyFile)).read_text()
    textList = inputText.split("\n\n")
    currentProfiles = []
    propertiesDict = {}
    for text in textList:
        # If it's a profile section header "########## REMOTESERVICES" etc
        if re.search(r"#{10}", text):
            roughProfile = copy.deepcopy(text)
            for profileNoSpaces, profileSpaces in profile_spaces.items():
                if profileSpaces in roughProfile:
                    roughProfile = roughProfile.replace(profileSpaces,
                                                        profileNoSpaces)
            currentProfiles = re.findall(r"[A-Z,1-9]+", roughProfile)

        # If it contains a property
        else:
            propertyDict = {}
            commentList = []
            propertyList = []
            property_lines_list = text.split("\n")
            for property_line in property_lines_list:
                if re.match(propSearchString, property_line):
                    propertyList.append(property_line)
                elif PLUGIN_SEPARATOR in property_line:
                    continue
                    # Note here we could store plugin type
                    # And use in documentation
                else:
                    commentList.append(property_line)
            # This can be useful for debugging :-)
            # print("CL: ", commentList)
            # print("PL: ", propertyList)
            if len(propertyList) >= 1:
                propertyDict = get_property_values(
                    propertyList, propertyDict,
                    group_types, category_dict)
                propertyDict["profiles"] = currentProfiles[:]
                usesMarkdown = False
                for markdownProp in markdown_properties:
                    if markdownProp == propertyDict["property"]:
                        usesMarkdown = True
                        propertyDict["usesMarkdown"] = True
                propertyDict["description"] = \
                    process_comment(commentList,
                                   newline,
                                   usesMarkdown,
                                   process_properties_formatted)
                if "Valid values" in propertyDict["description"]:
                    propertyDict["description"], propertyDict[
                        "validvalues"] = process_valid(
                        propertyDict["description"])

                temp_prop_name = copy.deepcopy(propertyDict["property"])
                if temp_prop_name not in list_of_dead_properties:
                    propertiesDict[temp_prop_name] = copy.deepcopy(propertyDict)
                else:
                    print("temp_prop_name: ", temp_prop_name)
            else:
                # This is the comment at the start of the file,
                # which doesn't contain any valid properties,
                # or at least it didn't
                continue
    return(copy.deepcopy(propertiesDict))


    check_storage_format = writeStorageFormatFile(properties_storage_format_dict, 
                                                  output_subdir, 
                                                  properties_sf_file, 
                                                  deprecated_to_remove, 
                                                  properties_test_sf_file) 


def writePropsToFile(propertiesToPrintDict, output_subdir,
                     wikiPropertiesFile, deprecated_to_remove,
                     FMTPRINTORDER, properties_test_file):
    # Basic wiki markup file with all properties
    with open(os.path.join(output_subdir, wikiPropertiesFile), 'w') as f:
        headLineText = " || ".join(str(x) for x in FMTPRINTORDER)
        headLine = "|| " + headLineText + " ||\n"
        f.write(headLine)

        # 
        for prop, propToPrint in propertiesToPrintDict.items():
            for pluginDeprecated in deprecated_to_remove:
                if not re.search(pluginDeprecated, prop):
                    propLineText = " | ".join(propToPrint.values())
                    propLine = "| " + propLineText + " |\n"
                    f.write(propLine)
    return True


def main():
    '''Process the properties file to create a wiki table'''
    # Configure the connection to the Abiquo API
    token = input("Enter token: ")
    apiUrl = input("Enter API URL: ")
    api = Abiquo(apiUrl, auth=TokenAuth(token), verify=False)

    # Get the valid plugins from the API
    hypervisorTypes, deviceTypes, \
        backupPluginTypes, draasPluginTypes = get_plugins(api)
    # Add "plugins" that aren't "real" plugins
    backupPluginTypes.append("veeam")
    hypervisorTypes.append("esxi")

    # Join all plugins together because we are not displaying plugins by type
    plugins = hypervisorTypes + deviceTypes \
        + backupPluginTypes + draasPluginTypes

    plugins.remove("e1c")
    PLUGIN_SEPARATOR = "#--"

    # Some profile names have spaces, which is ridiculuous but hey
    profile_spaces = {"COSTUSAGE": "COST USAGE"}

    # Regexes to identify properties
    propertySearchString = r"#?\s?((([\w,\-,\{,\}]{1,60}?\.){1,10})([\w,\-,\{,\}]{1,50}))(=?(.*?))\n"
    propSearchString = r"#?\s?((([\w,\-,\{,\}]{1,60}?\.){1,10})([\w,\-,\{,\}]{1,50}))(=?(.*?))"

    # Input and output files
    input_dir = '../../platform/system-properties/src/main/resources/'
    propertyFile = 'abiquo.properties'
    output_subdir = 'output_files/'
    outputPropertyFile = 'wiki_properties_table_'
    outputStorageFormatFile = "wiki_properties_stformat_"
    # As there is only one property, use a text file, could later change to json, etc
    process_properties_formatted = "process_properties_formatted.txt"
    todaysDate = datetime.today().strftime('%Y-%m-%d')
    wikiPropertiesFile = outputPropertyFile + todaysDate + ".txt"
    properties_sf_file = outputStorageFormatFile + todaysDate + ".txt"
    properties_test_file = "proptestout_" + todaysDate + ".txt"
    properties_test_sf_file = "proptestsf_" + todaysDate + ".txt"

    # Improve some category names
    category_dict = {"stale": "stale sessions",
                    "dvs": "dvs and vcenter",
                    "vi": "virtual infrastructure",
                    "m": "m outbound api"}

    # Note that the function fix_defaults replaces some
    # default values that are set for our developers

    # Columns for output of properties documentation
    FMTPRINTORDER = ["Property", "Description", "API", "RS", "V2V", "OA"]
    # Confluence newline
    newline = " \\\\ "
    newline_storage_format = "<br/>"

    # Deprecated properties - to remove in format r"\.ha\."
    # deprecated_to_remove = [r"\.netapp\.", r"\.datastoreRdm"]
    deprecated_to_remove = [r"\.ha\."]
    list_of_dead_properties = [
        "abiquo.esxi.datastoreRdm",
        "abiquo.storagemanager.netapp.aggrfreespaceratio",
        "abiquo.storagemanager.netapp.debug",
        "abiquo.storagemanager.netapp.initiatorGroupName",
        "abiquo.storagemanager.netapp.volumelunration",
        "abiquo.enterprise.property.pricefactor.suffix",
        "abiquo.enterprise.property.discount.suffix"]
    # ESXi metrics list
    metrics = ["cpu",
               "cpu-mz",
               "cpu-time",
               "memory",
               "memory-swap",
               "memory-swap2",
               "memory-vmmemctl",
               "memory-physical",
               "memory-host",
               "disk-latency",
               "uptime"]

    group_types = {"{plugin}": plugins, "{metric}": metrics}

    profile_images = {"SERVER":
                     "{color:green}API{color}",
                     "REMOTESERVICES":
                     "{color:blue}RS{color}",
                     "V2VSERVICES":
                     "{color:grey}V2V{color}",
                     "MOUTBOUNDAPI":
                     "{color:brown}OA{color}",
                     "DNSMASQ":
                     "{color:brown}DNSMASQ{color}",
                     "COSTUSAGE":
                     "{color:brown}COSTUSAGE{color}",
                     "BILLING":
                     "{color:brown}BILLING{color}",
                     "XAASAPI":
                     "{color:brown}XAAS{color}",
                     "XAASRS":
                     "{color:brown}XAAS{color}"
                     }

    # These profiles have columns in the wiki
    default_profiles = ["SERVER",
                       "REMOTESERVICES",
                       "V2VSERVICES"]

    # Piggyback other profiles into the main columns
    profile_columns = {"SERVER": "SERVER",
                      "REMOTESERVICES": "REMOTESERVICES",
                      "V2VSERVICES": "V2VSERVICES",
                      "DNSMASQ": "REMOTESERVICES",
                      "COSTUSAGE": "SERVER",
                      "BILLING": "SERVER",
                      "XAASAPI": "SERVER",
                      "XAASRS": "REMOTESERVICES",
                      "VSM" : "SERVER",
                      "AM" : "SERVER"
                      }


    profile_storage_format = {"SERVER": "API",
                     "REMOTESERVICES": "RS",
                     "V2VSERVICES": "V2V",
                     "DNSMASQ": "DNSMASQ",
                     "COSTUSAGE": "COSTUSAGE",
                     "BILLING": "BILLING",
                     "XAASAPI": "XAAS",
                     "XAASRS": "XAAS",
                     "VSM": "API",
                     "AM": "API"
                     }


    # Example websites without proper <SERVER_IP_ADDRESS> notation
    webrefs = r"abiquo\.example\.com|80\.169\.25\.32"

    # Properties with an empty default value to document as empty
    # Note that if this were the last property in a list, strip the
    # space from it, because otherwise it will break the italics
    # for the default values
    plugin_blank_defaults = ["hyperv_301"]

    # Do not remove \n and can use for other markdown formatting
    markdown_properties = ["abiquo.guest.password.length"]

    propertiesDict = {}
    propertiesDict = readFileGetProperties(input_dir, propertyFile,
                                           profile_spaces,
                                           propertySearchString,
                                           propSearchString,
                                           group_types,
                                           category_dict,
                                           newline,
                                           markdown_properties,
                                           PLUGIN_SEPARATOR,
                                           list_of_dead_properties,
                                           process_properties_formatted)

    propertiesSortedDict = sort_for_output(propertiesDict)

    # propertiesToPrintDict = prepare_for_wiki(propertiesSortedDict,
    #                                        profile_columns,
    #                                        profile_images,
    #                                        newline,
    #                                        webrefs,
    #                                        default_profiles,
    #                                        plugin_blank_defaults)

    properties_storage_format_dict = prepare_for_storage_format(
                                           propertiesSortedDict,
                                           profile_columns,
                                           newline_storage_format,
                                           webrefs,
                                           default_profiles,
                                           plugin_blank_defaults,
                                           profile_storage_format)

    # # print(json.dumps(propertiesToPrintDict, indent=4, sort_keys=True))
    # check = writePropsToFile(propertiesToPrintDict, output_subdir,
    #                          wikiPropertiesFile, PLGDEPRC,
    #                          FMTPRINTORDER, properties_test_file)

    # if check is True:
    #     print("Wrote to file", output_subdir + wikiPropertiesFile)

    check_storage_format = writeStorageFormatFile(properties_storage_format_dict, 
                                                  output_subdir, 
                                                  properties_sf_file, 
                                                  deprecated_to_remove, 
                                                  properties_test_sf_file) 
    if check_storage_format is True:
        print("Wrote to file", output_subdir + properties_sf_file)


# Calls the main() function
if __name__ == '__main__':
    main()
