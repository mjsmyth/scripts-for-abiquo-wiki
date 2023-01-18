# #!/usr/bin/python3
# Python script: release/moveDraftPages
# ---------------------------------------
# Script designed to move draft pages of older version
# Gets pages with vXXX and moves them to another space
# You need to create a parent page called 
# "original space_key + "_" + release_version"
# e.g. doc_v603
#
# Move draft pages
# ------------------
# 1. Get the vXXX draft pages
# 2. Get page where you want to move pages (parentId)
# Note: You must create this page before you run the script!!!
# 2. Move draft pages to location
# If the draft page exists:
# Rename it in the old space
# Then move it to the new space


import os
from atlassian import Confluence
from datetime import datetime
import abqreltools as art
import json


def create_wiki_log(wiki_page_list):
    todays_date = datetime.today().strftime('%Y-%m-%d')
    output_file = "outputMoveDraftPages." + todays_date + ".txt"
    output_dir = "./output_files"
    output_list = []
    output_list.append("|| Page ID || Name || Link ||\n")
    output_list.extend(wiki_page_list)
    wiki_file = open(os.path.join(output_dir,
                    output_file), "w+")
    for line in output_list:
        wiki_file.write(line)
    wiki_file.close()


def getParentPageIdByTitle(confluence, targetspace_key, pageName):
    parentPageId = ""
    parentPageExists = art.check_page_exists(
        confluence, targetspace_key, pageName)
    if parentPageExists:
        parentfull_draft_page = confluence.get_page_by_title(
            targetspace_key, pageName)
        parentPageId = parentfull_draft_page["id"][:]
    return parentPageId


def main():
    # Get user credentials and space
    print("Will move pages to under a new page vXXX_pages")
    # Get user credentials and space
    site_url = input("Confluence Cloud site URL, with protocol,"
                     + " and wiki, and exclude final slash, "
                     + "e.g. https://abiquo.atlassian.net/wiki: ")
    cloud_username = input("Cloud username: ")
    pwd = input("Cloud token string: ")
    space_key = input("Space key: ")
    targetspace_key = input("Target space key: ")
    release_version = input("Release version, e.g. v463: ")
    # print_version = input("Release print version, e.g. 4.6.3: ")

    # Log in to Confluence
    confluence = Confluence(
        url=site_url,
        username=cloud_username,
        password=pwd,
        cloud=True)

    # site_url = input("Enter Confluence site URL (no protocol & final slash): ")
    # inuname = input("Username: ")
    # inpsswd = input("Password: ")
    # space_key = input("Space key: ")
    # targetspace_key = input("Target space key: ")
    # release_version = input("Release version, e.g. v463: ")

    parent_title = str(space_key + "_" + release_version)
    parentPrint = "page: " + parent_title + " " \
                  "in space: ", targetspace_key
    print("Parent page is: ", parentPrint)
    confirmParentPage = input("Waiting while you create parent!: ")
    if confirmParentPage:
        print("Moving pages...")

    # print_version = input("Release print version, e.g. 4.6.3: ")
    versionWiki = space_key[:]
    if "doc" in space_key:
        versionWiki = space_key + " " + "ABI" + release_version[1:2] + " "
    # confluence = Confluence(
    #     url='https://' + site_url,
    #     username=inuname,
    #     password=inpsswd)

    parentPageId = getParentPageIdByTitle(confluence,
                                          targetspace_key,
                                          parent_title)
    if not parentPageId:
        noparent = "Please create " + parentPrint
        print(noparent)
    draft_page_list = art.get_draft_pages(
        space_key, release_version, confluence)
#    draftPageOnlyList = []
    wiki_page_list = []

    for basePage in draft_page_list:
        page = art.get_full_page(confluence, basePage)
        page["version"]["number"] += 1
        movedPageTitle = page["title"][:]
        newPageTitle = page["title"] + " " + versionWiki
        page["title"] = newPageTitle[:]
        # print(json.dumps(page, indent=4))
    # Get more page details with expands
        draft_page_id = page["id"][:]
        # print("draft_page_id: ", draft_page_id)
        # print("target_title: ", newPageTitle)

        movedPageExists = art.check_page_exists(
            confluence, targetspace_key, movedPageTitle)
        print("movedPageExists: ", movedPageExists)
        if movedPageExists:
            # update existing page before moving
            updatedPage = confluence.update_page(
                draft_page_id,
                newPageTitle,
                body=page["body"]["storage"]["value"],
                representation="storage")
            if updatedPage["id"]:
                movedPageTitle = newPageTitle[:]
            else:
                print("updatedResponse: ", updatedPage)

        moveResponse = confluence.move_page(
            space_key,
            draft_page_id,
            target_id=parentPageId,
            position="append")
        print("moveResponse: ", json.dumps(moveResponse, indent=4))
        if moveResponse["page"]["id"]:
            new_page_id = moveResponse["page"]["id"]
        else:
            print("moveResponse: ", moveResponse)
        wikiPrint = "| " + new_page_id + " |" \
                    " " + newPageTitle + " |" \
                    " [" + targetspace_key + ":" + movedPageTitle + "] |\n"
        wiki_page_list.append(wikiPrint)
    create_wiki_log(wiki_page_list)


# Calls the main() function
if __name__ == '__main__':
    main()
