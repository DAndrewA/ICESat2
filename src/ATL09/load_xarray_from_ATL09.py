import os
import h5py as h5
import xarray as xr
import icepyx as ipx

def load_xarray_from_ATL09(filename,subsetVariables=None):
    '''Function to load in ATL09 data to xarray format from the hdf5 file format.
    
    The function will first open the h5 file and then create a high-frequency and low-frequency xr.Dataset objects.
    Each xr.Dataset will have the dimensions of:
        + profile = 1,2,3
        + time = ['bkgrd_atlas']['delta_time']
        + height = ['profile1']['ds_va_bin_h']
        + layer = [0:10]

    I will then create xr.DataArray objects for datastructure in the profiles, with dimensions of profile,time and (height/layer) if required.
    These will then be placed into the xr.Dataset objects.

    At the end, I will return both the high-frequency and low-frequency datasets. These could then possibly be conjoined afterwards along the time axis, although I'm unsure if thats a good idea or not...
    '''
    pass

def load_xarray_from_ATL09_icepyx(filename, pattern=None, wanted_vars=None):
    '''Function to load in ATL09 datafiles to xarray format, utilising the icepyx.Read object.

    Given the limitations of icepyx release 0.6.4 (see Github issue #397) I've edited the icesat_summit version of icepyx.Read to allow ATL09 to be laoded.
    In this situation, each profile is assigned to a 'spot':
        1: profile_1/high_rate
        2: " "_2/" "
        3: " "_3/" "
        4: profile_1/low_rate
        5: " "_2/" "
        6: " "_3/" "
    '''
    if pattern is None:
        pattern = "processed_ATL{product:2}_{datetime:%Y%m%d%H%M%S}_{rgt:4}{cycle:2}{orbitsegment:2}_{version:3}_{revision:2}.h5"
    product = 'ATL09'

    reader = ipx.Read(data_source=filename, product=product, filename_pattern=pattern)

    # add the desired variables
    if wanted_vars is None:
        wanted_vars = ['longitude','latitude','cab_prof','density_pass2']
    reader.vars.append(var_list=wanted_vars)

    ds = reader.load()
    return ds
