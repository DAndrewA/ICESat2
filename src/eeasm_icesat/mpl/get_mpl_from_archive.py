'''Author: Andrew Martin
Creation date: 27/1/23

Function to get the mpl data from an archive position and then extract the files int the target directory.

This is a simple combineation of move_mplraw, extract_mplgz and extract_mpl2nc.
'''
import datetime
from move_mplraw import move_mplraw
from extract_from_mplgz import extract_from_mplgz
from extract_mpl2nc import extract_mpl2nc

def get_mpl_from_archive(dir_target, dir_mpl='/gws/nopw/j04/ncas_radar_vol2/data/ICECAPSarchive/mpl/raw', date_range=None, date=None, filenames_list=None, verbose=False):
    '''Function to get and extract raw mpl archived files.
    
    INPUTS:
        dir_target : string
            String containing the base directory for the mpl data analysis.

        dir_mpl : string
            The directory from which the .mpl.gz files will be copied.

        date_range : None, 2x1 iterable of dt.datetime objects
            The initial and start datetime objects for which a list of files to copy will be generated. If None, then filenames_list will be used.

        date : None, datetime.date
            If a singular date is desired, then a date object can be supplied from which a date_range variable can be created.

        filenames_list : None, iterable of strings
            Iterable of strings that will serve as the filenames to be copied - must be exact matches including file extensions.

        verbose : boolean
            if True, status for each file will be printed. If False, this will be in a compressed, single-line format
    '''
    print(f'get_mpl_from_archive({dir_target=}, {dir_mpl=}, {date_range=}, {date=}, {filenames_list=}, {verbose=})')

    if date is not None:
        d_init = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=0, minute=0, second=0)
        d_end = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=23, minute=59, second=59)
        date_range = [d_init, d_end]
    
    move_mplraw(dir_target=dir_target, dir_mpl=dir_mpl, date_range=date_range, filenames_list=filenames_list, verbose=verbose)
    extract_from_mplgz(dir_target=dir_target, verbose=verbose)
    extract_mpl2nc(dir_target=dir_target, verbose=verbose)