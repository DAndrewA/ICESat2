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
        if type(temp) == np.ndarray:
            temp = temp.astype(l[1])
        attrs = l[2]
        dims = l[0]
        da = xr.DataArray(temp,dims=dims,attrs=attrs)
        ds[k] = da

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

def datetime64_to_datetime(dt64):
    '''Converts a np.datetime64[ns] object to a python datetime.datetime object.
    Taken from https://gist.github.com/blaylockbk/1677b446bc741ee2db3e943ab7e4cabd?permalink_comment_id=3775327

    INPUTS:
        dt64 : np.datetime64
            The datetime64 object to be converted.
            
    OUTPUTS:
        dtdt : datetime.datetime
            The converted output datetime.datetime object.    
    '''
    timestamp = ( (dt64 - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1,'s') )
    return datetime.datetime.utcfromtimestamp(timestamp)

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

def ingested_hour(dsl, **kwargs):
    '''Create the ingested hour variable.
    NOTE: This approach gives a linear error from O(-5e-4) to 0 over 24 hours

    INPUTS:
        dsl : xr.Dataset
            raw loaded dataset
	    
	OUTPUTS:
        hour : np.ndarray (time,)
            Array containing the hour values for the measurements.
    '''
    time = dsl.time.values
    time_init = time[0]

    date = datetime64_to_datetime(time_init)
    date_delta = date - date.replace(hour=0,minute=0,second=0,microsecond=0)
    print(date_delta)
    
    delta = (((time - time_init).astype(datetime.datetime) / 1e9 + date_delta.total_seconds()) / 3600 ) % 24 #conversion to hours
    return delta

def ingested_nshots(dsl, **kwargs):
	'''Create the ingested nshots variable.
    
    INPUTS:
        dsl : xr.Dataset
	        The raw loaded dataset
	    
    OUTPUTS:
        nshots : np.ndarray (time,)
	        numpy array containing the summed shots per measurement.
	'''
	nshots = dsl.shots_sum.values
	return nshots

def ingested_rep_rate(dsl, **kwargs):
	'''Create the ingested rep_rate variable.
    
    INPUTS:
        dsl : xr.Dataset
	        The raw loaded dataset
	    
    OUTPUTS:
        rep_rate : np.ndarray (time,)
	        numpy array containing the shot frequency data.
	'''
	rep_rate = dsl.trigger_frequency.values
	return rep_rate

def ingested_energy(dsl, **kwargs):
	'''Create the energy ingested variable.
    Note, this formulation doesn't match the ingested value exactly, but the error is O(2e-7) which I deem to be sufficiently small for now.
    
    INPUTS:
        dsl : xr.Dataset
	        The raw laoded dataset.
	    
    OUTPUTS:
        energy : np.ndarray (time,)
	        np array with the laser energy output.
	'''
	energy = dsl.energy_monitor.values / 1000
	return energy

def ingested_temp_detector(dsl, **kwargs):
	'''Create the ingested temP_detector variable.
    NOTE: discrepancies between dsl and the original ingested format are due to float64->float32 conversions.
	
    INPUTS:
        dsl : xr.Dataset
	        the raw loaded data.
	    
	OUTPUTS:
        temp_detector : np.ndarray (time,)
	        numpy array with the detector temperature values.
	'''
	temp_detector = dsl.temp_0.values / 100
	return temp_detector

def ingested_temp_telescope(dsl, **kwargs):
	'''Create the ingested temp_telescope variable.
    NOTE: discrepancies between dsl and the original ingested format are due to float64->float32 conversions.
	
    INPUTS:
        dsl : xr.Dataset
	        the raw loaded data.
	    
	OUTPUTS:
        temp_telescope : np.ndarray (time,)
	        numpy array with the telescope temperature values.
	'''
	temp_telescope = dsl.temp_2.values / 100
	return temp_telescope

def ingested_temp_laser(dsl, **kwargs):
	'''Create the ingested temp_laser variable.
    NOTE: discrepancies between dsl and the original ingested format are due to float64->float32 conversions.
	
    INPUTS:
        dsl : xr.Dataset
	        the raw loaded data.
	    
	OUTPUTS:
        temp_laser : np.ndarray (time,)
	        numpy array with the laser temperature values.
	'''
	temp_laser = dsl.temp_3.values / 100
	return temp_laser

def ingested_mn_background_1(dsl, **kwargs):
	'''Create the mn_background_1 ingested variable.
    This is the mean background, and is simply taken from the background_average variable in the raw data.
    
    INPUTS:
        dsl: xr.Dataset
	        The loaded dataset
	    
    OUTPUTS:
        mn_background_1 : np.ndarray (time,)
            numpy array containing the mean background from channel 1
	'''
	mn_background_1 = dsl.background_average.values
	return mn_background_1

def ingested_sd_background_1(dsl, **kwargs):
	'''Create the sd_background_1 ingested variable.
	
	INPUTS:
        dsl : xr.Dataset
            The loaded raw dataset
	    
	OUTPUTS:
        sd_background_1 : np.ndarray (time,)
            Array containing the standard deviation of the background noise values
    '''
	sd_background_1 = dsl.background_stddev.values
	return sd_background_1
	
def ingested_mn_background_2(dsl, **kwargs):
    '''Create the mn_background_2 ingested variable.
    This is the mean background, and is simply taken from the background_average variable in the raw data.
    
    INPUTS:
        dsl: xr.Dataset
	        The loaded dataset
	    
    OUTPUTS:
        mn_background_2 : np.ndarray (time,)
            numpy array containing the mean background from channel 2
	'''
    mn_background_2 = dsl.background_average_2.values
    return mn_background_2

def ingested_sd_background_2(dsl, **kwargs):
	'''Create the sd_background_2 ingested variable.
	
	INPUTS:
        dsl : xr.Dataset
            The loaded raw dataset
	    
	OUTPUTS:
        sd_background_2 : np.ndarray (time,)
            Array containing the standard deviation of the background noise values
    '''
	sd_background_2 = dsl.background_stddev_2.values
	return sd_background_2

def ingested_initial_cbh(dsl, **kwargs):
	'''Create the ingested initial_cbh variable.
	It appears this is uniformly 0 in the files, so an arbitrary choice of (time,) variable can be used.
    
	INPUTS:
        dsl : xr.Dataset
            The raw loaded dataset
	    
	OUPUTS:
        initial_cbh : np.ndarray (time,)
            numpy array that contains the "lowest detected cloud base height". Will be uniformly 0.
    '''
	initial_cbh = dsl.bin_time.values * 0
	return initial_cbh

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

def ingested_lat(dsl, **kwargs):
	'''Create the lat ingested varibale.
	In the ingested the format, the value is simply given as 72.59622 -- check this is consistent with other values over time.
    '''
	return 72.59622

def ingested_lon(dsl, **kwargs):
	'''Create the lon ingested variable.
    In the ingested format, this appears to be given as -38.42197 - check this is consistent with other ingested files.
    '''
	return -38.42197

def ingested_alt(dsl, **kwargs):
	'''Create the alt ingested variable.
	
	In the ingested format, this variable is given as a line of value 0. The dsl.gps_altitude variable gives a valid number (3200.0 for 11/2/2021). I'll stick with a line of value 0, for consistency.
    
    INPUTS:
        dsl : xr.Dataset
            The raw loaded dataset
	    
    OUTPUTS:
        alt : float ()
            3200
    '''
	alt = 3200 # bin_time is an arbitrary choice
	return alt


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
    'hour': [('time',), np.float32, {'long_name': 'Hour of the day', 'units': 'UTC'}, ingested_hour],
    'nshots': [('time',), np.int32, {'long_name': 'number of laser shots', 'units': 'unitless'}, ingested_nshots],
    'rep_rate': [('time',), np.int32, {'long_name': 'laser pulse repetition frequency', 'units': 'Hz'}, ingested_rep_rate],
    'energy': [('time',), np.float32, {'long_name': 'laser energy', 'units': 'microJoules'}, ingested_energy],
    'temp_detector': [('time',), np.float32, {'long_name': 'detector temperature', 'units': 'C'}, ingested_temp_detector],
    'temp_telescope': [('time',), np.float32, {'long_name': 'telescope temperature', 'units': 'C'}, ingested_temp_telescope],
    'temp_laser': [('time',), np.float32, {'long_name': 'laser temperature', 'units': 'C'}, ingested_temp_laser],
    'mn_background_1': [('time',), np.float32, {'long_name': 'mean background in channel 1', 'units': 'counts / microsecond'}, ingested_mn_background_1],
    'sd_background_1': [('time',), np.float32, {'long_name': 'standard deviation of the background in channel 1', 'units': 'counts / microsecond'}, ingested_sd_background_1],
    'mn_background_2': [('time',), np.float32, {'long_name': 'mean background in channel 2', 'units': 'counts / microsecond'}, ingested_mn_background_2],
    'sd_background_2': [('time',), np.float32, {'long_name': 'standard deviation of the background in channel 2', 'units': 'counts / microsecond'}, ingested_sd_background_2],
    'initial_cbh': [('time',), np.float32, {'long_name': 'initial cloud base height from MPL software', 'units': 'km AGL'}, ingested_initial_cbh],
    'backscatter_1': [('time', 'height'), np.float32, {'long_name': 'attenuated backscatter in channel 1', 'units': 'counts / microsecond', 'channel_interpretation': 'This is the linear cross-polarization channel.  It is sensitive to the depolarized backscatter from the atmosphere', 'comment': 'This field literally contains the counts detected by the detector for each range bin.  No corrections of any kind have been applied to this field.  In order to make proper use of the data, one should correct for detector non-linearity, subtract the afterpulse, subtract background counts, apply a range-squared correction, and correct for optical overlap and collimation effects'}, ingested_backscatter_1],
    'backscatter_2': [('time', 'height'), np.float32, {'long_name': 'attenuated backscatter in channel 2', 'units': 'counts / microsecond', 'channel_interpretation': 'This is the circular polarization channel.  It is sensitive to the unpolarized backscatter from the atmosphere', 'comment': 'This field literally contains the counts detected by the detector for each range bin.  No corrections of any kind have been applied to this field.  In order to make proper use of the data, one should correct for detector non-linearity, subtract the afterpulse, subtract background counts, apply a range-squared correction, and correct for optical overlap and collimation effects'}, ingested_backscatter_2],
    'lat': [(), np.float32, {'long_name': 'north latitude', 'units': 'deg'}, ingested_lat],
    'lon': [(), np.float32, {'long_name': 'east longitude', 'units': 'deg'}, ingested_lon],
    'alt': [(), np.float32, {'long_name': 'altitude', 'units': 'm MSL'}, ingested_alt]
}

'''
# test function
date = datetime.date(2021,2,11)
raw_to_ingested('/home/users/eeasm/_scripts/ICESat2/data/cycle10/mpl/mpl',date)
'''
