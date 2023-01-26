'''Author: Andrew Martin
Creation date: 24/01/2023

Function to utilise the mpl2nc package in the command line to turn the .mpl files into .nc files.
'''

import os
import warnings
import mpl2nc

def extract_mpl2nc(dir_target):
    '''Function to extract .mpl files in dir_target/mplraw to .nc files in dir_target/mpl using the mpl2nc package.
    
    In its initial implementation, I'm not going to have any calibration for afterpulse, deadtime correction or overlap correction. Given I can access the functions directly, I shouldn't have to load in binary afterpulse files, I could just pass the data loaded from .nc files created using mpl2nc anyway...

    INPUTS:
        dir_target : string
            directory in which the data analysis is being performed. Should contain a subdirectory dir_target/mplraw containing .mpl files.
    '''

    dir_bin = os.path.join(dir_target, 'mplraw')
    dir_nc = os.path.join(dir_target, 'mpl')

    # create the dir_target/mpl folder if it doesn't already exist
    if not os.path.isdir(dir_nc):
        warnings.warn(f'extract_mpl2nc: /mpl does not exist at {dir_target=}. Creating subdirectory now.')
        os.mkdir(dir_nc)

    files_mpl = os.listdir(dir_bin)
    files_mpl = [f for f in files_mpl if f[-4:] == '.mpl']

    files_unzip = os.listdir(dir_nc)

    for fname in files_mpl:
        if (fname[:-3] + '.nc') in files_unzip:
            # if the file has already been extracted, pass
            print(f'{fname} : already converted')
            continue
        
        # taken from mpl2nc.main path for individual files
        mpl = mpl2nc.read_mpl( os.path.join(dir_bin,fname) )
        mpl = mpl2nc.process_nrb(mpl)
        mpl2nc.write(mpl, os.path.join(dir_nc, (fname[:-3] + '.nc')) )
        print(f'{fname} : converted')

    return None


'''
# example code
target = '/home/users/eeasm/_scripts/ICESat2/src/mpl'
extract_mpl2nc(target)
'''