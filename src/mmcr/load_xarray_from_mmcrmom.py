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

def read_radar_data(dir_target, mode_idx, mask_sn): 
    '''Author: Sarah Barr
    Creation date: 18/1/23

    Function to read all of the files within a directory that are MMCR Moment files.
    
    INPUTS:
        dir_target : string
            directory the .nc data files are located in.
        mode_idx : 
            radar operational mode from which we want to select the data. This is 0-indexed, whereas the instrument modes range from 1-10. Thus, subtract one from the desired mode. *** CHECK THIS IS TRUE ***
        mask_sn : boolean
            True will return data masked where the signal-to-noise ratio is less than -14. False will return all the data.
        
    '''
    #start_time = time.time()
    files_mmcr = os.listdir(dir_target)
    files_mmcr = [f for f in files_mmcr if f[-10:] == 'MMCRMom.nc']

    files_mmcr.sort()

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