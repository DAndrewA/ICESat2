# ICESat2

This library of code will be the main location that I will try to write all my scripts to. The code will focus on obtaining and manipulating ICESat2 data, and any data I want to compare it to (i.e. Summit data).

## Packages

+ helper: This module will contain helpful scripts that can be applied generally to multiple different scenarios (i.e. for copying data files, converting files into specific formats, etc).

## Modules

+ describe_h5.py: a script to output the structure of a .h5 file.

+ plot_profile_variables: notebook for plotting variables within an ICESat2 file across the three beam profiles. Plotted variables can be customised on the fly.

+ download_summit.ipynb: notebook to copy Summit data files from the ncas gws2 to my space on the ncas gws1 based on the date and time of an ATL09 file.

