'''Author: Andrew Martin
Creation date: 17/1/23

Code to load in the .nc files from a folder and concatenate them into a singular xarray dataset
'''

import os
import xarray as xr
import numpy as np

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

    # list to hold the individual datasets before concatenation
    datasets = []

    for fname in files_mmcr:
        data = xr.load_dataset(os.path.join(dir_target,fname))
        datasets.append(data)

    ds = xr.concat(datasets,dim='time')
    return ds