'''# Python script: checkIfUpdated
# --------------------------------------
# Script to check if main pages have not been updated
#
# Check if updated
# ------------------
# 1. Get the vXXX draft pages
# 2. Strip version from name
# 3. Check if the main page exists
# 4. Get ID of main page
# ?. Get parent ID???
# 5. Get content of draft page and compare with main'''

#!/usr/bin/python3

import os
from datetime import datetime
from atlassian import Confluence
import abqreltools as art


def create_wiki_log(wiki_page_list):
    '''Create some kind of log'''
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
    '''Get draft and main pages and output pages that are not updated'''
    # Get user credentials and space
    site_url = input("Confluence Cloud site URL, with protocol,"
                     + " and wiki, and exclude final slash, "
                     + "e.g. https://abiquo.atlassian.net/wiki: ")
    cloud_username = input("Cloud username: ")
    pwd = input("Cloud token string: ")
    space_key = input("Space key: ")

    release_version = input("Release version, e.g. v463: ")
    # Log in to Confluence
    confluence = Confluence(
        url=site_url,
        username=cloud_username,
        password=pwd,
        cloud=True)

    draft_page_list = art.get_draft_pages(
        space_key, release_version, confluence)
#    draftPageOnlyList = []
    wiki_page_list = []

    for page in draft_page_list:
        main_page_id = ""
        draft_page_id = page["content"]["id"][:]
        print("Version Page ID: ", draft_page_id)
        main_page_name = art.get_main_page_name(release_version, page)

        print("Original Page Name: ", main_page_name)
        full_draft_page = art.get_full_page(confluence, page)

        ancestorsList = full_draft_page["ancestors"]
        parentPage = ancestorsList.pop()

        pageContent = full_draft_page["body"]["storage"]["value"]
        print("main_page_name: ", main_page_name)
        #print("pageContent: ", pageContent)
        #print("full_draft_page: ", full_draft_page)
        # exit()
        main_page_id = ""
        main_page_exists = art.check_page_exists(
            confluence, space_key, main_page_name)
        print("main_page_exists response: ",main_page_exists)
        pageUpdated = False

    
        if main_page_exists:
            originalfull_draft_page = confluence.get_page_by_title(
                space_key, main_page_name)
            main_page_id = originalfull_draft_page["id"][:]

            pageUpdated = confluence.is_page_content_is_already_updated(
                main_page_id, pageContent)
            print("pageUpdated response: ",pageUpdated)




#        wiki_page_list.append("| " + main_page_id + " |"
#                            " " + main_page_name + " |"
#                            " [" + space_key + ":" + main_page_name + "] |\n")
#    create_wiki_log(wiki_page_list)


# Calls the main() function
if __name__ == '__main__':
    main()
