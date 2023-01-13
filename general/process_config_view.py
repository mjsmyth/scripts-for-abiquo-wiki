#!/usr/bin/python3 -tt
'''
Process the Configuration view options and print extra text from file

The Configuration view page is located at
    https://wiki.abiquo.com/display/doc/Configuration+view
Get Configuration view data of:
 - options and text from the UI files (requires hardcoded platform path)
 - values from Abiquo API (enter API URL and token auth)
Create two wiki markup tables for Configuration table and Wiki links table
Creates the file for today and overwrites any previous file for today
Changes to the extra text file should be versioned in git
Dependencies:
 abiquo-api installed with pip3 (note: auth function has an issue)
'''


# import sys
import re
import os
import json
# import requests
# import readline
# import copy
from abiquo.client import Abiquo
from abiquo.auth import TokenAuth
from datetime import datetime


def main():
    td = datetime.today().strftime('%Y-%m-%d')
    # td = "2021-11-17"

    input_subdir = "input_files"
    output_subdir = "output_files"
    output_file_name = "wiki_config_view_table_" + td + ".txt"
    output_wiki_file_name = "wiki_config_wiki_links_" + td + ".txt"
    #   extra_text_file_name = 'process_config_view_extratext_' + td + '.txt'
    extra_text_file_name = 'process_config_view_extra_text.txt'
    ui_path = "../../platform/ui/app/"
    ui_path_lang = ui_path + "lang/"
    ui_path_html = ui_path + "modules/configuration/partials/"

# Get data with requests - may require changes for python 3
    # apiHeaders = {}
    # apiAuth = input("Enter API authorization, e.g. Basic XXXX: ")
    # apiIP = input("Enter API address, e.g. api.abiquo.com: ")
    # # Get system properties data from the API of a fresh Abiquo
    # #    apiAuth = input("Authorization: ").strip()
    # #   apiIP = input("API IP address: ").strip()
    # apiUrl = 'https://' + apiIP + '/api/config/properties'
    # print (apiUrl)
    # apiAccept = 'application/vnd.abiquo.systemproperties+json'
    # apiHeaders['Accept'] = apiAccept
    # apiHeaders['Authorization'] = apiAuth
    # r = requests.get(apiUrl, headers=apiHeaders, verify=False)
    # sp_data = r.json()

    # Abiquo API token directly with no "Token" text
    token = input("Enter token: ")
    # API Example apiUrl = "https://abiquo.example.com/api"
    apiUrl = input("Enter API URL: ")
    api = Abiquo(apiUrl, auth=TokenAuth(token), verify=False)
    # Get the virtual datacenters from the cloud
    code, propertiesList = api.config.properties.get(
        headers={'accept': 'application/vnd.abiquo.systemproperties+json'})
    print("Get UI configuration properties. Response code is: ", code)

    # API configuration properties list has this format
    # {
    #   "id": 558,
    #   "name": "client.theme.defaultEnterpriseLogoPath",
    #   "value": "theme/abicloudDefault/img/logo.png",
    #   "description": "This is the path to the Enterprise logo used in the app",
    #   "links": [
    #     {
    #       "title": "client.theme.defaultEnterpriseLogoPath",
    #       "rel": "edit",
    #       "type": "application/vnd.abiquo.systemproperty+json",
    #       "href": "https://linatest.bcn.abiquo.com:443/api/config/properties/558"
    #     }
    #   ]
    # },
    # get the list of properties
    configProps = []
    configProps = propertiesList.collection
    # Eliminate the default dashboard config which is very big and scary
    configProps[:] = [d for d in configProps
                      if d.get('name') != "client.dashboard.default"]
    # Create a dictionary of config properties with name:value
    configDict = {j["name"]: j["value"] for j in configProps}

    # Process the language file which has keys and UI labels
    ui_json = ui_path_lang + "lang_en_US_labels.json"
    ui_json_data = open(ui_json)
    ui_data = json.load(ui_json_data)

    # Get UI labels for properties
    uiLabels = dict(filter(lambda elem: "configuration.systemproperties"
                           in elem[0]
                           and ".desc" not in elem[0], ui_data.items()))
    # Get UI labels for wiki links and tab headers
    mainmenuLabels = dict(filter(lambda elem: "mainmenu.button" in elem[0],
                                 ui_data.items()))
    configTabLabels = dict(filter(lambda elem: "configuration.tab" in elem[0],
                           ui_data.items()))
    # get my extra text from file in input files input_files
    extraText = {}
    with open(os.path.join(input_subdir,
                           extra_text_file_name), 'r') as extra_text_file:
        extra_text_all = extra_text_file.read()
        extra_text_list = extra_text_all.split("\n\n")
        for etl in extra_text_list:
            eti = etl.split("=")
            # if there are any "=" in the extra text, join them back in
            ext = "".join(eti[1:])
            extraText[eti[0].strip()] = ext.strip()

    htmlTextList = []
    htmlOrder = ["generalform.html",
                 "infrastructureform.html",
                 "networkform.html",
                 "dashboardform.html",
                 "passwordform.html",
                 "billingform.html",
                 "wikilinksform.html"]
    for hO in htmlOrder:
        htmlFileWithPath = ui_path_html + hO
        with open(htmlFileWithPath, 'r') as htmlFile:
            htmlTextList.append((htmlFile.read()).strip())
            # add a field separator at the end of each file
            # yeah this is horrible but it works :-p
            htmlTextList.append('<div class="form-label pl-2">')
    allHtmlText = " ".join(htmlTextList)
    splitText = '<div class="form-label pl-2">'

    htmlLabels = allHtmlText.split(splitText)
    tabHeaderRegex = re.compile('configuration\\.tab\\.[\\w]+')
    labelRegex = re.compile(r'configuration\.systemproperties\.[\w]+\.[\w]+\.?[\w]*')
    wikiRegex = re.compile(r'client\.wiki\.[\w]+\.[\w]+')
    valueRegex = re.compile("'client\\.[\\w]+\\.[\\w]+\\.?[\\w]*\\.?[\\w]*'")
    wikiHeaderRegex = re.compile(r'mainmenu\.button\.[\w]+')

    outputOrder = []
    outputWikiLik = []

    for hL in htmlLabels:
        # print ("hL: ", hL)
        wikiLinkEntry = False
        defaultView = False
        checkBox = False
        if "checkbox" in hL:
            checkBox = True
        if "defaultView" in hL:
            defaultView = True
        tabheader = re.findall(tabHeaderRegex, hL)
        if tabheader:
            headerName = tabheader[0].strip("'")
            if headerName in configTabLabels:
                headerValue = configTabLabels[headerName][:]
            headerString = ("|| h6. " + headerValue
                            + " || Default || Notes || Info ||")
            outputOrder.append(headerString)
        else:
            label = ""
            outputList = []
            valueKey = ""
            labelAll = re.findall(labelRegex, hL)
            if labelAll:
                label = labelAll[0]
                if label in uiLabels:
                    outputList.append(uiLabels[label])
            # returntourl is deprecated
            if label == "configuration.systemproperties.general.returntourl":
                continue
            elif label == "":
                continue
            # The restore dashboard button has a different valueKey
            elif label == "configuration.systemproperties.dashboard.restoredefaultdashboards":
                valueKey = "config.dashboard.restoredefaultdashboards.button"
            else:
                # value is the name of the configuration properties key
                valueQuoted = re.findall(valueRegex, hL)
                if valueQuoted:
                    valueKey = valueQuoted[0].strip("'")
            if len(valueKey) > 0:
                if valueKey in configDict:
                    if defaultView is True:
                        if configDict[valueKey] == "0":
                            outputList.append(" Home ")
                    elif checkBox is True:
                        if configDict[valueKey] == "0":
                            outputList.append(" (x) ")
                        if configDict[valueKey] == "1":
                            outputList.append(" (/) ")
                    else:
                        valueOutput = configDict[valueKey][:]
                        # c.w.v is not in use and it's not valid markup
                        if r"{client.wiki.version}" in valueOutput:
                            valueOutput = valueOutput.replace(
                                r"{client.wiki.version}", "doc")
                        outputList.append(valueOutput)
                else:
                    outputList.append(" ")

                if valueKey in extraText:
                    if extraText[valueKey] != "-":
                        outputList.append(extraText[valueKey])
                    else:
                        outputList.append(" ")

                wikiText = re.search(wikiRegex, valueKey)
                if wikiText:
                    wikiLinkEntry = True

            if wikiLinkEntry is True:
                outputWikiLikLi = "| " + (" | ").join(outputList) + " |  |"
                outputWikiLik.append(outputWikiLikLi)
            else:
                outputMain = "| " + (" | ").join(outputList) + " |  |"
                outputOrder.append(outputMain)
            wikiheader = re.findall(wikiHeaderRegex, hL)
            if wikiheader:
                if wikiheader[0] in mainmenuLabels:
                    wikiheaderName = mainmenuLabels[wikiheader[0]][:]
                    wikiheaderString = ("|| h6. " + wikiheaderName
                                        + " || Default || Info ||")
                outputWikiLik.append(wikiheaderString)

    outfile = open(os.path.join(output_subdir, output_file_name), 'w')
    for outputLine in outputOrder:
        outfile.write(outputLine + "\n")
    outfile.close()

    outwikifile = open(os.path.join(output_subdir, output_wiki_file_name), 'w')
    for wikiLine in outputWikiLik:
        outwikifile.write(wikiLine + "\n")
    outwikifile.close()


# Calls the main() function
if __name__ == '__main__':
    main()
