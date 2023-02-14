'''Author: Andrew Martin
Creation date: 14/2/23

Script to allow for the loading of .mpl.gz files without having to explicitly unzip the files.
'''

import mpl2nc
import gzip
import os
import datetime
import xarray as xr
import numpy as np
import netCDF4
import glob

def load_mpl_inline(fname):
    '''Function to load .mpl.gz files from the archive without the need to create additional files.
    
    This will work by opening the .gz file in a binary read mode, and then using functions from mpl2nc to read the binary format.
    
    The output from this should be a dictionary which I will turn into an xarray Dataset format. These can then be concatenated.
    
    INPUTS:
        fname : string
            Full filename of the .mpl.gz file to be opened, including the file extension.

    OUTPUTS:
        ds : xr.Dataset
            The loaded mpl data as an xarray dataset, which can be accepted by raw_to_ingested.py
    '''
    # same method as extract_mpl2nc, except utilising gzip.open().
    mpl = mpl2nc_read_mpl_gzip(fname)
    mpl = mpl2nc.process_nrb(mpl)
    # convert mpl to xr.Dataset format
    ds = mpl_dict_to_xarray(mpl)
    return ds


def mpl2nc_read_mpl_gzip(fname):
    '''Effective rewriting of mpl2nc.read_mpl to use gzip.open() rather than open().
    
    INPUTS:
        fname : string
            Full filename of the .mpl.gz file to be opened, including the file extension.
    '''
    dd = []
    with gzip.open(fname,'rb') as f:
        while True:
            d = mpl2nc.read_mpl_profile(f)
            if d is None:
                break
            dd.append(d)
    return mpl2nc.process_mpl(dd)


def mpl_dict_to_xarray(d):
    '''Convert the mpl2nc mpl dictionary to an xr.Dataset format.
    Rewrites the mpl2nc.write() function, except that the Dataset isn't saved to memory.
    
    INPUTS:
        d : dict
            The dictionary output of the mpl2nc loading process
            
    OUTPUTS:
        ds : xr.Dataset
            The xarray dataset created from the mpl dictionary.
    '''
    f = netCDF4.Dataset('diskless.nc','w',diskless=True)
    f.createDimension('profile', None)
    f.createDimension('range', None)
    f.createDimension('ap_range', None)
    f.createDimension('ol_range', None)
    f.createDimension('dt_coeff_degree', None)
    for k, v in d.items():
        h = mpl2nc.NC_HEADER[k]
        var = f.createVariable(k, mpl2nc.NC_TYPE[h['dtype']], h['dims'],
            fill_value=mpl2nc.FILL_VALUE[h['dtype']])
        var[::] = v
        if h['units'] is not None: var.units = h['units']
        if h['long_name'] is not None: var.long_name = h['long_name']
        if h['comment'] is not None: var.comment = h['comment']
    f.created = datetime.datetime.utcnow().strftime('%Y-%m-%dT:%H:%M:%SZ')
    f.software = 'mpl2nc (https://github.com/peterkuma/mpl2nc)'
    f.version = mpl2nc.__version__

    ds = xr.open_dataset(xr.backends.NetCDF4DataStore(f)).load()
    f.close()
    return ds


def mf_load_mpl_inline(fname_fmt, dir_root):
    '''Function to load multiple .mpl.gz files inline.
    
    INPUTS:
        fname_fmt : glob string
            glob string for the format the filenames take for the files being loaded.

        dir_root : string
            path to the root directory containing the .mpl.gz files
            
    OUTPUTS:
        ds : xr.Dataset
            xarray dataset containing the data from the mpl files.
    '''

    fnames = glob.glob(fname_fmt, root_dir=dir_root)
    fnames = sorted(fnames)
    fnames = [n for n in fnames if '.mpl.gz' in n[-7:]] # ensure all files are .mpl.gz

    ds = []
    for fname in fnames:
        n = os.path.join(dir_root,fname)
        print(f'loading {fname}')
        ds.append(load_mpl_inline(n))
    ds = xr.combine_nested(datasets=ds, concat_dim='profile')
    return ds



#fname = '/home/users/eeasm/_scripts/ICESat2/data/cycle10/mpl/mplraw_zip/202102110000.mpl.gz'
#load_mpl_inline(fname)

#dir_root = '/home/users/eeasm/_scripts/ICESat2/data/cycle10/mpl/mplraw_zip'
#globstr = '20210211*'
#print(mf_load_mpl_inline(globstr,dir_root))