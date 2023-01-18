#!/usr/bin/python3 -tt
#
# This script formats the abiquo.properties file for documentation.
# The initial version creates a wiki markup file.
#
# The script requires:
# - the Abiquo Python client installed with pip3
# - access to the Abiquo API (input token and URL)
# - access to platform files (hardcoded location)
#
# There are some values hardcoded in the functions:
# - main
# - fixDefaults
#
# Good luck!
#


import re
import copy
from datetime import datetime
import os
# import json
from collections import Counter
from abiquo.client import Abiquo
from abiquo.auth import TokenAuth
from pathlib import Path

# For test environment disable SSL warning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def getPlugins(api):
    # Get plugins: hypervisor types, network devices,
    #              backup devices, draas devices
    code, hypervisorTypesList = api.config.hypervisortypes.get(
        headers={'Accept': 'application/vnd.abiquo.hypervisortypes+json'})
    print("Get hypervisor types. Response code is: ", code)
    hypervisorTypes = [ht["name"].lower()
                       for ht in hypervisorTypesList.json["collection"]]

    code, deviceTypesList = api.config.devicetypes.get(
        headers={'Accept': 'application/vnd.abiquo.devicetypes+json'})
    print("Get device types. Response code is: ", code)
    deviceTypes = [dt["name"].lower()
                   for dt in deviceTypesList.json["collection"]]

    code, backupPluginTypesList = api.config.backupplugintypes.get(
        headers={'Accept': 'application/vnd.abiquo.backupplugintypes+json'})
    print("Get backup plugin types. Response code is: ", code)
    backupPluginTypes = [bpt["type"].lower()
                         for bpt in backupPluginTypesList.json["collection"]]

    code, draasPluginTypesList = api.config.draasplugintypes.get(
        headers={'Accept': 'application/vnd.abiquo.draasplugintypes+json'})
    print("Get DRaaS device types. Response code is: ", code)
    draasPluginTypes = [drpt["type"].lower()
                        for drpt in draasPluginTypesList.json["collection"]]
    return (hypervisorTypes, deviceTypes, backupPluginTypes, draasPluginTypes)


def sortForOutput(propertiesDict):
    # When sorting take into consideration sortName
    # For com.abiquo.foo.bar, sortname is abiquo.foo.bar
    for pName, pValue in propertiesDict.items():
        if not propertiesDict[pName]["sortName"]:
            propertiesDict[pName]["sortName"] = copy.deepcopy(
                propertiesDict[pName]["property"])
    sortedPropDict = dict(sorted(propertiesDict.items(),
                                 key=lambda x: x[1]["sortName"].lower()))
    return sortedPropDict


def prepareForWiki(pSDict, profileColumns,
                   profileImages, NEWLINE,
                   webrefs, defaultProfiles,
                   PLUGIN_BLANK_DEFAULTS):
    # Prepare a dict with the properties to document
    pTPD = {}
    # previousCategory = ""
    anchor = ""
    propvDefault = {}
    for pname, propv in pSDict.items():
        pTPD[pname] = {}
        # Prepare the Property entry
        pluginList = ""
        # if propv["category"] != previousCategory:
        #     anchor = " {anchor: " + copy.deepcopy(propv["category"]) + "} "
        # else:
        #     anchor = ""
        # previousCategory = copy.deepcopy(propv["category"])
        propName = propv["property"]
        if "{" in propName:
            propName = re.sub(r"\{", r"\\{", propName)
        if "[" in propName:
            propName = re.sub(r"\[", r"\\{", propName)
        if "]" in propName:
            propName = re.sub(r"\]", r"\}", propName)
        pluginList = ""
        if "default" in propv:
            if type(propv["default"]) is dict:
                propvDefault = dict(sorted(propv["default"].items()))
                for plugin in propvDefault.keys():
                    pluginList += NEWLINE + "\\- " + plugin
        pTPD[pname]["Property"] = anchor + "*" + propName + "* " + pluginList

        # Prepare the default entry
        defaultList = ""
        if "C:" in propv:
            propv = re.sub("\\", "\\\\", propv)
        if "default" in propv:
            if type(propv["default"]) is str:
                if "http" in propv["default"] or ("{" or "[") \
                        in propv["default"]:
                    defaultList = NEWLINE + "Default: {newcode}" + \
                        copy.deepcopy(propv["default"]) + "{newcode}"
                else:
                    if re.search(r"\S+", propv["default"]):
                        defaultList = NEWLINE + "_Default: " + copy.deepcopy(
                            propv["default"]) + "_"
                        if "*" in defaultList:
                            defaultList = re.sub(r"\*", r"\\*", defaultList)
            if type(propv["default"]) is dict:
                value, count = Counter(
                    propvDefault.values()).most_common(1)[0]
                # Count the number of times the most common value occurs
                if count > 1:
                    # More than one property has this value
                    # If it's not empty, make it the general default
                    if re.search(r"\S+", value):
                        defaultList = NEWLINE + "_Default: " + value[:]
                if count == 1:
                    # If the most common only occurs once,
                    # the properties all have their own values
                    # So don't display a general default
                    defaultList = NEWLINE + "_Default: "
                for plugin, defv in propvDefault.items():
                    if count > 1:
                        # If more than one property has the same value,
                        # but this property is different, then display it
                        if defv != value:
                            if re.search(r"\S+", defv):
                                defaultList += NEWLINE + "\\- " + plugin + \
                                    " = " + defv
                    if count == 1:
                        # If all properties have different defaults,
                        # then display them all
                        if re.search(r"\S+", defv) or \
                                plugin in PLUGIN_BLANK_DEFAULTS:
                            # A valid default is not empty or has an exemption
                            defaultList += NEWLINE + "\\- " + plugin + \
                                " = " + defv
                defaultList += "_"

        # Prepare values
        valuesList = ""
        if "validValues" in propv:
            valuesList = NEWLINE + "_Valid values: " + \
                propv["validValues"] + "_"

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
                if "*" in description:
                    description = re.sub(r'\*', r'\\*', description)
                if "-" in description:
                    description = re.sub(r'\-', r'\\-', description)
                if "[" in description:
                    description = re.sub(r'\[', r'\\-', description)
                if "{" in description:
                    description = re.sub(r'\{', r'\\-', description)
        # todo check if default has actual characters in it
        # todo etc.

        pTPD[pname]["Descripton"] = description + \
            valuesList + defaultList

        # Prepare profiles
        if "profiles" in propv:
            for profile in defaultProfiles:
                pTPD[pname][profile] = " "
            for profileName, profileImage in profileImages.items():
                if profileName in propv["profiles"]:
                    if profileName in profileColumns:
                        column = profileColumns[profileName]
                        pTPD[pname][column] = copy.deepcopy(
                            profileImages[profileName])

    return pTPD


def fixDefault(pName, default):
    # Some local defaults are replaced on filesystem during install
    # This should be in main() but hey
    newDefault = default[:]
    if "datacenter.id" in pName:
        newDefault = re.sub("default", "Abiquo", default)
    if "repositoryLocation" in pName:
        newDefault = re.sub("127.0.0.1", r"<REPO_IP_ADDRESS>", default)
    if "localhost" in default:
        newDefault = re.sub("localhost", r"127.0.0.1", default)
    if "10.60.1.4" in default:
        newDefault = re.sub("10.60.1.4", r"127.0.0.1", default)
    return newDefault


def getCategory(pName, CATEGORYDICT):
    # We use categories to create anchors.
    # They are generally the second part of the name
    propSortName = ""
    prop_cat = pName.split(".")
    if prop_cat[0] == "abiquo":
        property_cat = prop_cat[1][:]
    else:
        if prop_cat[0] == "com":
            if prop_cat[1] == "abiquo":
                property_cat = prop_cat[2][:]
                propSortName = ".".join(prop_cat[1:])
            else:
                property_cat = prop_cat[2][:]
        else:
            property_cat = prop_cat[0][:]

    if property_cat in CATEGORYDICT:
        return (copy.deepcopy(CATEGORYDICT[property_cat]), propSortName)
    else:
        return property_cat, propSortName


def getPropNameDefault(currentProp):
    # Split property name into name and default
    # note that default can contain an equals sign
    if "=" in currentProp:
        splitProp = currentProp.split("=")
        defaultJoined = "=".join(splitProp[1:])
        propDefault = defaultJoined.strip()
        propName = splitProp[0].strip()
        propName = re.sub(r"^#?\s?", "", propName)
    else:
        propName = currentProp.strip()
        propDefault = ""
        propName = re.sub(r"^#?\s?", "", propName)
    propDefault = fixDefault(propName, propDefault)
    return propName, propDefault


def processGroup(propList, GROUPTYPES):
    # For properties that are in groups e.g. by plugins, metrics
    # Return group name and array of tags (e.g. "amazon") and defaults
    groupWorkList = []
    groupList = []
    groupTagList = []
    propDefDict = {}
    propGroupDefDict = {}
    groupName = ""
    myGroup = ""

    for prop in propList:
        if "--" not in prop:
            propName, propDefault = getPropNameDefault(prop)
            propDefDict[propName] = propDefault

    for propName in propDefDict:
        propName.strip()
        propNameList = propName.split(".")
        # plugins etc are not in first two parts of name
        # filter list of plugins in each list
        # lastPropNameList = propNameList[2:]
        groupWorkList.extend(propNameList[2:])
    reducedSet = set(groupWorkList)
    reducedList = list(reducedSet)

    for group, groupList in GROUPTYPES.items():
        for x in reducedList:
            if x in groupList:
                groupTagList.append(x)
                myGroup = copy.deepcopy(group)

    if len(groupTagList) > 0:
        # Create a groupName, which is abiquo.foo.{tagType}.bar
        # Store tags in an array
        for tag in groupTagList:
            for name, default in propDefDict.items():
                if tag in name:
                    propGroupDefDict[tag] = default
                    if not groupName:
                        groupName = name.replace(tag, myGroup)
        return groupName, propGroupDefDict
    return "", ""


def getPropertyValues(propertyList, propertyDict,
                      GROUPTYPES, CATEGORYDICT):
    # For a property, get:
    # - Names, including group names with plugin or metric, etc.
    # - Names for sorting (e.g. no "com."),
    # - Categories (for anchors)
    # - and default values, which can be strings or arrays
    initialPropName, propDefault = getPropNameDefault(propertyList[0])
    propertyDict["category"], propertyDict["sortName"] = getCategory(
        initialPropName, CATEGORYDICT)
    if len(propertyList) == 1:
        propertyDict["property"] = initialPropName
        propertyDict["default"] = propDefault
    else:
        propertyDict["property"], propertyDict["default"] = processGroup(
            propertyList, GROUPTYPES)
    return(propertyDict)


def processComment(commentList, NEWLINE, usesMarkdown):
    # Process the description of the property from the
    # Commented lines that aren't properties
    description = ""
    if usesMarkdown:
        # For Markdown comments, replace newlines
        for comment in commentList[:-1]:
            description += comment.strip("#") + NEWLINE
        description += commentList[-1].strip("#")
    else:
        for comment in commentList:
            description += comment.strip("#")
    return(description.strip())


def processValid(description):
    # Get the Valid values supplied by devs
    # Remove this from the description
    foundValid = ""
    newDescription = description[:]
    searchValid = r"(?<=Valid values)[\s]*?[:]?[\s]*?(.*)$"
    foundValid = re.search(searchValid, description)
    replaceValid = "Valid values" + foundValid.group(0)
    newDescription = re.sub(replaceValid, "", description)
    validValues = foundValid.group(1).strip()
    return(newDescription, validValues)


def readFileGetProperties(inputDir, propertyFile,
                          PROFILE_SPACES,
                          propertySearchString,
                          propSearchString,
                          GROUPTYPES,
                          CATEGORYDICT,
                          NEWLINE,
                          MARKDOWN_PROPERTIES,
                          PLUGIN_SEPARATOR):
    inputText = Path(os.path.join(inputDir, propertyFile)).read_text()
    textList = inputText.split("\n\n")
    currentProfiles = []
    propertiesDict = {}
    for text in textList:
        # If it's a profile section header "########## REMOTESERVICES" etc
        if re.search(r"#{10}", text):
            roughProfile = copy.deepcopy(text)
            for profileNoSpaces, profileSpaces in PROFILE_SPACES.items():
                if profileSpaces in roughProfile:
                    roughProfile = roughProfile.replace(profileSpaces,
                                                        profileNoSpaces)
            currentProfiles = re.findall(r"[A-Z,1-9]+", roughProfile)

        # If it contains a property
        else:
            propertyDict = {}
            commentList = []
            propertyList = []
            propertyLines = text.split("\n")
            for propertyLine in propertyLines:
                if re.match(propSearchString, propertyLine):
                    propertyList.append(propertyLine)
                elif PLUGIN_SEPARATOR in propertyLine:
                    continue
                    # Note here we could store plugin type
                    # And use in documentation
                else:
                    commentList.append(propertyLine)
            # This can be useful for debugging :-)
            # print("CL: ", commentList)
            # print("PL: ", propertyList)
            if len(propertyList) >= 1:
                propertyDict = getPropertyValues(
                    propertyList, propertyDict,
                    GROUPTYPES, CATEGORYDICT)
                propertyDict["profiles"] = currentProfiles[:]
                usesMarkdown = False
                for markdownProp in MARKDOWN_PROPERTIES:
                    if markdownProp == propertyDict["property"]:
                        usesMarkdown = True
                propertyDict["description"] = \
                    processComment(commentList,
                                   NEWLINE,
                                   usesMarkdown)
                if "Valid values" in propertyDict["description"]:
                    propertyDict["description"], propertyDict[
                        "validValues"] = processValid(
                        propertyDict["description"])

                tempPropName = copy.deepcopy(propertyDict["property"])
                propertiesDict[tempPropName] = copy.deepcopy(propertyDict)
            else:
                # This is the comment at the start of the file,
                # which doesn't contain any valid properties,
                # or at least it didn't
                continue
    return(copy.deepcopy(propertiesDict))


def writePropsToFile(propertiesToPrintDict, outputSubdir,
                     wikiPropertiesFile, PLGDEPRC,
                     FMTPRINTORDER):

    # Basic wiki markup file with all properties
    with open(os.path.join(outputSubdir, wikiPropertiesFile), 'w') as f:
        headLineText = " || ".join(str(x) for x in FMTPRINTORDER)
        headLine = "|| " + headLineText + " ||\n"
        f.write(headLine)

        for prop, propToPrint in propertiesToPrintDict.items():
            for pluginDeprecated in PLGDEPRC:
                if not re.search(pluginDeprecated, prop):
                    propLineText = " | ".join(propToPrint.values())
                    propLine = "| " + propLineText + " |\n"
                    f.write(propLine)

    return True


def main():
    # Configure the connection to the Abiquo API
    token = input("Enter token: ")
    apiUrl = input("Enter API URL: ")
    api = Abiquo(apiUrl, auth=TokenAuth(token), verify=False)

    # Get the valid plugins from the API
    hypervisorTypes, deviceTypes, \
        backupPluginTypes, draasPluginTypes = getPlugins(api)
    # Add "plugins" that aren't "real" plugins
    backupPluginTypes.append("veeam")
    hypervisorTypes.append("esxi")

    # Join all plugins together because we are not displaying plugins by type
    PLUGINS = hypervisorTypes + deviceTypes \
        + backupPluginTypes + draasPluginTypes

    PLUGIN_SEPARATOR = "#--"

    # Some profile names have spaces, which is ridiculuous but hey
    PROFILE_SPACES = {"MOUTBOUNDAPI": "M OUTBOUND API",
                      "COSTUSAGE": "COST USAGE"}

    # Regexes to identify properties
    propertySearchString = r"#?\s?((([\w,\-,\{,\}]{1,60}?\.){1,10})([\w,\-,\{,\}]{1,50}))(=?(.*?))\n"
    propSearchString = r"#?\s?((([\w,\-,\{,\}]{1,60}?\.){1,10})([\w,\-,\{,\}]{1,50}))(=?(.*?))"

    # Input and output files
    inputDir = '../../platform/system-properties/src/main/resources/'
    propertyFile = 'abiquo.properties'
    outputSubdir = 'output_files/'
    outputPropertyFile = 'wiki_properties_table_'
    todaysDate = datetime.today().strftime('%Y-%m-%d')
    wikiPropertiesFile = outputPropertyFile + todaysDate + ".txt"

    # Improve some category names
    CATEGORYDICT = {"stale": "stale sessions",
                    "dvs": "dvs and vcenter",
                    "vi": "virtual infrastructure",
                    "m": "m outbound api"}

    # Note that the fuction fixDefaults replaces some
    # default values that are set for our developers

    # Columns for output of properties documentation
    FMTPRINTORDER = ["Property", "Description", "API", "RS", "V2V", "OA"]
    # Confluence newline
    NEWLINE = " \\\\ "

    # Deprecated plugins - ha is deprecated and just a placeholder
    # so you could delete it or replace it with something prettier
    PLGDEPRC = [r"\.ha\."]

    # ESXi metrics list
    METRICS = ["cpu",
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

    GROUPTYPES = {"{plugin}": PLUGINS, "{metric}": METRICS}

    # # Display these lozenges in wiki markup
    # profileImages = {"SERVER":
    #                  " {status:colour=green|title=API|subtle=false}",
    #                  "REMOTESERVICES":
    #                  " {status:colour=blue|title=RS|subtle=false}",
    #                  "V2VSERVICES":
    #                  " {status:colour=grey|title=V2V|subtle=false}",
    #                  "MOUTBOUNDAPI":
    #                  " {status:colour=yellow|title=OA|subtle=false}",
    #                  "DNSMASQ":
    #                  " {status:colour=yellow|title=DNSMASQ|subtle=false}",
    #                  "COSTUSAGE":
    #                  " {status:colour=yellow|title=COSTUSAGE|subtle=false}",
    #                  "BILLING":
    #                  " {status:colour=yellow|title=BILLING|subtle=false}",
    #                  "XAASAPI":
    #                  " {status:colour=yellow|title=XAAS|subtle=false}",
    #                  "XAASRS":
    #                  " {status:colour=yellow|title=XAAS|subtle=false}"
    #                  }
    profileImages = {"SERVER":
                     " {colour:green}API{colour}",
                     "REMOTESERVICES":
                     " {colour=blue}RS{colour}",
                     "V2VSERVICES":
                     " {colour=grey}V2V{colour}",
                     "MOUTBOUNDAPI":
                     " {colour=brown}OA{colour}",
                     "DNSMASQ":
                     " {colour=brown}DNSMASQ{colour}",
                     "COSTUSAGE":
                     " {colour=brown}COSTUSAGE{colour}",
                     "BILLING":
                     " {colour=brown}BILLING{colour}",
                     "XAASAPI":
                     " {colour=brown}XAAS{colour}",
                     "XAASRS":
                     " {colour=brown}XAAS{colour}"
                     }


    # These profiles have columns in the wiki
    defaultProfiles = ["SERVER",
                       "REMOTESERVICES",
                       "V2VSERVICES",
                       "MOUTBOUNDAPI"]

    # Piggyback other profiles into the main columns
    profileColumns = {"SERVER": "SERVER",
                      "REMOTESERVICES": "REMOTESERVICES",
                      "V2VSERVICES": "V2VSERVICES",
                      "MOUTBOUNDAPI": "MOUTBOUNDAPI",
                      "DNSMASQ": "REMOTESERVICES",
                      "COSTUSAGE": "SERVER",
                      "BILLING": "SERVER",
                      "XAASAPI": "SERVER",
                      "XAASRS": "REMOTESERVICES"
                      }

    # Example websites without proper <SERVER_IP_ADDRESS> notation
    webrefs = r"abiquo\.example\.com|80\.169\.25\.32"

    # Properties with an empty default value to document as empty
    # Note that if this were the last property in a list, strip the
    # space from it, because otherwise it will break the italics
    # for the default values
    PLUGIN_BLANK_DEFAULTS = ["hyperv_301"]

    # Do not remove \n and can use for other markdown formatting
    MARKDOWN_PROPERTIES = ["abiquo.guest.password.length"]

    propertiesDict = {}
    propertiesDict = readFileGetProperties(inputDir, propertyFile,
                                           PROFILE_SPACES,
                                           propertySearchString,
                                           propSearchString,
                                           GROUPTYPES,
                                           CATEGORYDICT,
                                           NEWLINE,
                                           MARKDOWN_PROPERTIES,
                                           PLUGIN_SEPARATOR)

    propertiesSortedDict = sortForOutput(propertiesDict)

    propertiesToPrintDict = prepareForWiki(propertiesSortedDict,
                                           profileColumns,
                                           profileImages,
                                           NEWLINE,
                                           webrefs,
                                           defaultProfiles,
                                           PLUGIN_BLANK_DEFAULTS)
    # print(json.dumps(propertiesToPrintDict, indent=4, sort_keys=True))
    check = writePropsToFile(propertiesToPrintDict, outputSubdir,
                             wikiPropertiesFile, PLGDEPRC,
                             FMTPRINTORDER)

    if check is True:
        print("Wrote to file", outputSubdir + wikiPropertiesFile)


# Calls the main() function
if __name__ == '__main__':
    main()
