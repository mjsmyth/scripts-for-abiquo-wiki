'''
# Python script: createMainPages
# ---------------------------------------
# Create main pages for new pages in new version
# Gets draft pages with vXXX and creates main pages for them
#
# Create main pages
# ------------------
# 1. Get the vXXX draft pages
# 2. Strip version from name
# 3. Check if the main page exists --> remove from list
# 4. Get ID of draft page
# 5. Get parent ID
# 7. Create new page
# 8. Hide new page
'''
#!/usr/bin/python3

import os
#import json
from datetime import datetime
from atlassian import Confluence
import abqreltools as art


def create_wiki_log(wiki_page_list):
    '''Create some kind of log'''
    todays_date = datetime.today().strftime('%Y-%m-%d')
    output_file = "outputCreateMainPages." + todays_date + ".txt"
    output_dir = "./output_files"
    output_list = []
    output_list.append("|| Page ID || Name || Link ||\n")
    output_list.extend(wiki_page_list)
    wiki_file = open(os.path.join(output_dir,
                                 output_file), "w+")
    for line in output_list:
        wiki_file.write(line)
    wiki_file.close()


def restrict_main_pages(confluence_parameters, new_page_id):
    site_url, cloud_username, pwd = confluence_parameters
    '''Restrict new main pages'''
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

    restns_response = art.upd_page_restns(confluence_parameters,
                                          new_page_id, restrictions)
    return restns_response


def main():
    '''Create main pages by copying draft pages'''
    # Get user credentials and space
    site_url = input("Confluence Cloud site URL, with protocol,"
                     + " and wiki, and exclude final slash, "
                     + "e.g. https://abiquo.atlassian.net/wiki: ")
    cloud_username = input("Cloud username: ")
    pwd = input("Cloud token string: ")
    accountId = input("Cloud user accountId: ")
    space_key = input("Space key: ")

    release_version = input("Release version, e.g. v463: ")
    confluence_parameters = (site_url, cloud_username, pwd)
    # Log in to Confluence
    confluence = Confluence(
        url=site_url,
        username=cloud_username,
        password=pwd,
        cloud=True)

    draft_page_list = art.get_draft_pages(
        space_key, release_version, confluence_parameters)
    wiki_page_list = []
    create_page_list = []

    for check_draft_page in draft_page_list:
        main_page_exists = ""
        main_page_name = art.get_main_page_name(release_version, check_draft_page)
        print("Main_page_name: ", main_page_name)
        main_page_exists = art.check_page_exists(
            confluence, space_key, main_page_name)
        print("main_page_exists: ", main_page_exists)
        if not main_page_exists:
            create_page_list.append(check_draft_page)

    for draft_page in create_page_list:
        status = {}
        draft_page_id = draft_page["content"]["id"]
        full_draft_page = art.get_full_page(confluence, draft_page)
        main_page_name = art.get_main_page_name(release_version, draft_page)
        ancestors_list = full_draft_page["ancestors"]
        parent_page = ancestors_list.pop()
        # parentPageId = parentPage["id"]
        # destination_storage_value = full_draft_page["body"]["storage"]["value"]
        # print("parentPageId: ", parentPageId)
        # print("main_page_name: ", main_page_name)
        # print("pageContent:", pageContent)
        destination_type = "parent_page"
        destination_page_id = parent_page["id"]
        destination_page_title = main_page_name[:]
        destination_page = (destination_type, destination_page_id, destination_page_title)

        status = art.copy_cloud_page(draft_page_id,
                                     confluence_parameters,
                                     destination_page)
        new_page_id = ""
        print ("Create page status: ", status)
        if "id" in status:
            print("Page created -------")
            # print("status: ", status)
            #status_dict = json.loads(status)
            new_page_id = status["id"][:]
            print("new_page_id: ", new_page_id)
            # restrictions = (accountId, "abiquo-team")
            # restns_response = art.hide_page(confluence_parameters, new_page_id, restrictions)
            # print("restns_response: ",restns_response)
        else:
            print("Page not created -------")
            print("status ", str(status))


        
        wiki_page_list.append("| " + new_page_id + " |"
                            " " + main_page_name + " |"
                            " [" + space_key + ":" + main_page_name + "] |\n")
    create_wiki_log(wiki_page_list)


# Calls the main() function
if __name__ == '__main__':
    main()
