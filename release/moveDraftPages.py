# #!/usr/bin/python3
# Python script: release/moveDraftPages
# ---------------------------------------
# Script designed to move draft pages of older version
# Gets pages with vXXX and moves them to another space
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


def createWikiLogPage(wikiPageList):
    todaysDate = datetime.today().strftime('%Y-%m-%d')
    output_file = "outputMoveDraftPages." + todaysDate + ".txt"
    output_dir = "./output_files"
    output_list = []
    output_list.append("|| Page ID || Name || Link ||\n")
    output_list.extend(wikiPageList)
    wikiFile = open(os.path.join(output_dir,
                    output_file), "w+")
    for line in output_list:
        wikiFile.write(line)
    wikiFile.close()


def getParentPageIdByTitle(confluence, targetSpacekey, pageName):
    parentPageId = ""
    parentPageExists = art.checkPgExists(
        confluence, targetSpacekey, pageName)
    if parentPageExists:
        parentPageFull = confluence.get_page_by_title(
            targetSpacekey, pageName)
        parentPageId = parentPageFull["id"][:]
    return parentPageId


def main():
    # Get user credentials and space
    print("Will move pages to under a new page vXXX_pages")
    site_URL = input("Enter Confluence site URL (no protocol & final slash): ")
    inuname = input("Username: ")
    inpsswd = input("Password: ")
    spacekey = input("Space key: ")
    targetSpacekey = input("Target space key: ")
    release_version = input("Release version, e.g. v463: ")

    parent_title = str(spacekey + "_" + release_version)
    parentPrint = "page: " + parent_title + " " \
                  "in space: ", targetSpacekey
    print("Parent page is: ", parentPrint)
    confirmParentPage = input("Waiting while you create parent!: ")
    if confirmParentPage:
        print("Moving pages...")

    # print_version = input("Release print version, e.g. 4.6.3: ")
    versionWiki = spacekey[:]
    if "doc" in spacekey:
        versionWiki = spacekey + " " + "ABI" + release_version[1:2] + " "
    confluence = Confluence(
        url='https://' + site_URL,
        username=inuname,
        password=inpsswd)

    parentPageId = getParentPageIdByTitle(confluence,
                                          targetSpacekey,
                                          parent_title)
    if not parentPageId:
        noparent = "Please create " + parentPrint
        print(noparent)
    versionPageList = art.getVersionPgs(
        spacekey, release_version, confluence)
#    draftPageOnlyList = []
    wikiPageList = []

    for basePage in versionPageList:
        page = art.getPgFull(confluence, basePage)
        page["version"]["number"] += 1
        movedPageTitle = page["title"][:]
        newPageTitle = page["title"] + " " + versionWiki
        page["title"] = newPageTitle[:]
        # print(json.dumps(page, indent=4))
    # Get more page details with expands
        versionPageId = page["id"][:]
        # print("versionPageId: ", versionPageId)
        # print("target_title: ", newPageTitle)

        movedPageExists = art.checkPgExists(
            confluence, targetSpacekey, movedPageTitle)
        print("movedPageExists: ", movedPageExists)
        if movedPageExists:
            # update existing page before moving
            updatedPage = confluence.update_page(
                versionPageId,
                newPageTitle,
                body=page["body"]["storage"]["value"],
                representation="storage")
            if updatedPage["id"]:
                movedPageTitle = newPageTitle[:]
            else:
                print("updatedResponse: ", updatedPage)

        moveResponse = confluence.move_page(
            spacekey,
            versionPageId,
            target_id=parentPageId,
            position="append")
        print("moveResponse: ", json.dumps(moveResponse, indent=4))
        if moveResponse["page"]["id"]:
            newPageId = moveResponse["page"]["id"]
        else:
            print ("moveResponse: ", moveResponse)
        wikiPrint = "| " + newPageId + " |" \
                    " " + newPageTitle + " |" \
                    " [" + targetSpacekey + ":" + movedPageTitle + "] |\n"
        wikiPageList.append(wikiPrint)
    createWikiLogPage(wikiPageList)


# Calls the main() function
if __name__ == '__main__':
    main()
