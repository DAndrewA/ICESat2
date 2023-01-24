'''Author: Andrew Martin
Creation date: 24/01/2023

Function to move raw mpl.gz files from the ICECAPSarchive to a desired target location.
'''

import os
import shutil
import datetime as dt
import warnings

def move_mplraw(dir_target, dir_mpl='/gws/nopw/j04/ncas_radar_vol2/data/ICECAPSarchive/mpl/raw', date_range=None, filenames_list=None):
    '''Function to move .mpl.gz raw files from the ICECAPS archive to a desired target directory.

    INPUTS:
        dir_target : string
            String containing the base directory for the mpl data analysis. Files will be copied into dir_target/mplraw

        dir_mpl : string
            The directory from which the .mpl.gz files will be copied.

        date_range : None, 2x1 iterable of dt.datetime objects
            The initial and start datetime objects for which a list of files to copy will be generated. If None, then filenames_list will be used.

        filenames_list : None, iterable of strings
            Iterable of strings that will serve as the filenames to be copied - must be exact matches including file extensions.

    OUTPUTS: None
    '''
    # either date_range or filenames_list must be not None
    if date_range is None and filenames_list is None:
        warnings.warn(f'move_mplraw({dir_target=}, {dir_mpl=}, {date_range=}, {filenames_list=}) -- Neither date_range or filenames_list has been set. Returning None.')
        return None

    mpl_filename_format = '%Y%m%d%H%M.nc.zip'

    # we will put the mpl files into dir_target/mplraw, so need to check if that subdirectory exists
    if not os.path.isdir(os.path.join(dir_target,'mplraw')):
        warnings.warn(f'move_mplraw: /mplraw does not exist at {dir_target=}. Creating subdirectory now.')
        os.mkdir(os.path.join(dir_target,'mplraw'))

    # change dir_target to have the /mplraw as its endpoint
    dir_target = os.path.join(dir_target,'mplraw') 

    # date_range takes precedence over filenames_list
    if date_range is not None:
        dt_hour = dt.timedelta(hours=1)
        date_init = date_range[0]
        date_end = date_range[1]
        # need to round to the hour: down for date_init; up for date_end
        date_init = _remove_minute_from_datetime(date_init)
        date_end = _remove_minute_from_datetime(date_end) + dt_hour

        currentDate = date_init
        while currentDate <= date_end:
            # for each datetime in the range, we need to create the expected filename and see if its in the directory
            current_filename = currentDate.strftime(mpl_filename_format)
            exists_archive = os.path.exists(os.path.join(dir_mpl,current_filename))
            exists_destination = os.path.exists(os.path.join(dir_target,current_filename))

            print(f'{current_filename} | {exists_archive=} | {exists_destination=}')
            shutil.copy(os.path.join(dir_mpl,current_filename),os.path.join(dir_target,current_filename))

            currentDate = currentDate + dt_hour
        return

    # otherwise, filenames_list has been provided
    raise NotImplementedError

def _remove_minute_from_datetime(dtObj):
    '''Function to remove the minute (and finer) component(s) from a datetime object.
    
    INPUTS:
        dtObj : pydt.datetime object
            The datetime object for which we want to remove the minute component (round down).
            
    OUTPUTS:
        dtObj_ : pydt.datetime object
            The datetime object with the minute and finer components removed.
    '''
    d_hour_string = f'{dtObj.year:04}-{dtObj.month:02}-{dtObj.day:02}T{dtObj.hour:02}:00:00'
    dtObj_ = dt.datetime.fromisoformat(d_hour_string)
    return dtObj_