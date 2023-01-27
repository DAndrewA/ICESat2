'''Author: Andrew Martin
Creation date: 24/01/2023

Function to extract the .mpl.gz files from dir_target/mplraw_zip to dir_target/mplraw
'''

import gzip
import os
import shutil
import warnings

def extract_from_mplgz(dir_target, verbose=False):
    '''Function to extract the .mpl.gz files from dir_target/mplraw_zip into dir_target/mpl_raw
    
    INPUTS:
        dir_target : string
            Target directory that contains the /mplraw_zip folder containing .mpl.gz files.

        verbose : boolean
            if True, long formatted string is printed for each file. Otherwise, 1 is printed for extracting, 0 for already extracted.
    '''
    dir_zip = os.path.join(dir_target, 'mplraw_zip')
    dir_unzip = os.path.join(dir_target, 'mplraw')

    # create the dir_target/mplraw folder if it doesn't already exist
    if not os.path.isdir(dir_unzip):
        warnings.warn(f'extract_from_mplgz: /mplraw does not exist at {dir_target=}. Creating subdirectory now.')
        os.mkdir(dir_unzip)

    files_mpl = os.listdir(dir_zip)
    files_mpl = [f for f in files_mpl if f[-7:] == '.mpl.gz']

    files_unzip = os.listdir(dir_unzip)

    if verbose: print('extract_from_mplgz: ')
    else: print(f'{"extract_from_mplgz":>20}: ', end='')

    for fname in files_mpl:
        if fname[:-3] in files_unzip:
            # if the file has already been extracted, pass
            if verbose: print(f'{fname} : already extracted')
            else: print('0', end='')
            continue
        
        if verbose: print(f'{fname} : extracting')
        else: print('1', end='')
        
        # solution taken from https://stackoverflow.com/questions/31028815/how-to-unzip-gz-file-using-python
        # Matt & Erick 's solutions
        with gzip.open(os.path.join(dir_zip,fname), 'rb') as f_in:
            with open(os.path.join(dir_unzip, fname[:-3]), 'wb') as f_out:
                shutil.copyfileobj(f_in,f_out)

    if verbose: print('extract_from_mplgz complete.')
    else: print('')
    return None

'''
# example code
target = '/home/users/eeasm/_scripts/ICESat2/src/mpl'
extract_from_mplgz(target)
'''