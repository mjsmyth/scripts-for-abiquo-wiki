#!/bin/zsh
# Developed very quickly in March 2020 because Shutter was not supported in Ubuntu at the time
#directory_name=$1
directory_date=$(date "+%Y_%m_%d")

#file_list=`ls -1d /Users/maryjane/Pictures/screenshots/v50 | grep "v50_" | grep "png" | grep -v "d_v50" | awk '{print $0}'`
directory="/Users/maryjane/Pictures/screenshots/v50_${directory_date}/"
output_directory="${directory}output_files/"

file_list=`ls -1 ${directory} | grep "v50_" | grep "png" | awk '{print $0}'`

filearray=($file_list)

if [[ `echo ${filearray[*]}` == "" ]]; then
         print "Files not found"
else
 for ifile in `echo ${filearray[*]}`; do

        width=$(magick identify "${directory}$ifile" | awk -F "[ ]\|x" '{print $3}')
        height=$(magick identify "${directory}$ifile" | awk -F "[ ]\|x" '{print $4}')

        print "$ifile: ${width}x${height}"

        ifileout=$(print "${ifile}")   
#        print "$ifileout"

        convert "${directory}${ifile}" \
         -bordercolor gray75 -compose copy -border 3 \
         -bordercolor gray58 -compose copy -border 3 \
         -fuzz 50% -trim +repage "${output_directory}$ifileout" 

        new_width=$(magick identify "${output_directory}$ifileout" | awk -F "[ ]\|x" '{print $3}')
        new_height=$(magick identify "${output_directory}$ifileout" | awk -F "[ ]\|x" '{print $4}')

        change_width=$(( width - new_width ))
        print "changewidth: $change_width"

        # For files with no dialog
        if [[ change_width -ge 20 ]]; then
            cp ${directory}$ifile ${output_directory}$ifileout
        else
            # for weird files that it doesn't work for (vdc and vapp)
            if [[ change_width -le 1 ]]; then
                convert "$directory${ifile}" -crop "${new_width}x${new_height}+0+0" +repage \
                -bordercolor gray75 -compose copy -border 3 \
                -bordercolor gray58 -compose copy -border 3 \
                -fuzz 50% -trim +repage \
                -fuzz 50% -trim +repage "$output_directory${ifileout}" 
            else    
                convert "${directory}${ifile}" \
                -bordercolor gray75 -compose copy -border 3 \
                -bordercolor gray58 -compose copy -border 3 \
                -fuzz 50% -trim +repage \
                -fuzz 50% -trim +repage "${output_directory}${ifileout}" 
            fi
        fi    

        print "Processed file ${ifileout}" 
 done
fi