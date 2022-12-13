'''Andrew Martin; Created: 13/12/22

Functions to transport data files from one directory to another on JASMIN.

I'll use these to move files from the ncas_radar_gws_v2/data/ICECAPSarchive to my space on the v1 gws. Will need to check that the files haven't already been moved, and if not, then copy the files over so that I can use them in any analysis I want to do.

I'll also include code that can handle datetime selections of the data. That way, I can get the files that (for example) match up with ICESat2 passes.
'''

import os
import warnings
import datetime
import shutil
import glob




def find_files_in_date_range(initial, daterange, filename_format, depth='d'):
    '''Within a directory, find files corresponding to a given format that fall within a given datetime range.
    For example, if we want to look at the ATL09 file on the 11/02/21 and go +- 24hrs, we need to be looking in the date range [10/02/21, 12/02/21]. This function will return all the valid files within that range.
    
    INPUTS:
        initial [string]: path to the directory the data files are in
        
        daterange [list of datetime objects]: ordered range of dates to find the data within.

        depth [string] in ['m','d','h']: at what level do the filenames have to be generated. 'm': data files are in a monthly format; 'd': data files are in a daily format; 'h': data files are in an hourly format.

        filename_format [string]: format that the data files use, that we can extract their dates from.
        e.g. 'ATL09_%Y%m%d*.h5'
        The file format will go down to the level of precision required and then all matching files can be found.

    OUTPUTS:
        filenames [tuple of strings]: list of filenames with data in the valid range.
    '''
    filenames = set()
    if depth == 'h':
        dt = datetime.timedelta(hours=1)
    elif depth == 'd':
        dt = datetime.timedelta(days=1)
    elif depth == 'm':
        dt = datetime.timedelta(days=10) # 25 days picked because months have differing lengths
    else:
        warnings.warn(f'depth {depth} not in [\'h\', \'d\', \'m\'].')
        return filenames

    cwd = os.getcwd()
    os.chdir(initial)
    try:

        d = daterange[0] # start with the initial date
        while d < daterange[1] + dt/2:
            check_filename = datetime.datetime.strftime(d,filename_format)
            found = glob.glob(check_filename)
            #print(f'Files found in {os.getcwd()}/{check_filename}: {found}')
            found = set(found)
            filenames.update(found)
            d = d + dt
    finally:
        os.chdir(cwd)    
    return tuple(filenames)



def _check_file_exists(dir_path, filename):
    '''Function that checks if a named file exists.
    
    INPUTS:
        dir_path [string]: directory the file will be stored in
        filename [string]: name of the file for which we are checking the existence of.
        
    OUTPUTS:
        exists [boolean]: True if the file exists, flase if not
    '''
    path = os.path.join(dir_path,filename)
    exists = os.path.isfile(path),path
    return exists


def copy_file(initial,filename,endpoint):
    '''Copies a file from the initial folder to the endpoint folder.
    
    INPUTS:
        initial [string]: path to the folder containing the original file
        filename [string]: name of the file to be copied. It will retain its filename
        endpoint [string]: directory into which the file will be copied.
        
    OUTPUTS:
        success [boolean]: will output true if the file is succesfully moved. Otherwise, will return False and raise a warning.
    '''
    # start by checking the file exists in the first place...
    exists = _check_file_exists(initial,filename)
    if not exists:
        warnings.warn(f'File at {os.path.join(initial,filename)} does not exist.')
        return False
    # check the receiving directory exists
    if not os.path.isdir(endpoint):
        warnings.warn(f'Endpoint {endpoint} does not exist. Attempting to create endpoint.')
        try:
            os.mkdir(endpoint)
        except FileExistsError:
            warnings.warn(f'Endpoint {endpoint} does already exist. Something has gone wrong... Exiting.')
            return False
        except FileNotFoundError as err:
            warnings.warn(f'Folder in {endpoint} does not exist. Cannot create endpoint.')
            print(err)
            return False
    # the initial file and endpoint both exist.
    shutil.copy(os.path.join(initial,filename),os.path.join(endpoint,filename))
    return True