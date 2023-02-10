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




def raw_to_ingested(dir_target,date,limit_height=True, c=299792458):
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

    OUTPUTS:
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
        print(f'raw_to_ingested: For full day, 24 files are expected. {len(mpl_filenames)} files matching date {date} in {dir_target=} found.')
        return False

    # load in the data to an xarray dataset
    data_loaded = xr.open_mfdataset(str(os.path.join(dir_target, filename_fmt)), combine='nested',concat_dim='profile') # open_mfdataset allows glob strings

    # create ingested dataset, with appropriate dimensions and height coordinates
    ds = xr.Dataset()
    # set the dimensions for the dataset
    dims = {'time':17280, 'height':1999}
    if limit_height: 
        dims['height'] = 1200
    
    args = {'num_bins': dims['height'], 'bin_time':data_loaded['bin_time'].values[0], 'c':c, 'v_offset':3000}
    heights = generate_heights(**args)
    times = data_loaded.time.values

    ds = ds.assign_coords({'time': times,'height':heights})

    # for each variable in VARIABLES_INGESTED, create the appropriate data, and turn it into a DataArray
    ingest_kwargs = {'limit_height':True}
    for k,l in VARIABLES_INGESTED.items():
        # create the data based on the ingestion function
        if l[3] is None:
            continue
        temp = l[3](data_loaded,**ingest_kwargs)
        temp = temp.astype(l[1])

        attrs = l[2]
        dims = l[0]
        da = xr.DataArray(temp,dims=dims,attrs=attrs)
        ds[k] = da

    print('=================================')
    print(ds)
    return ds







def generate_heights(num_bins, bin_time, c, v_offset=3000):
    '''Function to generate the heights for each bin based on the measurement frequency, speed of light and vertical offset.
    
    INPUTS:
        num_bins : int
            The number of height bins that need to be created

        bin_time : float ; [s]
            The 'bin_time' variable from the raw data, the integration period of the instrument.

        c : float ; [m/s]
            The speed of light.

        v_offset : float ; default= 3000 [m]
            The vertical offset of the first height bin, given as a positive number for distance below ground level.

    OUTPUTS:            
        heights : np.ndarray (num_bins,)
            Numpy array containing the bin heights in meters.
    '''
    # calculate the heights based on : half the distance light can travel in the given time, minus some offset
    heights = 0.5*bin_time*c*np.arange(num_bins) - v_offset
    return heights


######################################################
################ INGESTING FUNCTIONS #################
######################################################
# Functions for ingesting the data into the ingested #
# format. Each variable will have its own function,  #
# and the outputs of the function will be parsed     #
# into the datatype defined in VARIABLES_INGESTED.   #
######################################################

def ingest_base_time(dsl, **kwargs):
    '''Create the ingested base_time variable.
    
    INPUTS:
        dsl : xr.Dataset
            The loaded dataset.
    
    OUTPUTS:
        base_time : float
            The variable for base_time in the ingested data.
    '''
    
    base_time = dsl.time[0]
    return base_time

def ingested_time_offset(dsl, **kwargs):
    '''Create the ingested time_offset variable.
    
    INPUTS:
        dsl : xr.Dataset
            The loaded dataset.
            
    OUTPUTS:
        time_offset : np.ndarray (time,)
            The time offset from the base time.
    '''
    base_time = dsl.time.values[0]
    time_offset = dsl.time.values - base_time
    return time_offset

def ingested_backscatter_1(dsl,limit_height,**kwargs):
    '''Create the backscatter_1 ingested variable.
    
    INPUTS:
        dsl : xr.Dataset
            The loaded dataset
            
        limit_height : boolean
            If true, returns the height-limitted (lowest 1200) backscatter, otherwise returns the backscatter.
            
    OUTPUTS:
        backscatter_1 : np.ndarray (time,height)
            numpy array containing data for the backscatter_1 variable.
    '''
    backscatter_1 = dsl.channel_1.values
    if limit_height:
        backscatter_1 = backscatter_1[:,:1200]
    return backscatter_1

def ingested_backscatter_2(dsl,limit_height,**kwargs):
    '''Create the backscatter_2 ingested variable.
    
    INPUTS:
        dsl : xr.Dataset
            The loaded dataset
            
        limit_height : boolean
            If true, returns the height-limitted (lowest 1200) backscatter, otherwise returns the backscatter.
            
    OUTPUTS:
        backscatter_2 : np.ndarray (time,height)
            numpy array containing data for the backscatter_2 variable.
    '''
    backscatter_2 = dsl.channel_2.values
    if limit_height:
        backscatter_2 = backscatter_2[:,:1200]
    return backscatter_2



'''
# variables required by the ingested data format
# dictionary entries are the variable name, associated with lists containing:
    [0] : tuple of strings
        dimension names for the variable

    [1] : dtype
        data type the variable has

    [2] : dictionary
        attributes that the data variable has in the ingested format.

    [3] : function handle, None
        Function for ingesting the data.
'''
VARIABLES_INGESTED = {
    'base_time': [(), np.datetime64, {'long_name': 'Base time in Epoch'}, ingest_base_time],
    'time_offset': [('time',), np.timedelta64, {'long_name': 'Time offset from base_time'}, ingested_time_offset],
    'hour': [('time',), np.float32, {'long_name': 'Hour of the day', 'units': 'UTC'}, None],
    'nshots': [('time',), np.int32, {'long_name': 'number of laser shots', 'units': 'unitless'}, None],
    'rep_rate': [('time',), np.int32, {'long_name': 'laser pulse repetition frequency', 'units': 'Hz'}, None],
    'energy': [('time',), np.float32, {'long_name': 'laser energy', 'units': 'microJoules'}, None],
    'temp_detector': [('time',), np.float32, {'long_name': 'detector temperature', 'units': 'C'}, None],
    'temp_telescope': [('time',), np.float32, {'long_name': 'telescope temperature', 'units': 'C'}, None],
    'temp_laser': [('time',), np.float32, {'long_name': 'laser temperature', 'units': 'C'}, None],
    'mn_background_1': [('time',), np.float32, {'long_name': 'mean background in channel 1', 'units': 'counts / microsecond'}, None],
    'sd_background_1': [('time',), np.float32, {'long_name': 'standard deviation of the background in channel 1', 'units': 'counts / microsecond'}, None],
    'mn_background_2': [('time',), np.float32, {'long_name': 'mean background in channel 2', 'units': 'counts / microsecond'}, None],
    'sd_background_2': [('time',), np.float32, {'long_name': 'standard deviation of the background in channel 2', 'units': 'counts / microsecond'}, None],
    'initial_cbh': [('time',), np.float32, {'long_name': 'initial cloud base height from MPL software', 'units': 'km AGL'}, None],
    'backscatter_1': [('time', 'height'), np.float32, {'long_name': 'attenuated backscatter in channel 1', 'units': 'counts / microsecond', 'channel_interpretation': 'This is the linear cross-polarization channel.  It is sensitive to the depolarized backscatter from the atmosphere', 'comment': 'This field literally contains the counts detected by the detector for each range bin.  No corrections of any kind have been applied to this field.  In order to make proper use of the data, one should correct for detector non-linearity, subtract the afterpulse, subtract background counts, apply a range-squared correction, and correct for optical overlap and collimation effects'}, ingested_backscatter_1],
    'backscatter_2': [('time', 'height'), np.float32, {'long_name': 'attenuated backscatter in channel 2', 'units': 'counts / microsecond', 'channel_interpretation': 'This is the circular polarization channel.  It is sensitive to the unpolarized backscatter from the atmosphere', 'comment': 'This field literally contains the counts detected by the detector for each range bin.  No corrections of any kind have been applied to this field.  In order to make proper use of the data, one should correct for detector non-linearity, subtract the afterpulse, subtract background counts, apply a range-squared correction, and correct for optical overlap and collimation effects'}, ingested_backscatter_2],
    'lat': [(), np.float32, {'long_name': 'north latitude', 'units': 'deg'}, None],
    'lon': [(), np.float32, {'long_name': 'east longitude', 'units': 'deg'}, None],
    'alt': [(), np.float32, {'long_name': 'altitude', 'units': 'm MSL'}, None]
}

# test function
date = datetime.date(2021,2,11)
raw_to_ingested('/home/users/eeasm/_scripts/ICESat2/data/cycle10/mpl/mpl',date)
