''' author: Andrew Martin
Creation date: 16/1/23

Function to move MOM MMCR files from the ICECAPSarchive on JASMIN to a target directory.
'''
import datetime as pydt
import os
import warnings
from ..helper import move_data_files as helper


def move_from_gws2(dir_target, dir_mmcr='/gws/nopw/j04/ncas_radar_vol2/data/ICECAPSarchive/mmcr/mom',date_range=None,filenames_list=None):
    '''Function to move MMCR MOM (raw) files from the ICECAPS archive to a target directory.

    The function will select files based on the date range that they fall in or based on direct matches to desired files. This means that date_range will take precedence over filenames_list if both are not None.

    If both date_range and filenames_list are None, then the function will return None and print a warning to the console that its being used incorrectly.

    The files will be copied into the folder target_dir/mmcrzip

    INPUTS:
        dir_target : string
            The target directory to copy the mmcr files into.

        dir_mmcr : string
            The folder from which the MMCR MOM files will be extracted. Defaults to the ICECAPS archive on the ncas radar gws.

        date_range : None, 2x1 iterable of datetime objects
            Ordered list of datetime objects, defines the start and end times (inclusive) that the program will look at for taking files from the ICECAPS archive. i.e. ['2022-12-14 12:37','2022-12-14 14:14'] will extract the 1200,1300,1400 files for the date 2022-12-14.

        filenames_list : None, iterable of strings
            List of filenames for which there must be a direct match in the archive (including file extension).
    '''
    # either date_range or filenames_list must be not None
    if date_range is None and filenames_list is None:
        warnings.warn(f'move_from_gws2({dir_target=}, {dir_mmcr=}, {date_range=}, {filenames_list=}) -- Neither date_range or filenames_list has been set. Returning None.')
        return None

    mmcr_filename_format = '%Y%j%H%MMMCRMom.nc.zip'

    # we will put the mmcr files into dir_target/mmcrzip, so need to check if that subdirectory exists
    if not os.path.isdir(os.path.join(dir_target,'mmcrzip')):
        warnings.warn(f'move_from_gws: /mmcrzip does not exist {dir_target=}. Creating subdirectory now.')
        os.mkdir(os.path.join(dir_target,'mmcrzip'))

    # change dir_target to have the /mmcrzip as its endpoint
    dir_target = os.path.join(dir_target,'mmcrzip') 

    # date_range takes precedence over filenames_list
    if date_range is not None:
        dt_hour = pydt.timedelta(hours=1)
        date_init = date_range[0]
        date_end = date_range[1]
        # need to round to the hour: down for date_init; up for date_end
        date_init = _remove_minute_from_datetime(date_init)
        date_end = _remove_minute_from_datetime(date_end) + dt_hour

        currentDate = date_init
        while currentDate <= date_end:
            # for each datetime in the range, we need to create the expected filename and see if its in the directory
            current_filename = currentDate.strftime(mmcr_filename_format)
            exists_archive = os.path.exists(os.path.join(dir_mmcr,current_filename))
            exists_destination = os.path.exists(os.path.join(dir_target,current_filename))

            print(f'{current_filename} | {exists_archive=} | {exists_destination=}')
            helper.copy_file(dir_mmcr,current_filename,dir_target)
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
    dtObj_ = pydt.datetime.fromisoformat(d_hour_string)
    return dtObj_


start = pydt.datetime(2018,7,21,13,12)
end = pydt.datetime(2018,7,22,1,13)
range = [start, end]
target = '/home/users/eeasm/_scripts/ICESat2/src/MMCR'
move_from_gws2(target,date_range=range)