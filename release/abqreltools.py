# #!/usr/bin/python3
# Python script: release/abqreltools.py
# ---------------------------------------
# Module with common tools to use in scripts
# - create master pages for new version
# - publish draft pages (do release)
#
# Tools
# ------------------
# 1. Get the draft pages with vXXX in name
# 2. Strip version from name to create master page name
# 3. Check if page exists
# 4. Get ID of page
# 5. Get parent ID
# 6. Hide a page
# 7. Get all version of page


import requests
import json


def getVersionPgs(spacekey, release_version, confluence):
    start_next = 0
    returned_size = 1
    while returned_size > 0:
        # get draft pages for release searching on "vXXX"
        cql = "space.key={} and (text ~ {})".format(spacekey, release_version)
        results = confluence.cql(cql, limit=200, start=start_next)
        returned_size = results["size"]
        page_list = []
        for page in results["results"]:
            pg_id = page["content"]["id"]
            # pg_name = str(page["content"]["title"])
            # check the vXXX in title and not only in the page content
            # specific title search will get vXXX when you use vXX
            page_links_web_ui = str(page["content"]["_links"]["webui"])
            if release_version.strip().lower() in page_links_web_ui.lower():
                # only work with pages, not attachments
                if "att" not in pg_id:
                    page_list.append(page)
        return page_list


def getPgFull(confluence, initial_page):
    # Get more page details with expands
    pg_id = initial_page["content"]["id"]
    page_got = confluence.get_page_by_id(
        page_id=pg_id,
        expand='ancestors,version,body.storage')
    return page_got


def getOrigPgName(release_version, page):
    pg_name = str(page["content"]["title"])
    master_page_name = (str(pg_name)).replace(
        release_version, "").strip()
    # maybe use re.sub to only replace at end of string
    #                replace_in_page_name = release_version + "$"
    #                (re.sub(replace_in_page_name,"",pg_name)).strip()
    # or use original page name --> master_page_name = pg_name[:]
    return master_page_name


def checkPgExists(confluence, spacekey, page_name):
    if confluence.page_exists(
            space=spacekey,
            title=page_name):
        return True
    else:
        return False


def updPgRestns(site_URL, inuname, inpsswd,
                spacekey, page_id, restrictions):
    payload = json.dumps(restrictions)
    apiUrl = 'https://' + site_URL
    url = apiUrl + "/rest/experimental/content/" + page_id + "/restriction"
    apiAppJson = "application/json"
    apiHeaders = {}
    apiHeaders["Accept"] = apiAppJson[:]
    apiHeaders["Content-Type"] = apiAppJson[:]
    restrictionsResponse = requests.put(url, verify=False, data=payload,
                                        headers=apiHeaders,
                                        auth=(inuname, inpsswd))
    return restrictionsResponse


def getAllPgVers(site_URL, inuname, inpsswd,
                 spacekey, page_id):
    apiUrl = 'https://' + site_URL
    rurl = apiUrl + "/rest/experimental/content/" + page_id + "/version"
    aAppJson = "application/json"
    aHeaders = {}
    aHeaders["Accept"] = aAppJson[:]
    pgVersionsResponse = requests.get(rurl, verify=False,
                                      params={'expand': 'content'},
                                      headers=aHeaders,
                                      auth=(inuname, inpsswd))
    # print("pgVersions:", pgVersionsResponse.status_code)
    # print("pgVJSON:", pgVersionsResponse.json())
    return pgVersionsResponse.json()


def main():
    # Print something to let user know what is going on
    print("This module has tools to do the documentation release\n")
    print("These common tools are used in scripts\n")
    print("To create master pages for new version\n")
    print("And to publish draft pages (do release)\n")


# Calls the main() function
if __name__ == '__main__':
    main()
