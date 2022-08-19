#!/usr/bin/python2 -tt
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
# TODO: also need to compare with previous version's table and mark changed lines and print a diff file
# and/or diff markers
#
import sys
import getopt
import re
import os
import requests
import copy
import json
from operator import itemgetter, attrgetter, methodcaller


class ApiErrorLine:
    def __init__(self,a_internal_message_id,a_message,a_label):
        self.label=a_label
        self.internal_message_id=a_internal_message_id
        self.message=a_message

    def string_admin(self):
        wiki_label = self.label
        wiki_internal_message_id = self.internal_message_id.strip("\"")
        wiki_message = dowikimarkup(self.message)        
        return '| %s | %s | %s |\n' % (wiki_internal_message_id, wiki_message, wiki_label)

    def string_user(self):
        wiki_internal_message_id = self.internal_message_id.strip("\"")
    #   wiki_message = self.message.strip("\"")
    #   wiki_message = re.sub("\|","\\\|",wiki_message)
    #   wiki_message = re.sub("-","\\\-",wiki_message)
        wiki_message = dowikimarkup(self.message)        
    #   print("| ",wiki.internal_message_id," | ",wiki.message," |")
        return '| %s | %s |\n' % (wiki_internal_message_id, wiki_message)

def main():
    input_subdir = "input_files"
    output_subdir = "output_files"
    todays_date = "2022-08-17"
    api_error_input_file = "apierrors_wiki_" + todays_date + ".txt"
    FS = "|"
    error_lines = {}
    error_sorted = {}
    section_header = ""

    api_error_file_admin = "wiki_api_error_admin_guide_" + todays_date + ".txt"
    api_error_file_user = "wiki_api_error_user_guide_" + todays_date + ".txt"

    admin_header = "|| Internal Message ID {color:#efefef}__________________{color}|| Message {color:#efefef}____________________________________________________________{color} ||  Identifier ||\n"; 
    user_header = "|| Internal Message ID {color:#efefef}__________________{color}|| Message {color:#efefef}____________________________________________________________{color} ||\n"; 

    sections_json = "apierror_sections.json"        
    api_error_sections_data = open(sections_json, "r")
    section_data = json.load(api_error_sections_data)
    api_error_sections_data.close()
    section_keys = sorted(section_data.keys())

    apie_error_formats = [ae.strip() for ae in open(os.path.join(input_subdir,api_error_input_file))]
    count_records = 0
    count_matches = 0

    for apierr in apie_error_formats:
#       count_records = count_records + 1   
        # apierr_replaced = apierr.replace("{","(")
        # apierr_replaced = apierr_replaced.replace("}",")")
        # apierr_replaced = apierr_replaced.replace("[","(")        
        # apierr_replaced = apierr_replaced.replace("]",")")
#       if re.match("=|",apierr_replaced):
        

        apierr_line = re.split('(?<!=)\|',apierr)

#       print "apierr_line[1]" + apierr_line[1]
#       print "apierr_line[2]" + apierr_line[2]
#       print "apierr_line[3]" + apierr_line[3]
        
        ae_id = apierr_line[1].strip()
        ae_msg = apierr_line[2].strip()
        ae_lab = apierr_line[3].strip()

        aeline = ApiErrorLine(ae_id,ae_msg,ae_lab)
        for skey in section_keys:
            if re.match(section_data[skey],ae_id):
                error_lines.setdefault(skey, []).append(aeline)
#               print "section_data[skey]: " + section_data[skey] + " skey: " + skey + " ae_id: " + ae_id

    error_msg_id = ""

    error_key_list = list(error_lines.keys()) 
#   print error_key_list
#   Fiddle with the list to put the status code at the top of the list  
    if "Status codes" in error_key_list:
        error_key_list.remove("Status codes")
    error_key_list = sorted(error_key_list)
    error_key_list.insert(0,"Status codes") 

#   print error_key_list        

#   for x in error_key_list:
        # if re.match(x, "Status code"):
        #   print "i found it!"
        #   break
        # else:
        #   x = None
##  new_error_lines = {}

    outfile_admin = open(os.path.join(output_subdir,api_error_file_admin), 'w')
    outfile_user = open(os.path.join(output_subdir,api_error_file_user), 'w')

    outfile_admin.write (admin_header)
    outfile_user.write (user_header)

    for ee in error_key_list:
#       print "ss: " + ss
        # ab = re.sub("\D","",el)
        # print ab
#       for hh in error_lines[ee]:
#           hi = re.sub("\D(\d{0-3})$","\\1",hh.internal_message_id)
#           print "hi: " + hi
#           new_key = padkey(hh)
#           print new_key
#           new_error_lines.setdefault(ee, []).append(ApiErrorLine(padkey(gg),gg.message,gg.label))

        
        ss_interest = sorted(error_lines[ee], key=lambda XX: padkey(XX.internal_message_id))
#       ss_interest = sorted(error_lines[ss], key=sort_api_errors(error_lines[ss].internal_message_id))
        admin_header_line =  "|| h6. " + ee + " ||  ||  ||\n"
        outfile_admin.write(admin_header_line)
        user_header_line = "|| h6. " + ee + " ||  ||\n"
        outfile_user.write(user_header_line)
        for ii in ss_interest:
            outfile_admin.write(ii.string_admin())
            outfile_user.write(ii.string_user())
#           print ael.string_admin()
#           print ael.string_user()
#   sorted(sk,key=lambda str: re.sub("\D","",str))

#       ae_admin = aeline.string_admin()
#       ae_user = aeline.string_user()

    outfile_admin.close()
    outfile_user.close()



def dowikimarkup(my_wiki_message):
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
    idbreakup = re.search("(^.+?)((\d*)$)",mg_id)
    print "my id: " + idbreakup.group(1)
    print "my no: " + idbreakup.group(2)
    mynumber = idbreakup.group(2)

    if re.match("\d",mynumber):
        realnumber = int(mynumber)
#       print "real number: " + mynumber
        hello = "{0:05d}".format(realnumber)
#       print "hello: " + hello
        finalmg = re.sub("\d+$",hello,mg_id)
#       print "finalmg: " + finalmg
    else:   
        finalmg = mg_id
#       print "no match: " + finalmg    
    return finalmg


# Calls the main() function
if __name__ == '__main__':
    main()
