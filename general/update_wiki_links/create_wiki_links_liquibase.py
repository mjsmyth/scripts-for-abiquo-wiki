#!/usr/bin/python3 -tt
'''
Read a tsv file with wiki links to change and create a liquibase to change them
Add line
# <sql>
    # "insert into system_properties (name, value) values ('client.wiki.infra.manageProtectionManagers', 
    #  'https://wiki.abiquo.com/display/doc/Protection+managers');"
# </sql>    
Update to change name of property
# <update tableName="system_properties">
    # <column name="value" value="https://wiki.abiquo.com/display/doc/Abiquo+XaaS"/>
    # <where>name='client.wiki.xaas'</where>    
# </update>    
'''


# import sys
import re
import os
import json
import pystache
import codecs
# import requests
# import readline
import copy
# from abiquo.client import Abiquo
# from abiquo.auth import TokenAuth
from datetime import datetime


def main():
    td = datetime.today().strftime('%Y-%m-%d')
    # td = "2021-11-17"

    input_subdir = "input_files"
    output_subdir = "output_files"
    input_file_name = "wiki_links_table_" + td + ".tsv"
    output_wiki_file_name = "wiki_links_wiki_base_" + td + ".txt"

    wiki_link_dict = {}
    wiki_link_dict_list = []
    output_dict = {}
    output_dict["creates"] = []
    output_dict["updates"] = []

    with open(os.path.join(input_subdir,
                           input_file_name), 'r') as wiki_links_input_file:
        wiki_links_all = wiki_links_input_file.read()
        wiki_links_list = wiki_links_all.split("\n")

        header_tsv = wiki_links_list.pop(0)
        header_list = header_tsv.split("\t")
        link_tuple = ()
        for wiki_link_list_item in wiki_links_list:
            wiki_link_raw = wiki_link_list_item.split("\t")
            # operation   wikiLinkKey wikiLinkLabel   currentLink newLink
            for wiki_link_tuple in zip(header_list, wiki_link_raw):
                # print(wiki_link_tuple)
                link_tuple += (wiki_link_tuple,)
            wiki_link_dict = dict(link_tuple)
            wiki_link_dict_list.append(wiki_link_dict)
            # print (wiki_link_dict_list)
    # exit()
    for wiki_link_dict in wiki_link_dict_list:
        if wiki_link_dict["operation"] == "CREATE" and \
                wiki_link_dict["wikiLinkKey"] != "":
            create_dict = {}
            create_dict["ui_key"] = wiki_link_dict["wikiLinkKey"]
            create_dict["wiki_link"] = wiki_link_dict["newLink"]
            output_dict["creates"].append(copy.deepcopy(create_dict))
        if wiki_link_dict["operation"] == "UPDATE": 
            update_dict = {}
            update_dict["wiki_link"] = wiki_link_dict["newLink"]
            update_dict["ui_key"] = wiki_link_dict["wikiLinkKey"]
            output_dict["updates"].append(copy.deepcopy(update_dict))

    mustacheTemplate = codecs.open("wiki_links_liquibase.mustache",
                                   'r', 'utf-8').read()

    efo = pystache.render(mustacheTemplate, output_dict)
    ef = open(os.path.join(output_subdir, output_wiki_file_name), 'w')

    if ef:
        ef.write(efo)
        ef.close()


# Calls the main() function
if __name__ == '__main__':
    main()
