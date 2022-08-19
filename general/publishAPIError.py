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
inputSubdir = "output_files"
todaysDate = datetime.today().strftime('%Y-%m-%d')
# todaysDate = "2021-11-03"
filePrefixesPages = \
    [("wiki_api_error_admin_guide_", "API Error Code List")]
    # [("wiki_api_error_user_guide_", "User interface messages"),
    #  ("wiki_api_error_admin_guide_", "API Error Code List")]
# outputPropertyFile = 'wiki_properties_'
# wikiPropertiesFile = outputPropertyFile + "format_" + todaysDate + ".txt"
#    inputDirPropertyFile = inputDir + propertyFile


def main():
    # Get user credentials and space
    site_URL = input("Confluence Cloud site URL, with protocol,"
                     + " and wiki, and exclude final slash, "
                     + "e.g. https://abiquo.atlassian.net/wiki: ")
    cloud_username = input("Cloud username: ")
    pwd = input("Cloud token string: ")
    spacekey = input("Space key: ")

    release_version = input("Release version, e.g. v463: ")
    print_version = input("Release print version, e.g. 4.6.3: ")
    # updatePageTitle = "Abiquo configuration properties"
    wikiFormat = True
    tableReplaceString = r'<table(.*?)</table>'
    for filePrefix, Page in filePrefixesPages:
        wikiInputFile = filePrefix + todaysDate + ".txt"
        inputFile = inputSubdir + "/" + wikiInputFile
        wikiContent = ""
        with open(inputFile, 'r') as f:
            wikiContent = f.read()

        status = adt.updateWiki(Page, wikiContent, wikiFormat,
                                site_URL, cloud_username, pwd, spacekey,
                                tableReplaceString,
                                release_version, print_version)
        if status is True:
            print("Page ", Page,
                  " for ", release_version, " draft was updated sucessfully!")
        else:
            print("Page ", Page,
                  " for ", release_version,
                  " draft was not updated successfully!")


# Calls the main() function
if __name__ == '__main__':
    main()
