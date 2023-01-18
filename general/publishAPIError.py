# #!/usr/bin/python3
# Python script: general/publishScriptPages.py
# ---------------------------------------
# Script to publish script pages for new version
# Gets pages with vXXX and updates them
#
# Publish script pages
# ------------------
# 1. Get the vXXX draft pages and for each script
# 2. Get content of draft page
# 3. Get script output
# 4. Update draft page
#

from datetime import datetime
import abqdoctools as adt

wikiPageList = []
INPUT_SUBDIR = "output_files"
todaysDate = datetime.today().strftime('%Y-%m-%d')
# todaysDate = "2021-11-03"
file_prefixes_pages = \
    [("wiki_api_error_user_guide_", "User interface messages"),
     ("wiki_api_error_admin_guide_", "API Error Code List")]
    #  ("wiki_api_error_admin_guide_", "API Error Code List")]
# outputPropertyFile = 'wiki_properties_'
# wikiPropertiesFile = outputPropertyFile + "format_" + todaysDate + ".txt"
#    inputDirPropertyFile = inputDir + propertyFile


def main():
    '''publish api error to cloud wiki'''
    # Get user credentials and space
    site_url = input("Confluence Cloud site URL, with protocol,"
                     + " and wiki, and exclude final slash, "
                     + "e.g. https://abiquo.atlassian.net/wiki: ")
    cloud_username = input("Cloud username: ")
    pwd = input("Cloud token string: ")
    spacekey = input("Space key: ")

    release_version = input("Release version, e.g. v463: ")
    print_version = input("Release print version, e.g. 4.6.3: ")
    # updatePageTitle = "Abiquo configuration properties"
    wiki_format = True
    table_replace_string = r'<table(.*?)</table>'
    for file_prefix, page in file_prefixes_pages:
        wiki_input_file = file_prefix + todaysDate + ".txt"
        input_file = INPUT_SUBDIR + "/" + wiki_input_file
        wiki_content = ""
        with open(input_file, 'r') as f:
            wiki_content = f.read()

        status = adt.updateWiki(page, wiki_content, wiki_format,
                                site_url, cloud_username, pwd, spacekey,
                                table_replace_string,
                                release_version, print_version)
        if status is True:
            print("Page ", page,
                  " for ", release_version, " draft was updated sucessfully!")
        else:
            print("Page ", page,
                  " for ", release_version,
                  " draft was not updated successfully!")


# Calls the main() function
if __name__ == '__main__':
    main()
