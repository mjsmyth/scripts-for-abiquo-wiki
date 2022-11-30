'''
# Python script: release/publishRelease
# ---------------------------------------
# Script designed to publish draft pages for new version
# Gets pages with vXXX and updates pages without it
#
# Publish draft pages
# ------------------
# 1. Get the vXXX draft pages and for each
# 2. Strip version from name
# 3. Check if the original page exists
# 4. Unhide master page
#
'''
#!/usr/bin/python3

import os
from datetime import datetime
from atlassian import Confluence
# from confluence.client import Confluence
import abqreltools as art
# import json


def create_wiki_log(wiki_page_list):
    '''Create output file'''
    todays_date = datetime.today().strftime('%Y-%m-%d')
    output_file = "outputUnlockMainPages." + todays_date + ".txt"
    output_dir = "./output_files"
    output_list = []
    output_list.append("|| Page ID || Name || Link ||\n")
    output_list.extend(wiki_page_list)
    wiki_file = open(os.path.join(output_dir,
                                 output_file), "w+")
    for line in output_list:
        wiki_file.write(line)
    wiki_file.close()


def main():
    '''Unlock new main pages'''
    # Get user credentials and space
    site_url = input("Confluence Cloud site URL, with protocol,"
                     + " and wiki, and exclude final slash, "
                     + "e.g. https://abiquo.atlassian.net/wiki: ")
    cloud_username = input("Cloud username: ")
    pwd = input("Cloud token string: ")
    space_key = input("Space key: ")

    release_version = input("Release version, e.g. v463: ")
    # print_version = input("Release print version, e.g. 4.6.3: ")

    # Log in to Confluence
    confluence = Confluence(
        url=site_url,
        username=cloud_username,
        password=pwd,
        cloud=True)

    draft_page_list = art.get_draft_pages(
        space_key, release_version, confluence)
#    draftPageOnlyList = []
    wiki_page_list = []

    for draft_page in draft_page_list:
        confluence_parameters = site_url, cloud_username, pwd
        main_page_id = ""
        draft_page_id = draft_page["content"]["id"][:]
        print("Version Page ID: ", draft_page_id)
        main_page_name = art.get_main_page_name(release_version, draft_page)
        print("Original Page Name: ", main_page_name)

        # full_draft_page = art.get_full_page(confluence, draft_page)

        main_page_exists = art.check_page_exists(
            confluence, space_key, main_page_name)
        print("main_page_exists response: ",main_page_exists)

        if main_page_exists:
            originalfull_draft_page = confluence.get_page_by_title(
                space_key, main_page_name)
            main_page_id = originalfull_draft_page["id"][:]

            norestrictions = [{"operation": "update", "restrictions":
                               {"user": [],
                                "group": []}},
                              {"operation": "read", "restrictions":
                               {"user": [],
                                "group": []}}]
            restns_response = art.upd_page_restns(confluence_parameters,
                                                  main_page_id, norestrictions)

        if str(restns_response) != "<Response [200]>":
            print("Error removing restrictions: ", restns_response)
        else:
            print("Success publishing page: ", restns_response)
        wiki_page_list.append("| " + main_page_id + " |"
                            " " + main_page_name + " |"
                            " [" + space_key + ":" + main_page_name + "] |\n")
    create_wiki_log(wiki_page_list)


# Calls the main() function
if __name__ == '__main__':
    main()
