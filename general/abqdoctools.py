# #!/usr/bin/python3
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


import requests
import json
import re
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


def updPgRestns(site_URL, inuname, inpsswd,
                spacekey, page_id, restrictions):
    payload = json.dumps(restrictions)
    # /wiki/rest/api/content/{id}/restriction
    url = site_URL + "/rest/api/content/" + page_id + "/restriction"
    apiAppJson = "application/json"
    apiHeaders = {}
    apiHeaders["Accept"] = apiAppJson[:]
    apiHeaders["Content-Type"] = apiAppJson[:]
    restrictionsResponse = requests.put(url, verify=False, data=payload,
                                        headers=apiHeaders,
                                        auth=(inuname, inpsswd))
    return restrictionsResponse


def getParentPageId(page):
    ancestorsList = page["ancestors"]
    parentPage = ancestorsList.pop()
    parentPageId = parentPage["id"]
    return(parentPageId)


def updateWiki(updatePageTitle, wikiContent, wikiFormat, site_URL,
               cloud_username, pwd, spacekey, tableReplaceString,
               release_version, print_version):

    # Log in to Confluence
    confluence = Confluence(
        url=site_URL,
        username=cloud_username,
        password=pwd,
        cloud=True)

    parentPageId = 0
    page = {}

    versionPageTitle = updatePageTitle + " " + release_version
    # If a version page exists operate on that
    if confluence.page_exists(spacekey, versionPageTitle):
        versionPageId = confluence.get_page_id(spacekey, versionPageTitle)
        page = confluence.get_page_by_id(
            page_id=versionPageId,
            expand='ancestors,version,body.storage')
    # Otherwise get the master page to save it as the version page
    else:
        pageId = confluence.get_page_id(spacekey, updatePageTitle)
        page = confluence.get_page_by_id(
            page_id=pageId,
            expand='ancestors,version,body.storage')
    parentPageId = getParentPageId(page)
    origPageContent = page["body"]["storage"]["value"][:]
    print("origPageContent: ", origPageContent)
    # Convert events table to Confluence XHTML format from wiki style
    if wikiFormat is not "storage":
        pageContentDict = confluence.convert_wiki_to_storage(wikiContent)
    pageContent = pageContentDict["value"][:]
    newPageContent = ""
    if "table" in origPageContent:
        newPageContent = re.sub(tableReplaceString,
                                pageContent, origPageContent)
    else:
        newPageContent = origPageContent + pageContent
    # status = confluence.create_page(spacekey,
    #                                 releasePageTitle,
    #                                 newPageContent,
    #                                 parent_id=parentPageId,
    #                                 type='page',
    #                                 representation='storage',
    #                                 editor='v2')

    # Update page or create page if it does not exist
    status = confluence.update_or_create(
        parentPageId, versionPageTitle,
        newPageContent, representation='storage',
        version_comment=print_version)

    if status["id"]:
        versionPageId = status["id"][:]
    else:
        print("Create or update page ", versionPageTitle,
              " failed with status: ", status)
        return False

    restrictions = [{"operation": "update", "restrictions":
                     {"user": [{"type": "known",
                                "username": cloud_username}],
                      "group": [{"type": "group",
                                 "name": "abiquo-team"}]}},
                    {"operation": "read", "restrictions":
                     {"user": [{"type": "known",
                                "username": cloud_username}],
                      "group": [{"type": "group",
                                 "name": "abiquo-team"}]}}]

    restrictionsResponse = updPgRestns(site_URL, cloud_username,
                                       pwd, spacekey,
                                       versionPageId, restrictions)
    if str(restrictionsResponse) != "<response [200]>":
        print("restrictionsResponse: ", restrictionsResponse)
    return True


def main():
    # Print something to let user know what is going on
    print("This module has tools to do the documentation release\n")
    print("These common tools are used in scripts\n")
    print("To create master pages for new version\n")
    print("And to publish draft pages (do release)\n")


# Calls the main() function
if __name__ == '__main__':
    main()
