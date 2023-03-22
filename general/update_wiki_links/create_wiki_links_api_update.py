#!/usr/bin/python3 -tt
'''
Read a tsv file with wiki links to change
In the format:
    operation   wikiLinkKey wikiLinkLabel currentLink newLink
and create an API properties data object to change them
and a liquibase file to change them in the database.

Add line
# <sql>
    # "insert into system_properties (name, value)
    #  values ('client.wiki.infra.manageProtectionManagers',
    #  'https://wiki.abiquo.com/display/doc/Protection+managers');"
# </sql>    
Update to change name of property
# <update tableName="system_properties">
    # <column name="value" value="https://wiki.abiquo.com/display/doc/Abiquo+XaaS"/>
    # <where>name='client.wiki.xaas'</where>    
# </update>    
'''

# import sys
# import re
import copy
import os
import json
from datetime import datetime
import pystache

# import requests
# import readline

# from abiquo.client import Abiquo
# from abiquo.auth import TokenAuth


def write_liquibase_file(output_dict, output_subdir, output_liquibase_file_name):
    ''' Write a liquibase file from the output dict''' 
    response = False
    mustache_file = open("wiki_links_liquibase.mustache", 'r', encoding='UTF-8')
    mustache_template = mustache_file.read()
    efo = pystache.render(mustache_template, output_dict)
    efe = open(os.path.join(output_subdir, output_liquibase_file_name), 'w', encoding='UTF-8')
    if efe:
        efe.write(efo)
        response = True
        efe.close()
    if mustache_file:
        mustache_file.close()
    return response


def create_api_update(property_collection, wiki_links_dict, 
                      output_subdir, output_api_file_name):
    ''' Process the list of wiki links to create api update object'''  
    response = False
    working_link = {}
    working_property = {}
    new_property_list = []
    ## This is all the wiki properties from config view in a list of dicts
    for a_property in property_collection["collection"]:
        working_property = copy.deepcopy(a_property)
        working_property["__property"] = copy.deepcopy(working_property["name"])
        # wiki_links_dict is links from update file in a dict with index property name
        if working_property["name"] in wiki_links_dict:
            working_link = copy.deepcopy(wiki_links_dict[working_property["name"]])
            if "UPDATE" in working_link["operation"] or \
                    "CREATE" in working_link["operation"]:
                print("update: ", working_link["wikiLinkKey"])
                working_property["value"] = copy.deepcopy(working_link["newLink"])
                print("working_link:newlink: ", working_link["newLink"])
        new_property_list.append(working_property)
    property_collection["collection"] = copy.deepcopy(new_property_list)
    with open(os.path.join(output_subdir, output_api_file_name), 'w',  encoding='UTF-8') as afo:
        json.dump(property_collection, afo)
        response = True
    return response


def create_output_dict(wiki_links_dict):
    ''' Get the list of wiki links from input file and create output dict
        This is only used for pystache'''  
    output_dict = {}
    output_dict["creates"] = []
    output_dict["updates"] = []
    output_dict["deletes"] = []
    for wiki_link_dict in wiki_links_dict.values():
        wiki_dict = {}
        if wiki_link_dict["operation"] == "CREATE" and \
                wiki_link_dict["wikiLinkKey"] != "":
            wiki_dict["ui_key"] = wiki_link_dict["wikiLinkKey"]
            wiki_dict["wiki_link"] = wiki_link_dict["newLink"]
            output_dict["creates"].append(copy.deepcopy(wiki_dict))
        if wiki_link_dict["operation"] == "UPDATE": 
            wiki_dict["wiki_link"] = wiki_link_dict["newLink"]
            wiki_dict["ui_key"] = wiki_link_dict["wikiLinkKey"]
            output_dict["updates"].append(copy.deepcopy(wiki_dict))
        if wiki_link_dict["operation"] == "DELETE":
            wiki_dict["ui_key"] = wiki_link_dict["wikiLinkKey"]
            wiki_dict["wiki_link"] = " " 
            output_dict["deletes"].append(copy.deepcopy(wiki_dict))
    return output_dict


def read_property_file(input_subdir, property_file_name):
    '''Read the property file and create a dict of properties'''    
    with open(os.path.join(input_subdir,
                           property_file_name), 'r', encoding='UTF-8') as properties_input_file:
        properties_from_file = properties_input_file.read()
        in_property_collection = json.loads(properties_from_file)
    return in_property_collection


def read_input_file(input_subdir, input_file_name):
    '''Read the input file and create a list of wiki links'''    
    wiki_link_dict = {}
    wiki_links_dict = {}
    # wiki_link_dict_list = []
    with open(os.path.join(input_subdir,
                           input_file_name), 'r', encoding='UTF-8') as wiki_links_input_file:
        wiki_links_all = wiki_links_input_file.read()
        wiki_links_list = wiki_links_all.split("\n")

        header_tsv = wiki_links_list.pop(0)
        header_list = header_tsv.split("\t")
        link_tuple = ()
        for wiki_link_list_item in wiki_links_list:
            wiki_link_raw = wiki_link_list_item.split("\t")
            # operation   wikiLinkKey wikiLinkLabel currentLink newLink
            for wiki_link_tuple in zip(header_list, wiki_link_raw):
                # print(wiki_link_tuple)
                link_tuple += (wiki_link_tuple,)
            wiki_link_dict = dict(link_tuple)
            wiki_links_dict[wiki_link_dict["wikiLinkKey"]] = copy.deepcopy(wiki_link_dict)
            # print (wiki_link_dict_list)
    # exit()
    return wiki_links_dict


def main():
    '''Process the input file from spreadsheet and Abiquo API response to create
   API response to update'''    
    today_date = datetime.today().strftime('%Y-%m-%d')
    # today_date = "2021-11-17"    

    # output_dict = {}
    input_subdir = "input_files"
    output_subdir = "output_files"
    input_file_name = "wiki_links_table_" + today_date + ".tsv"
    # property_file_name = "v61_wiki_properties.json"
    property_file_name = "v61_wiki_properties_client.json"
    output_liquibase_file_name = "wiki_links_liquibase_" + today_date + ".txt"
    output_api_file_name = "wiki_links_api_file_" + today_date + ".txt"
    wiki_links_dict = read_input_file(input_subdir, input_file_name)
    in_property_list = read_property_file(input_subdir, property_file_name)
    output_dict = create_output_dict(wiki_links_dict)
    output_response = write_liquibase_file(output_dict, output_subdir, output_liquibase_file_name)
    print(output_response)
    output_api_response = create_api_update(in_property_list, wiki_links_dict,
                                            output_subdir, output_api_file_name)

    print(output_api_response)

# Calls the main() function
if __name__ == '__main__':
    main()
