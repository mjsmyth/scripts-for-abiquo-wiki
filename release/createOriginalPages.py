# #!/usr/bin/python3
# Python script: release/relCreatePages
# ---------------------------------------
# Script designed to create original pages for new version
# Gets pages with vXXX and creates pages without it
#
# Create original pages
# ------------------
# 1. Get the vXXX draft pages and for each
# 2. Strip version from name
# 3. Check if the original page exists --> remove from pages
# 4. Get ID of draft page
# 5. Get parent ID
# 7. Create new page
# 8. Hide new page


import os
from atlassian import Confluence
from datetime import datetime
import abqreltools as art


def createWikiLogPage(wikiPageList):
    todaysDate = datetime.today().strftime('%Y-%m-%d')
    output_file = "outputCreateOriginalPages." + todaysDate + ".txt"
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
    # print_version = input("Release print version, e.g. 4.6.3: ")

    confluence = Confluence(
        url='https://' + site_URL,
        username=inuname,
        password=inpsswd)

    versionPageList = art.getVersionPgs(
        spacekey, release_version, confluence)
    draftPageList = []
    wikiPageList = []

    for page in versionPageList:
        originalPageName = art.getOrigPgName(release_version, page)
        originalPageExists = art.checkPgExists(
            confluence, spacekey, originalPageName)
        if originalPageExists is False:
            draftPageList.append(page)

    for page in draftPageList:
        pageFull = art.getPgFull(confluence, page)
        originalPageName = art.getOrigPgName(release_version, page)
        ancestorsList = pageFull["ancestors"]
        parentPage = ancestorsList.pop()
        parentPageId = parentPage["id"]

        pageContent = pageFull["body"]["storage"]["value"]
        # print("parentPageId: ", parentPageId)
        # print("originalPageName: ", originalPageName)
        # print("pageContent:", pageContent)

        status = confluence.create_page(spacekey,
                                        originalPageName,
                                        pageContent,
                                        parent_id=parentPageId,
                                        type='page',
                                        representation='storage',
                                        editor='v2')
        if status["id"]:
            newPageId = status["id"]
        else:
            print ("status", status)

        restrictions = [{"operation": "update", "restrictions":
                        {"user": [{"type": "known",
                                   "username": "maryjane.smyth"}],
                         "group": [{"type": "group",
                                    "name": "abiquo-team"}]}},
                        {"operation": "read", "restrictions":
                        {"user": [{"type": "known",
                                   "username": inuname}],
                         "group": [{"type": "group",
                                    "name": "abiquo-team"}]}}]

        restrictionsResponse = art.updPgRestns(site_URL, inuname,
                                               inpsswd, spacekey,
                                               newPageId, restrictions)
        if str(restrictionsResponse) != "<response [200]>":
            print("restrictionsResponse: ", restrictionsResponse)
        wikiPageList.append("| " + newPageId + " |"
                            " " + originalPageName + " |"
                            " [" + spacekey + ":" + originalPageName + "] |\n")
    createWikiLogPage(wikiPageList)


# Calls the main() function
if __name__ == '__main__':
    main()
