# #!/usr/bin/python3
'''
# Python script: release/abqdoctools.py
# ---------------------------------------
# Module with common tools to use in scripts
# - Update or create a draft page
# - publish draft pages (do release)
#
# Tools
# ------------------
# 1. Get a full paage with all info
# 2. Check if page exists
# 3. Update page restrictions to hide a page
# 4. Get parent page ID
# 5. Hide a page
# 6. Update the wiki
'''

import json
import re
import sys
import requests
from atlassian import Confluence

# Note may use these in the future if proper checks logging etc
# def getPgFull(confluence, initial_page):
#     # Get more page details with expands
#     pg_id = initial_page["content"]["id"]
#     print("pg_id: ", pg_id)
#     page_got = confluence.get_page_by_id(
#         page_id=pg_id,
#         expand='ancestors,version,body.storage')
#     if page_got:
#         print("page_got: ", page_got)
#     return page_got


# def checkPgExists(confluence, spacekey, page_name):
#     print("check page exists")
#     if confluence.page_exists(
#             space=spacekey,
#             title=page_name):
#         return True
#     else:
#         return False


def update_page_restrictions(site_url, inuname, inpsswd,
                page_id, restrictions):
    '''Update page restrictions?'''
    payload = json.dumps(restrictions)
    # /wiki/rest/api/content/{id}/restriction
    url = site_url + "/rest/api/content/" + page_id + "/restriction"
    app_json = "application/json"
    api_headers = {}
    api_headers["Accept"] = app_json[:]
    api_headers["Content-Type"] = app_json[:]
    restrictions_response = requests.put(url, verify=False, data=payload,
                                        headers=api_headers,
                                        auth=(inuname, inpsswd), timeout=300)
    return restrictions_response


def get_parent_page_id(page):
    '''Get the ID of the parent page'''
    ancestors_list = page["ancestors"]
    parent_page = ancestors_list.pop()
    parent_page_id = parent_page["id"]
    return parent_page_id


def updateWiki(update_page_title, wiki_content, wiki_format, site_url,
               cloud_username, pwd, spacekey,
               release_version, print_version, operation):

    # Log in to Confluence
    confluence = Confluence(
        url=site_url,
        username=cloud_username,
        password=pwd,
        cloud=True)

    parent_page_id = 0
    page = {}

    version_page_title = update_page_title + " " + release_version
    # If a version page exists operate on that
    if confluence.page_exists(spacekey, version_page_title):
        version_page_id = confluence.get_page_id(spacekey, version_page_title)
        page = confluence.get_page_by_id(
            page_id=version_page_id,
            expand='ancestors,version,body.storage')
    # Otherwise get the master page to save it as the version page
    else:
        if confluence.page_exists(spacekey, update_page_title):
            pageId = confluence.get_page_id(spacekey, update_page_title)
            page = confluence.get_page_by_id(
                page_id=pageId,
                expand='ancestors,version,body.storage')
        else:
            print("Cannot find master page: ", update_page_title)
            sys.exit()
    parent_page_id = get_parent_page_id(page)
    orig_page_content = page["body"]["storage"]["value"][:]
    # print("orig_page_content: ----------\n")
    # print(orig_page_content)
    # print("end orig_page_content ------\n")
    # Convert events table to Confluence XHTML format from wiki style
    if wiki_format is True:
        page_content_dict = confluence.convert_wiki_to_storage(wiki_content)
        page_content = page_content_dict["value"][:]
        with open("./output_files/pageouttest.txt", "w") as f:
            f.write(page_content)
    else:
        page_content = wiki_content[:]
    new_page_content = ""
    replace_string = r'<table(.*?)</table>'
    if operation == "append":
        new_page_content = orig_page_content + page_content
    elif operation == "replacetable":
        # replace the table
        new_page_content = re.sub(replace_string, page_content, orig_page_content, 0, re.DOTALL)
    elif operation == "replace":
        print("Replace page")
        new_page_content = page_content
    else:
        print("Abiquo doc tools: No operation specified")
        sys.exit()
    # status = confluence.create_page(spacekey,
    #                                 releasePageTitle,
    #                                 new_page_content,
    #                                 parent_id=parent_page_id,
    #                                 type='page',
    #                                 representation='storage',
    #                                 editor='v2')
    #
    # jsonPageContent.update({"metdata":{"properties": {"editor": {"key": "editor", "value": "v2"}}}})
    #
    # Update page or create page if it does not exist
    # parent_id, title, body, representation='storage', 
    # minor_edit=False, version_comment=None, editor=None, full_width=False,
    status = confluence.update_or_create(
        parent_page_id, version_page_title,
        new_page_content, representation='storage',
        version_comment=print_version, editor="v2",
        full_width=True)

    if status["id"]:
        version_page_id = status["id"][:]
        print("Create or update page ", version_page_title,
              " finished with status: ", status)
    else:
        print("Create or update page ", version_page_title,
              " failed with status: ", status)
        return False

    # restrictions = [{"operation": "update", "restrictions":
    #                  {"user": [{"type": "known",
    #                             "username": cloud_username}],
    #                   "group": [{"type": "group",
    #                              "name": "abiquo-team"}]}},
    #                 {"operation": "read", "restrictions":
    #                  {"user": [{"type": "known",
    #                             "username": cloud_username}],
    #                   "group": [{"type": "group",
    #                              "name": "abiquo-team"}]}}]

    # restrictionsResponse = update_page_restrictions(site_url, cloud_username,
    #                                    pwd, spacekey,
    #                                    version_page_id, restrictions)
    # if str(restrictionsResponse) != "<response [200]>":
    #     print("restrictionsResponse: ", restrictionsResponse)
    return True


def main():
    '''Documentation tools module for Abiquo wiki scripts'''
    # Print something to let user know what is going on
    print("This module has tools to do the documentation release\n")
    print("These common tools are used in scripts\n")
    print("To create master pages for new version\n")
    print("And to publish draft pages (do release)\n")


# Calls the main() function
if __name__ == '__main__':
    main()
