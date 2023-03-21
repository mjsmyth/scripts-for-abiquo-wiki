'''# Python script: publishDraftPages to do Confluence release
# ---------------------------------------
# Script designed to publish draft pages for new version
# Gets pages with vXXX and updates pages without it
# E.g. Get "Azure blah v610" and update "Azure blah" 
#
# Publish draft pages
# ------------------
# 1. Get the vXXX draft pages and for each
# 2. Strip version from name
# 3. Check if the original page exists
# 4. Get ID of original page
# ?. Get parent ID???
# 5. Get content of draft page and compare --> check if works in cloud
# 7. Get history message --> Cannot use copy single page to update history
# 8. Update master page
# 9. Unhide master page --> now in separate script
#
'''
#!/usr/bin/python3
import os
# import json
from datetime import datetime
from atlassian import Confluence
import abqreltools as art


def create_wiki_log(wiki_page_list):
    '''Create a wiki markup format log'''
    todays_date = datetime.today().strftime('%Y-%m-%d')
    output_file = "outputPublishDraftPages." + todays_date + ".txt"
    output_dir = "./output_files"
    output_list = []
    output_list.append("|| Page ID || Name || Link ||\n")
    output_list.extend(wiki_page_list)
    wiki_file = open(os.path.join(output_dir,
                                 output_file), "w+")
    for line in output_list:
        wiki_file.write(line)
    wiki_file.close()


def main():
    # Get user credentials and space
    site_url = input("Confluence Cloud site URL, with protocol,"
                     + " and wiki, and exclude final slash, "
                     + "e.g. https://abiquo.atlassian.net/wiki: ")
    cloud_username = input("Cloud username: ")
    pwd = input("Cloud token string: ")
    accountId = input("Cloud user accountId: ")
    space_key = input("Space key: ")
    confluence_parameters = (site_url, cloud_username, pwd)
    release_version = input("Release version, e.g. v463: ")
    print_version = input("Release print version, e.g. 4.6.3: ")

    # Log in to Confluence
    confluence = Confluence(
        url=site_url,
        username=cloud_username,
        password=pwd,
        cloud=True)

    draft_page_list = art.get_draft_pages(
        space_key, release_version, confluence_parameters)
#    draftPageOnlyList = []
    wiki_page_list = []

    for page in draft_page_list:
        main_page_id = ""
        draft_page_id = page["id"][:]
        print("Version Page ID: ", draft_page_id)
        main_page_name = art.get_main_page_name(release_version, page)

        print("Original Page Name: ", main_page_name)
        full_draft_page = art.get_full_page(confluence, page)

        ancestors_list = full_draft_page["ancestors"]
        parent_page = ancestors_list.pop()
        parent_page_id = parent_page["id"]

        draft_page_content = full_draft_page["body"]["storage"]["value"]
        print("parentPageId: ", parent_page_id)
        print("main_page_name: ", main_page_name)
        # print("pageContent: ", draft_page_content)
        # print("full_draft_page: ", full_draft_page)
        # exit()
        main_page_id = ""
        main_page_exists = art.check_page_exists(
            confluence, space_key, main_page_name)
        print("main_page_exists response: ",main_page_exists)
        main_page_updated = False

        # version_comment = print_version + " - release "

        status = {}
        if main_page_exists:
            confluence_parameters = (site_url, cloud_username, pwd)
            originalfull_draft_page = confluence.get_page_by_title(
                space_key, main_page_name)
            main_page_id = originalfull_draft_page["id"][:]
        # Compare content and check is already updated or not
            main_page_updated = confluence.is_page_content_is_already_updated(
                main_page_id, draft_page_content)
            print("Check if page was already updated: ", main_page_updated)
            # Publish release by updating master pages from draft pages
            # - new_page_id = master page id
            # - destination_type = existing_page
            # - parentPageId = nul
           
            if not main_page_updated:
                # check if main page is locked

                # unlock main page
                restns_response = art.unlock_page(confluence_parameters, main_page_id,)
                print("restns_response: ",restns_response)
                print("Updating main page!")
                destination_type = "existing_page"
                destination_page_id = main_page_id[:]
                destination_page_title = main_page_name[:]
                destination_page = (destination_type, destination_page_id, destination_page_title)
                # update master page
                status = art.copy_cloud_page(draft_page_id, confluence_parameters, destination_page)
                # else:
                #    print("Page already updated: ", destination_page_title)


        else:
            # create master page

            # Create master pages with same parent as draft pages
            # - parentPageId = draft page parent
            # - master page name = draft page name - release version
            # - destination_type = parent_page

            # destination_storage_value = full_draft_page["body"]["storage"]["value"]
            print("Creating master page")
            destination_type = "parent_page"
            destination_page_id = parent_page["id"]
            destination_page_title = main_page_name[:]
            destination_page = (destination_type, destination_page_id, destination_page_title)
            status = art.copy_cloud_page(draft_page_id,
                                        confluence_parameters,
                                        destination_page)
            # Update page or create page if it does not exist
            # status = confluence.update_or_create(
            #     parentPageId, main_page_name,
            #     pageContent, representation='storage',
            #     version_comment=versionComment)

            # if status["id"]:
            #     main_page_id = status["id"][:]
            # else:
            #     print("status", status)

            # set the page to unhide and print name to be the original page


        # norestrictions = [{"operation": "update", "restrictions":
        #                    {"user": [],
        #                     "group": []}},
        #                   {"operation": "read", "restrictions":
        #                    {"user": [],
        #                     "group": []}}]

        # restns_response = art.upd_page_restns(confluence_parameters, space_key,
        #                                        main_page_id, norestrictions)
        # if str(restns_response) != "<response [200]>":
        #     print("restns_response: ", restns_response)
        new_page_id = ""
        print ("Update or create page status: ", status)
        if "id" in status:
            print("Page created")
            # print("status: ", status)
            # status_dict = json.loads(status)
            new_page_id = status["id"][:]
            print("new_page_id: ", new_page_id)
        else:
            print("Page not created")
            print("status ", str(status))

        wiki_page_list.append("| " + main_page_id + " |"
                            " " + main_page_name + " |"
                            " [" + space_key + ":" + main_page_name + "] |\n")
    create_wiki_log(wiki_page_list)


# Calls the main() function
if __name__ == '__main__':
    main()
