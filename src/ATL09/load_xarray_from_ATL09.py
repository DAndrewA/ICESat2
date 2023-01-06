import os
import h5py as h5
import xarray as xr
import numpy as np
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
    ds = xr.Dataset()
    with h5.File(filename,'r') as f:
        # start by extracting the coordinate dimensions: profile, time, height and layer
        profile = np.array([1,2,3])
        time = f['profile_1']['high_rate']['delta_time'][()] # NEED TO IMPLEMENT POSSIBILITY FOR delta_time TO DIFFER BETWEEN PROFILES:
        height = f['profile_1']['high_rate']['ds_va_bin_h'][()]
        layer = np.arange(10)
        surface_type = np.arange(5)

        # add these to the dataset object
        coords = {'profile':profile, 'time':time, 'height':height, 'layer':layer, 'surface type':surface_type}
        ds = ds.assign_coords(coords)
        print(ds.dims)

        # ASSUMES NONE OF THE COORDINATES HAVE THE SAME SIZE: REQUIRE THAT time!=700 AND ALL WILL BE FINE... 
        dim_lengths = {v.size: k for k,v in coords.items()}
        # for each variable in the profile_[n]/high_rate/ part of the file, we need to create an xr DataArray to hold its information for all 3 profiles, with the other required dimensions included.
        for k in f['profile_1']['high_rate'].keys():
            shape_inprofile = f['profile_1']['high_rate'][k].shape
            vals = np.zeros(shape=(3,*shape_inprofile))

            # populate vals with the values from the three profiles
            print(f'{k}: target shape={vals.shape}: profile shape={f["profile_1"]["high_rate"][k].shape}')
            print(f'target shape={vals[0,...].shape}; profile shape={f["profile_1"]["high_rate"][k][()].shape}')
            for p in profile:
                print(f'{p}...')
                vals[p-1,...] = f['profile_' + str(p)]['high_rate'][k][()]

            # generate the list of axis names for vals
            axis_names = [dim_lengths[v] for v in vals.shape]
            print(f'{k}: {shape_inprofile}: {axis_names}')

            # generate attributes for the xarray DataArray
            attrs = {k:v for k,v in f['profile_1']['high_rate'][k].attrs}

            # create the DataArray and append it to the Dataset
            da = xr.DataArray(vals,coords=coords, dims=axis_names, attrs=attrs)
            ds[k] = da

        return ds


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


fname = '/home/users/eeasm/ICESAT_data/RGT0749_Cycles_10-12-bigger/processed_ATL09_20210211004659_07491001_005_01.h5'
ds = load_xarray_from_ATL09(fname)

print(ds)