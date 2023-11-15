# Introduction

You can use the Abiquo wiki scripts to update the documentation of messages, tracers, privileges and properties on Abiquo wiki pages.

The best time to run these scripts is just before the code freeze for a release.

I wrote the original scripts in AWK to output wiki markup, then moved to Python and Confluence storage format, and Markdown.
The scripts are purely functional and very ugly.

## Add output from scripts to the wiki

Some of the scripts automatically update the wiki.

To add wiki markup output from scripts to the wiki:
1. Convert to Markdown 
2. Open the page with the Alt-text editor, by clicking the button near the Edit button
3. Paste the Markdown


## UI labels file

This is a file not a script! Paste the UI labels file in the wiki for each each version.

1. Copy the "UI labels" page
2. Rename it to "UI Labels vXXX" (where XXX is the latest version number) and save
3. Pull the latest version of platform master from Github (e.g. use the alias tolete master)
4. Find the UI labels file with the folder path and file name as follows:
```platform/ui/app/lang/lang_en_US_labels.json```
5. Open the labels file in a text editor and copy the text
6. In the "UI labels vXXX" page, delete the current text
7. Paste the new labels and Save

Use the version compare feature to check UI Changes in between versions.

## API Errors

To add the API errors to the base UI file and the wiki, start with the ``APIError.java`` file.
This info is now published en every build, in the same folder as the API docs.

```platform/api/target/site/apidocs/```

* apierrors_wiki
* apierrors_ui
 

### API errors for UI messages

For the "apierrors_ui" file.
Add this JSON to the wiki so customers can customize the API Error messages that their users will see in the UI.
Also check for new categories to add to the categories input file for the API errors wiki script.

```{
    "server.error.400-BAD-REQUEST" : "Request not valid",
    "server.error.401-UNAUTHORIZED" : "This request requires user authentication",
    "server.error.403-FORBIDDEN" : "Access denied",
```

1. Copy the "UI error messages" page
2. Save it with the new version number, e.g. "UI Error Messages v550"
3. Edit the new page and delete the messages
4. Add the new messages and save the page
5. Click on the change note to compare the new page with the old page
6. Look for new error categories, which means new tags.
   For example, if there was a new message: CLOUDFAIL-01, its tag would be CLOUDFAIL.
7. Go to the abiquo-wiki-scripts/input_files folder and edit the file apierror_sections.json
8. Add the new section with a key (regular expression) and value (header). 
   The regular expression is so that the script can recognise this section (usually just "CLOUDFAIL-" or similar) 
   Don't forget to add a comma before the new section
9. Save the file 
 

### API errors for the wiki
The output for Wiki errors section of the APIError main is the APIErrors in wiki markup format.
You could put this straight in the wiki but it is just one table with about 1000 lines in it...

```
| 2FA-0 | Unexpected error generating the two factor verification code | TWO_FACTOR_UNABLE_TO_GENERATE_CODE |
| 2FA-1 | Two-factor authentication is already enabled for the current user | TWO_FACTOR_AUTH_ENABLED |
| 2FA-2 | The given two-factor authentication provider is not supported | TWO_FACTOR_UNSUPPORTED_PROVIDER |
| 400-BAD-REQUEST | Request not valid | STATUS_BAD_REQUEST |
| 401-UNAUTHORIZED | This request requires user authentication | STATUS_UNAUTHORIZED |
| 403-FORBIDDEN | Access denied | STATUS_FORBIDDEN |
```

For the input file:
1. Edit the message with the code PSW-1 that is multi-line and make it a single line
2. Add a space at the end of each line after the last pipe character "|" (to enable split on pipe + space because of extra pipes) 
3. Save with today's date at the end

The input files are:
* apierrors_wiki
* input_files/apierror_sections.json

The script is ``process_api_error_from_api.py``

1. Edit the script and change the todays_date variable to be the date on your input file.
2. Run the script with Python 2, ``python2 process_api_error_from_api.py``
3. From the output_files directory, open the output files in a text editor:
``output_files/wiki_api_error_admin_guide_2015-08-04.txt
output_files/wiki_api_error_user_guide_2015-08-04.txt``
4. Convert to Markdown and paste these files into wikimarkup boxes on copies of the wiki pages: 
   1. User guide: User interface messages
   2. Admin guide: API Error Code List

Note: you may need to remove some extraneous wiki markup, e.g. \{color} spans.


## Privileges

You can run a script to update the "Privileges" page in the wiki

It requires:

* platform (or at least UI files) on your local computer
* a fresh copy of Abiquo
* API access
* Cut and paste of UI privileges page text from Abiquo
Before you begin:
1. Check with the UI programmers to make sure that the UI is up to date and all new privileges are present.

Prepare the UI text:

1. In a fresh Abiquo, open the UI Users Roles page and don't select a role
2. Copy the Privileges text and paste it in a Google docs file
3. On each header section line, remove the "indent" by clicking the unordered list item button
4. Download as a plain text file. Name the text file with the following format:
``privileges/input_files/privilege_ui_order_2016-11-16.txt``
5. Replace the asterisk ``* `` with a space `` `` 
6. Check each privilege is its own line with a space at the start of the line
7. Check that there are section headers (Home, Infrastructure, etc).  
8. Compare this file with the file of the previous version, if there are no changes to privileges, you can stop here! 

Prepare to run the script 

1. Edit the script and set the input directory to read "lang_en_US_labels.json" from the platform files on your computer or a copy of this UI file. Hint: use the "t" shortcut in the UI repo to find these files on GitHub
2. There should be an extra text file in the input_files directory ``privileges/input_files/process_privileges_extratext.txt``
3. Check the auth for Abiquo
4. Enter the date for the input and output files in the script in the format ``td="2016-11-16"``


Run the script 

1. Use the command ``python privileges/api_process_abiquo_privileges_ui_order.py``
2. Edit the wiki page in a Source editor and remove the table. 
3. This script creates the whole "Section" for the wiki in storage format. Confluence Cloud probably doesn't support the Section so remove it.
4. Copy the text of the file output by the script and paste it between the last two paragraph symbols.
5. Check the changes between this and the last version of the page by clicking view changes. 
6. Check the order against the UI and the existing wiki (comparison).
7. On the "Changes to privileges" page, enter new, changed, deprecated and deleted privileges  
8. In the *Info* column of the table mark new privileges with a star (using the string (\*)) and changes with a warning (using the string (!))


## Events table

To create the table for the Events table page:
1. Update your copy of platform
2. Run the events table script with the command ``python3 process_events_table.py``

This script gets the generated events (from the last build) and the event privileges and creates a table in wiki markup.

You can find the table in the output_files folder and the filename is in the format 

```wiki_event_tracer_all_2020-06-03.txt```

It uses today's date from the system, but you could override this to use another date as required.

It creates or updates the Confluence draft page for the given version.


## Properties

There is a script to create the table for the Abiquo configuration properties page.

The Python 3 script file is at: ``scripts-for-abiquo-wiki/general/process_properties_table.py``

To run this properties script, you will need:

1. Abiquo python library installed with pip3
2. An Abiquo API endpoint
3. An access token (to get lists of plugins and devices) 
4. Updated platform repo
5. The ``abiquo.properties`` file is found in the ``abiquo/system-properties`` repo.
6. The mustache template file for Confluence storage format is at `wiki_properties_template.mustache`
7. The storage format text for the `abiquo.guest.password.length` property is at `process_properties_abiquoguestpasswordlength.txt` 
 
You should check each PR that commits to the `abiquo.properties` file.

Developers should follow the file format as described in the ``README.md`` of the ``system-properties`` repo.

Note that the script contains some manual additions to the list of plugins and deprecations. 

Run the script as follows:
``python process_properties_table.py``
The output file will be a wiki storage format file with a name in the format with today's date:
``wiki_properties_stformat_yyyy-mm-dd.txt``
For example:
``wiki_properties_stformat_2021-12-24.txt``
This script will overwrite previous files of the same day.

To manually add this file to the wiki:

1. Create a copy of the page for the new version (e.g. Abiquo Configuration Properties v620)
2. Remove the table
3. From the page menu, select Edit storage format
4. Paste the table

You can also add it with a table replace script.

Remember that you also need to update the following pages:

1. Changes to Abiquo configuration properties
2. Changes to Abiquo configuration properties list
3. You can probably compare the markup files between versions and build a mini table with the new lines to add to these pages. 



## Configuration view tables

You can run the config view script to create tables for the "Configuration View" page.

The script is called ``process_config_view_python3.py``

The script requires:

1. Access to the API of a fresh Abiquo install
2. The platform cloned on the local machine
3. The abiquo-api Python library installed with pip3
4. An extra text file: ``input_files/process_config_view_extra_text.txt``


To update the config view tables:

1. Edit the script and set the date, if you don't want today's date.
2. Run the script with the command ``python3.9 process_config_view_python3.py``
3. Edit the two files of wiki markup and convert to Markdown
   1. ``output_files/wiki_config_view_table_2021-11-18.txt``
   2. ``output_files/wiki_config_wiki_links_2021-11-18.txt``
4. Copy the following page to a vXXX version page:
   ``Configuration view``
5. Edit "Configuration view vXXX" with the Alt-text editor
6. Paste in the new tables



## Get wiki content
Use a modified version of Sarah Maddox's script in the Confluence cloud migration section.



## Abiquo documentation tools
This is a utility file called abqdoctools.py that contains common functions for the documentation scripts.
