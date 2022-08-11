# #!/usr/bin/python3
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
# 4. Get ID of original page
# ?. Get parent ID???
# 5. Get content of draft page and compare --> if same, drop
# 7. Get history message
# 8. Update master page
# 9. Unhide master page
#
# TODO get all history messages

import os
from atlassian import Confluence
# from confluence.client import Confluence
from datetime import datetime
import abqreltools as art
import json


def createWikiLogPage(wikiPageList):
    todaysDate = datetime.today().strftime('%Y-%m-%d')
    output_file = "outputPublishDraftPages." + todaysDate + ".txt"
    output_dir = "./output_files"
    output_list = []
    output_list.append("|| Page ID || Name || Link ||\n")
    output_list.extend(wikiPageList)
    wikiFile = open(os.path.join(output_dir,
                    output_file), "w+")
    for line in output_list:
        wikiFile.write(line)
    wikiFile.close()


def main():
    # Get user credentials and space
    site_URL = input("Enter Confluence site URL (no protocol & final slash): ")
    inuname = input("Username: ")
    inpsswd = input("Password: ")
    spacekey = input("Space key: ")
    release_version = input("Release version, e.g. v463: ")
    print_version = input("Release print version, e.g. 4.6.3: ")

    confluence = Confluence(
        url='https://' + site_URL,
        username=inuname,
        password=inpsswd)

    versionPageList = art.getVersionPgs(
        spacekey, release_version, confluence)
#    draftPageOnlyList = []
    wikiPageList = []

    for page in versionPageList:
        releasePageId = ""
        versionPageId = page["content"]["id"][:]
        originalPageName = art.getOrigPgName(release_version, page)

        pageFull = art.getPgFull(confluence, page)

        ancestorsList = pageFull["ancestors"]
        parentPage = ancestorsList.pop()
        parentPageId = parentPage["id"]

        pageContent = pageFull["body"]["storage"]["value"]
        # print("parentPageId: ", parentPageId)
        # print("originalPageName: ", originalPageName)
        # print("pageContent:", pageContent)
        originalPageId = ""
        originalPageExists = art.checkPgExists(
            confluence, spacekey, originalPageName)
        pageUpdated = False
        if originalPageExists:
            originalPageFull = confluence.get_page_by_title(
                spacekey, originalPageName)
            originalPageId = originalPageFull["id"][:]
        # Compare content and check is already updated or not
            pageUpdated = confluence.is_page_content_is_already_updated(
                originalPageId, pageContent)
            releasePageId = originalPageId[:]

        versionComment = print_version + " - release "
        if not pageUpdated:
            if originalPageExists:
                pgVersionsResp = art.getAllPgVers(
                    site_URL, inuname, inpsswd, spacekey, versionPageId)
                for pgVersion in pgVersionsResp["results"]:
                    print ("pgVersion: ", pgVersion)
                    if print_version in pgVersion["message"]:
                        print("pgv msg: ", pgVersion["message"])
                        versionComment = pgVersion["message"][:]
                        break

            # Update page or create page if it does not exist
            status = confluence.update_or_create(
                parentPageId, originalPageName,
                pageContent, representation='storage',
                version_comment=versionComment)

            if status["id"]:
                releasePageId = status["id"][:]
            else:
                print ("status", status)

            # set the page to unhide and print name to be the original page

        norestrictions = [{"operation": "update", "restrictions":
                          {"user": [],
                           "group": []}},
                          {"operation": "read", "restrictions":
                          {"user": [],
                           "group": []}}]

        restrictionsResponse = art.updPgRestns(site_URL, inuname,
                                               inpsswd, spacekey,
                                               releasePageId, norestrictions)
        if str(restrictionsResponse) != "<response [200]>":
            print("restrictionsResponse: ", restrictionsResponse)

        wikiPageList.append("| " + releasePageId + " |"
                            " " + originalPageName + " |"
                            " [" + spacekey + ":" + originalPageName + "] |\n")
    createWikiLogPage(wikiPageList)


# Calls the main() function
if __name__ == '__main__':
    main()
