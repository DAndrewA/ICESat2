'''Author: Andrew Martin
Creation date: 17/1/23

Function to extract the MMCR MOM .nc.zip files within a /mmcrzip folder to .nc format in the root / folder provided.
'''

import os
import zipfile

def extract_from_mmcrzip(dir_target):
    '''Function to extract MMCR .n.zip files in dir_target/mmcrzip into dir_target

    INPUTS:
        dir_target : string
            Path to the directory the files will be extracted to, which also contains a /mmcrzip subdirectory
    
    OUTPUTS:
        None : None type
            placeholder return
    '''
    # get all the .nc.zip files in dir_target/mmcrzip
    files_zip = os.listdir(os.path.join(dir_target, 'mmcrzip'))
    files_zip = [f for f in files_zip if f[-7:] == '.nc.zip']

    files_unzip = os.listdir(dir_target)

    for fname in files_zip:
        # for each .nc.zip file, check it hasn't already been unzipped to dir_target
        if fname[:-4] in files_unzip:
            pass
        # otherwise, unzip the file
        with zipfile.ZipFile(os.path.join(dir_target,'mmcrzip',fname), 'r') as zip_ref:
            zip_ref.extractall(dir_target)

    return None

'''#example code'''
target = '/home/users/eeasm/_scripts/ICESat2/src/mmcr'
extract_from_mmcrzip(target)