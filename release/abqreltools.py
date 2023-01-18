'''
# Python script: release/abqreltools.py
# ---------------------------------------
# Module with common tools to use in scripts
# - create master pages for new version
# - publish draft pages (do release)
#
# Tools
# ------------------
# * Copy a draft page over a master page
# * Get the draft pages with vXXX in name
# * Strip version from name to create master page name
# * Check if page exists
# * Get ID of page
# * Get parent ID
# * Hide a page
# * Get all version of page
'''

#!/usr/bin/python3
import json
import requests

# Confluence code :-p
# This code sample uses the 'requests' library:
# http://docs.python-requests.org

from requests.auth import HTTPBasicAuth


def copy_cloud_page(page_id, confluence_parameters, destination_page):
    '''Use Confluence copy single page to copy the draft
       page over the master page'''

    site_url, cloud_username, pwd = confluence_parameters
    destination_type, destination_page_id, destination_page_title = destination_page

    #url = "https://your-domain.atlassian.net/wiki/rest/api/content/{id}/copy"
    url=site_url + "/rest/api/content/" + page_id + "/copy"
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
       auth=auth,
       timeout=30,
    )

    print("Response from copy_cloud_page: ", response.text)
    return response.json()


def get_draft_pages(space_key, release_version, confluence):
    '''Get all the draft pages for the release version'''
    print("get version pages: ")
    print("space_key: ", space_key)
    print("release_version: ", release_version)
    print("confluence: ", confluence)
    start_next = 0
    returned_size = 1
    while returned_size > 0:
        # get draft pages for release searching on "vXXX"
        cql = "space.key={} and (text ~ {})".format(space_key, release_version)
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
                    print("pg_id: ", pg_id)
        return page_list


def get_full_page(confluence, initial_page):
    '''Get more page details with expands'''
    page_got = ""
    pg_id = initial_page["content"]["id"]
    print("pg_id: ", pg_id)
    page_got = confluence.get_page_by_id(
        page_id=pg_id,
        expand='ancestors,version,body.storage')
    if page_got:
        print("Got the page!")
        # print("page_got: ", page_got)
    return page_got


def get_main_page_name(release_version, page):
    '''Get name of main page from draft page'''
    pg_name = str(page["content"]["title"])
    master_page_name = (str(pg_name)).replace(
        release_version, "").strip()
    # maybe use re.sub to only replace at end of string
    #                replace_in_page_name = release_version + "$"
    #                (re.sub(replace_in_page_name,"",pg_name)).strip()
    # or use original page name --> master_page_name = pg_name[:]
    return master_page_name


def check_page_exists(confluence, space_key, page_name):
    '''Check if a page exists, usually a master page'''
    print("check page exists")
    result = False
    if confluence.page_exists(
            space=space_key,
            title=page_name):
        print ("Page exists: ",page_name)
        result = True
    else:
        print ("Page doesn't exist: ", page_name)
        result = False
    return result


def upd_page_restns(confluence_parameters, page_id, restrictions):
    '''Unhide new master pages as part of release
       by removing page restrictions'''
    site_url, inuname, inpsswd = confluence_parameters
    payload = json.dumps(restrictions)
    # /wiki/rest/api/content/{id}/restriction
    url = site_url + "/rest/api/content/" + page_id + "/restriction"
    api_headers = {}
    api_headers["Accept"] = "application/json"

    response = requests.get(url, verify=False, 
                                        headers=api_headers,
                                        auth=(inuname, inpsswd),
                                        timeout=30)
    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": "))) 
    # api_headers["Content-Type"] = "application/json"

    # restns_response = requests.put(url, verify=False, data=payload,
    #                                     headers=api_headers,
    #                                     auth=(inuname, inpsswd),
    #                                     timeout=30)
    return response.json


def hide_page(confluence_parameters, page_id, restrictions):
    '''Hide a page for group and user?'''
    site_url, cloud_username, pwd = confluence_parameters
    accountId, groupName = restrictions
    auth = HTTPBasicAuth(cloud_username, pwd)    
    operationKeys = ["read", "update"]
    for operationKey in operationKeys:
        url = site_url + "/rest/api/content/" + page_id \
              + "/restriction/byOperation/" + operationKey + "/user?accountId=" + accountId

        response = requests.request(
             "PUT",
             url,
             auth=auth
        )
        print("user: ", operationKey, " - ", response.json)

        url = site_url + "/rest/api/content/" + page_id \
             + "/restriction/byOperation/" + operationKey + "/group/" + groupName

        response = requests.request(
            "PUT",
            url,
            auth=auth
        )
        print("group: ", operationKey, " - ", response.json)


def unlock_page(confluence_parameters, page_id):
    '''Hide a page for group and user?'''
    site_url, cloud_username, pwd = confluence_parameters
    auth = HTTPBasicAuth(cloud_username, pwd)    
    operationKeys = ["read", "update"]
    for operationKey in operationKeys:
        url = site_url + "/rest/api/content/" + page_id \
              + "/restriction"

        response = requests.request(
             "DELETE",
             url,
             auth=auth
        )
        print("remove restrictions", response.json)


# def get_all_page_versions(site_url, inuname, inpsswd,
#                  space_key, page_id):
#     # apiUrl = 'https://' + site_url
#     rurl = site_url + "/rest/api/content/" + page_id + "/version"
#     aAppJson = "application/json"
#     aHeaders = {}
#     aHeaders["Accept"] = aAppJson[:]
#     pgVersionsResponse = requests.get(rurl, verify=False,
#                                       params={'expand': 'content'},
#                                       headers=aHeaders,
#                                       auth=(inuname, inpsswd))
#     # print("pgVersions:", pgVersionsResponse.status_code)
#     # print("pgVJSON:", pgVersionsResponse.json())
#     return pgVersionsResponse.json()


def main():
    '''This module has tools to do the documentation release
       These common tools are used in scripts
       To create main pages for new version
       And to publish draft pages (do the release), etc'''
    print("Please use the release scripts rather than this module directly")


# Calls the main() function
if __name__ == '__main__':
    main()
