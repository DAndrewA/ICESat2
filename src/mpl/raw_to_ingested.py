'''Author: Andrew Martin
Creation date: 9/2/23

Scripts to deal with converting the raw mpl data into the Summit ingested format.
'''

import numpy as np
import datetime
import xarray as xr
import netCDF4
import os
import glob

# import local packages

def raw_to_ingested(dir_target,date,limit_height=True, c=3e8):
    '''Convert hourly mpl files to the Summit ingested format.

    The function will take hourly .nc files (created by mpl2nc) and concatenate them to produce a file matching the Summit ingested mpl format.
    
    The raw mpl data contains more height bins than the ingested format does. As such, I'll give the option to maintain that information or drop it to match the original format exactly.

    INPUTS:
        dir_target : string
            directory containing the .nc files produced by mpl2nc. This is also the directory that the ingested file will be saved into.

        date : datetime.date, datetime.datetime
            datetime object for the day the data should belong too. This allows for multiple days of data to be stored in dir_target

        limit_height : boolean : default=True
            If True, limits the output to the first 1200 height bins. 

        c : float : default=3e8 ; [m/s]
            The speed of light, in m/s, used to calculate the height bins. Summit uses 3e8, but mpl2nc uses the SI defined c=299792458m/s
    '''

    # STEPS TO IMPLEMENT
    # 1) Determine files in dir_target, that match date. Ensure there are enough for 24 hours, get sorted list
    # 2) Load in data as multifile dataset (xarray); create new dataset to be saved
    # 3) For new dataset, create time and height dimensions; limit height data?
    # 4) Transfer relevant data from loaded to created dataset, with metadata
    # 5) Transfer attributes to new dataset, with metadata
    # 6) save the file

    # get files in dir_target that match the date given
    filename_fmt = f'{date.year:04}{date.month:02}{date.day:02}*.nc'
    mpl_filenames = sorted(glob.glob(filename_fmt,root_dir=dir_target))
    # if not 24 files are found, then the function will break and return None
    if len(mpl_filenames) != 24:
        print(f'raw_to_ingested: For full day, 24 filoes are expected. {len(mpl_filenames)} files matching date {date} in {dir_target=} found.')
        return False

    # load in the data to an xarray dataset
    data_loaded = xr.open_mfdataset(str(os.path.join(dir_target, filename_fmt))) # open_mfdataset allows glob strings
    print(data_loaded)










# test function
date = datetime.date(2021,2,11)
raw_to_ingested('/home/users/eeasm/_scripts/ICESat2/src/mpl/mpl',date)
