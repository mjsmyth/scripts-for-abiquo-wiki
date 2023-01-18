#!/usr/bin/python -tt
#
# The input file to this program is created by running the main of APIError.java
# The main outputs a wiki text and a JSON labels file
#
# Save the wiki text in a separate file
# Manually edit the APIError file to join the PSW-1 message lines
#
# For user's guide (User+Interface+Messages) and developer's guide (API+Error+Code+List)
#
# replace {} with ""
# replace [] with ()
# read the sections file
# put the error messages into a dict in sections
# sort the sections based on the last part of the id (whatever it may be)
# print a header for each section
# TODO: also need to compare with previous version's table 
# and mark changed lines and print a diff file
# and/or diff markers
#

import json
import re
import os


class ApiErrorLine:
    '''API error line'''
    def __init__(self,a_internal_message_id,a_message,a_label):
        self.label=a_label
        self.internal_message_id=a_internal_message_id
        self.message=a_message

    def string_admin(self):
        '''Admin guide line'''
        wiki_label = self.label
        wiki_internal_message_id = self.internal_message_id.strip("\"")
        wiki_message = dowikimarkup(self.message)
        return '| %s | %s | %s |\n' % (wiki_internal_message_id, wiki_message, wiki_label)

    def string_user(self):
        '''User guide line'''
        wiki_internal_message_id = self.internal_message_id.strip("\"")
    #   wiki_message = self.message.strip("\"")
    #   wiki_message = re.sub("\|","\\\|",wiki_message)
    #   wiki_message = re.sub("-","\\\-",wiki_message)
        wiki_message = dowikimarkup(self.message)
    #   print("| ",wiki.internal_message_id," | ",wiki.message," |")
        return '| %s | %s |\n' % (wiki_internal_message_id, wiki_message)


def main():
    '''Process API errors from API'''
    input_subdir = "input_files"
    output_subdir = "output_files"
    todays_date = "2022-12-30"
    api_error_input_file = "apierrors_wiki_" + todays_date + ".txt"
    error_lines = {}

    api_error_file_admin = "wiki_api_error_admin_guide_" + todays_date + ".txt"
    api_error_file_user = "wiki_api_error_user_guide_" + todays_date + ".txt"

    admin_header = "|| Internal Message ID {color:#efefef}__________________{color}" \
        + "|| Message {color:#efefef}____________________________________________________________" \
        + "{color} ||  Identifier ||\n"

    user_header = "|| Internal Message ID {color:#efefef}__________________{color}" \
        + "|| Message {color:#efefef}____________________________________________________________" \
        + "{color} ||\n"

    sections_json = "apierror_sections.json"
    api_error_sections_data = open(sections_json, "r")
    section_data = json.load(api_error_sections_data)
    api_error_sections_data.close()
    section_keys = sorted(section_data.keys())

    apie_error_formats = [ae.strip() for ae in open(os.path.join(input_subdir,api_error_input_file))]

    for apierr in apie_error_formats:

        apierr_line = re.split('(?<!=)\|',apierr)

        ae_id = apierr_line[1].strip()
        ae_msg = apierr_line[2].strip()
        ae_lab = apierr_line[3].strip()

        aeline = ApiErrorLine(ae_id,ae_msg,ae_lab)
        for skey in section_keys:
            if re.match(section_data[skey],ae_id):
                error_lines.setdefault(skey, []).append(aeline)
                # print "section_data[skey]: " + section_data[skey] +
                #    skey: " + skey + " ae_id: " + ae_id


    error_key_list = list(error_lines.keys())
    #   print error_key_list
    #   Fiddle with the list to put the status code at the top of the list
    if "Status codes" in error_key_list:
        error_key_list.remove("Status codes")
    error_key_list = sorted(error_key_list)
    error_key_list.insert(0,"Status codes")


    outfile_admin = open(os.path.join(output_subdir,api_error_file_admin), 'w')
    outfile_user = open(os.path.join(output_subdir,api_error_file_user), 'w')

    outfile_admin.write (admin_header)
    outfile_user.write (user_header)

    for error_item in error_key_list:
        ss_interest = sorted(error_lines[error_item], key = lambda XX: padkey(XX.internal_message_id))
        admin_header_line =  "|| h6. " + error_item + " ||  ||  ||\n"
        outfile_admin.write(admin_header_line)
        user_header_line = "|| h6. " + error_item + " ||  ||\n"
        outfile_user.write(user_header_line)
        for interest in ss_interest:
            outfile_admin.write(interest.string_admin())
            outfile_user.write(interest.string_user())

    outfile_admin.close()
    outfile_user.close()


def dowikimarkup(my_wiki_message):
    '''Create wiki markup'''
    a_wiki_message = my_wiki_message.replace(r"\\",r"\\\\")
    a_wiki_message = re.sub("\|","\\\|",a_wiki_message)
    a_wiki_message = re.sub("-","\\\-",a_wiki_message)
#   a_wiki_message = a_wiki_message.strip("\"")
#   a_wiki_message = re.sub(r"\\\\\|",r"\\\|",a_wiki_message)
    a_wiki_message = a_wiki_message.replace("{",r"&#123;")
    a_wiki_message = a_wiki_message.replace("}",r"&#125;")
    a_wiki_message = a_wiki_message.replace("[",r"&#91;")
    a_wiki_message = a_wiki_message.replace("]",r"&#93;")
    return a_wiki_message


def padkey(mg_id):
    '''Pad the keys'''
    idbreakup = re.search("(^.+?)((\d*)$)",mg_id)
    print("My ID: ", idbreakup.group(1))
    print("My No: ", idbreakup.group(2))
    mynumber = idbreakup.group(2)

    if re.match("\d",mynumber):
        realnumber = int(mynumber)
        hello = "{0:05d}".format(realnumber)
        finalmg = re.sub("\d+$",hello,mg_id)
    else:
        finalmg = mg_id
    return finalmg


# Calls the main() function
if __name__ == '__main__':
    main()
