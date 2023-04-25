# MPL package

A package to contain the notebooks and scripts for obtaining, manipulating and plotting the MPL lidar data from Summit.

### Modules:
+ move_mplraw:
    Move raw .mpl.gz files from the ICECAPSarchive/mpl/raw directory to a target/mplraw_zip directory

+ extract_from_mplgz:
    Extracts .mpl.gz files in target/mplraw_zip into .mpl files in target/mplraw

+ extract_mpl2nc:
    Converts the .mpl files in target/mplraw to .nc files in target/mpl using the mpl2nc package.

+ get_mpl_from_archive:
    Combines move_mplraw(), extract_from_mplgz() and extract_mpl2nc() all into one convenience function. 


### Further work

### Known Issues