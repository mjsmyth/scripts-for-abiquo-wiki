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

# Confluence code :-p
# This code sample uses the 'requests' library:
# http://docs.python-requests.org

from requests.auth import HTTPBasicAuth


# POST <baseurl>/wiki/rest/api/content/<source_page_id>/copy
# {
#     "destination": {
#         "type": "parent_page",
#         "value": "<parent_id>"
#     },
#     "copyAttachments": true,
#     "copyProperties": true
# }
# It should be successfully copied and create new page with <new_page_id>.

# Copy the source page again, but now with "existing_page" destination type to <new_page_id> with "copyContentProperties" and "copyAttachments" flags:
# POST <baseurl>/wiki/rest/api/content/<source_page_id>/copy
# {
#     "destination": {
#         "type": "existing_page",
#         "value": "<new_page_id>"
#     },
#     "copyAttachments": true,
#     "copyProperties": true
# }

# Use this to create master pages and update master pages

# Create master pages with same parent as draft pages
# - parentPageId = draft page parent
# - master page name = draft page name - release version
# - destination_type = parent_page

# Publish release by updating master pages from draft pages
# - new_page_id = master page id
# - destination_type = existing_page
# - parentPageId = null

def copyCloudPage(page_id, site_URL,
                  cloud_username, pwd,
                  destination_page_id,
                  destination_storage_value,
                  destination_type,
                  destination_page_title,
                  release_version, 
                  print_version):


    #        parentPageId, versionPageTitle,
    #        newPageContent, representation='storage',
    #        version_comment=print_version

    #url = "https://your-domain.atlassian.net/wiki/rest/api/content/{id}/copy"
    url=site_URL + "/rest/api/content/" + page_id + "/copy"
    # username=cloud_username
    # password=pwd
    
    #auth = HTTPBasicAuth("email@example.com", "<api_token>")
    auth = HTTPBasicAuth(cloud_username, pwd)

    headers = {
       "Accept": "application/json;charset=UTF-8",
       "Content-Type": "application/json"
    }

    payload = json.dumps( {
      "copyAttachments": True,
      "copyPermissions": True,
      "copyProperties": True,
      "copyLabels": True,
      "copyCustomContents": True,
      "destination": {
        "type": destination_type,
        "value": destination_page_id,
      },
      "pageTitle": destination_page_title
    })

    response = requests.request(
       "POST",
       url,
       data=payload,
       headers=headers,
       auth=auth
    )

    print(response.text)
    return(response.text)


def getVersionPgs(spacekey, release_version, confluence):
    print("get version pages: ")
    print("spacekey: ", spacekey)
    print("release_version: ", release_version)
    print("confluence: ", confluence)
    start_next = 0
    returned_size = 1
    while returned_size > 0:
        # get draft pages for release searching on "vXXX"
        cql = "space.key={} and (text ~ {})".format(spacekey, release_version)
        results = confluence.cql(cql, start=start_next, limit=None,
                                 expand=None, include_archived_spaces=None,
                                 excerpt=None)

        if results:
            print("results: ", results)
#        results = confluence.cql(cql, limit=200, start=start_next)
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
            print("page: ", page)
        return page_list


def getPgFull(confluence, initial_page):
    # Get more page details with expands
    pg_id = initial_page["content"]["id"]
    print("pg_id: ", pg_id)
    page_got = confluence.get_page_by_id(
        page_id=pg_id,
        expand='ancestors,version,body.storage')
    if page_got:
        print("page_got: ", page_got)
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
    print("check page exists")
    if confluence.page_exists(
            space=spacekey,
            title=page_name):
        print ("Page exists: ",page_name)
        return True
    else:
        print ("Page doesn't exist: ", page_name)
        return False


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


def getAllPgVers(site_URL, inuname, inpsswd,
                 spacekey, page_id):
    # apiUrl = 'https://' + site_URL
    rurl = site_URL + "/rest/api/content/" + page_id + "/version"
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
