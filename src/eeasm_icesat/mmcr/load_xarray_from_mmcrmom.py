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

def read_radar_data(dir_target, mode_idx=3, mask_sn=None): 
    '''Author: Sarah Barr
    Creation date: 18/1/23

    Function to read all of the files within a directory that are MMCR Moment files.
    
    INPUTS:
        dir_target : string
            directory the .nc data files are located in.
        mode_idx : int : 3
            radar operational mode from which we want to select the data. This is 0-indexed, whereas the instrument modes range from 1-10. Thus, subtract one from the desired mode. *** CHECK THIS IS TRUE ***
        mask_sn : float, None
            If None, no masking will be performed, if a float, any reflectivity lower than mask_sn will be culled
        
    '''
    #start_time = time.time()
    files_mmcr = os.listdir(dir_target)
    files_mmcr = [f for f in files_mmcr if f[-10:] == 'MMCRMom.nc']
    files_mmcr = [os.path.join(dir_target,f) for f in files_mmcr]
    files_mmcr = sorted(files_mmcr)

    mmcr_data = xr.open_mfdataset(files_mmcr,concat_dim = 'time', combine = 'nested')#,drop_variables='heights')
    
    # testing the laoding of the netcdf
    #mmcr_data = xr.open_dataset(files_mmcr[0])
    #return mmcr_data

    #reassign height values 
    #mmcr_data = mmcr_data.assign(height_vals=(['mode','heights'],height_vals))
    
    # select data from chosen mode
    mmcr_data = mmcr_data.sel(mode = mode_idx,drop=True)
    #mmcr_data = mmcr_data.where(mmcr_data.ModeNum==mode_idx)#, drop = True)
    

    heights = mmcr_data.Heights
    heights = heights.where(heights < 1e30)
    heights.interpolate_na(dim='heights',fill_value='extrapolate')

    mmcr_data = mmcr_data.assign_coords(Heights=heights)
    #mmcr_data = mmcr_data.assign_coords(time =mmcr_data.time_offset)
    
    if mask_sn is not None:
        mmcr_data = mmcr_data.where(mmcr_data.SignalToNoiseRatio> mask_sn)
    mmcr_data = mmcr_data.where(mmcr_data.SignalToNoiseRatio < 1e36)
        
    #print("--- %s seconds ---" % (time.time() - start_time))
    return mmcr_data