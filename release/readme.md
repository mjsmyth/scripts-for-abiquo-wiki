# Confluence release scripts

You can use these scripts to quickly perform a documentation release.

I don't think they work for the release notes pages, but it's better to do those by hand anyway. 
All scripts create a wiki markup table of wiki pages marking those to create/change/etc in the output_files folder.


## createOriginalPages.py

This script copies draft pages (vXXX) that don't have master pages to create new hidden master pages.
Remember that you should always make changes to the draft pages because the release script will overwrite the master pages.
Also, the page comments are not copied, so that will clean up any random developer comments (:smile). 
This script creates an output file listing all pages, so you can use this instead of testDocReleaseConfluence.py


## publishDraftPages.py

This script copies the draft pages (vXXX) over the top of master pages (new or original).
This script should also make any the new master pages readable.
Sometimes pages stay hidden - maybe if there are no changes to the master page, the page permissions step is not reached.


## moveDraftPages.py

This script moves draft pages to put them all under another page
The new parent page is hard coded! 


## abqreltools.py

This is a module with the common actions in it.