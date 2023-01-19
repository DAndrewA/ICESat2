'''Author: Andrew Martin
Creation date: 17/1/23

Code to load in the .nc files from a folder and concatenate them into a singular xarray dataset
'''

import os
import xarray as xr
import numpy as np
import netCDF4

def load_xarray_from_mmcrmom(dir_target):
    '''Function to load multiple MMCRMOM.nc files in dir_target into a singular xr.Dataset object.

    INPUTS:
        dir_target : string
            the target directory that contains the data files.

    OUTPUTS:
        ds : xr.Dataset object
            The xr.Dataset object containing the radar data.
    '''
    # list all the MMCRMom.nc files in the directory
    files_mmcr = os.listdir(dir_target)
    files_mmcr = [f for f in files_mmcr if f[-10:] == 'MMCRMom.nc']

    print(f'Files being loaded: {files_mmcr}')

    # list to hold the individual datasets before concatenation
    datasets = []

    for fname in files_mmcr:
        data = xr.load_dataset(os.path.join(dir_target,fname))
        datasets.append(data)

    ds = xr.concat(datasets,dim='time')
    return ds

'''£example code
target = '/home/users/eeasm/_scripts/ICESat2/src/mmcr'
ds = load_xarray_from_mmcrmom(target)
print(ds)
'''

def read_radar_data(start_date,stop_date,mode_idx, mask_sn): 
    '''Author: Sarah Barr
    Creation date: 18/1/23

    Function to read processed radar files between two dates, select data from one mode and output one xarray dataset
    
    Input: 
     - dates: in format YYYY-MM-DD
     - mask_sn: boolean, True masks data where signal to noise ratio <-14
    '''
    #start_time = time.time()
    dpath = '/gws/nopw/j04/ncas_radar_vol2/data/ICECAPSarchive/mmcr/processed/'
    
    all_files = []
    date_list = pd.date_range(start_date,stop_date,freq='1D')

    for date in date_list:
        all_files.append(glob.glob(dpath+ 'smtmmcrmomX1.b1.%s*.cdf'%dt.datetime.strftime(date,format='%Y%m%d')))

    flatten = lambda l: [item for sublist in l for item in sublist]
    all_files = flatten(all_files)
    all_files.sort()

    # get heights to add back later (necessary due to problem with xarray trying to input netcdf with a variable and dimension called 'heights')
    mmcr_heights = netCDF4.Dataset(all_files[0],'r')
    height_vals = mmcr_heights.variables['heights'][:]

    mmcr_data = xr.open_mfdataset(all_files,concat_dim = 'time', combine = 'nested',drop_variables='heights')
    
    #reassign height values 
    mmcr_data = mmcr_data.assign(height_vals=(['mode','heights'],height_vals))
    
    # select data from chosen mode
    mmcr_data = mmcr_data.sel(mode = mode_idx)
    mmcr_data = mmcr_data.where(mmcr_data.ModeNum==3., drop = True)
    
    mmcr_data = mmcr_data.assign_coords(time =mmcr_data.time_offset)
    mmcr_data = mmcr_data.assign_coords(heights =mmcr_data.height_vals[:,0].values)
    
    if mask_sn:
        mmcr_data = mmcr_data.where(mmcr_data.SignalToNoiseRatio>-14)
        
    #print("--- %s seconds ---" % (time.time() - start_time))
    return mmcr_data