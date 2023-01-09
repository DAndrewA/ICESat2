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
        height = f['profile_1']['high_rate']['ds_va_bin_h'][()]
        layer = np.arange(10)
        surface_type = np.arange(5)

        # delta_time differs between profiles. As such, we need to find the length of the time dimensions and pick the longest one
        time_lengths = np.zeros((3,))
        for p in profile:
            time_lengths[p-1] = int(f[f"profile_{p}"]['high_rate']['delta_time'].size)
        time_index = np.arange(np.max(time_lengths)).astype(int)

        # add these to the dataset object
        coords = {'profile':profile, 'time_index':time_index, 'height':height, 'layer':layer, 'surface type':surface_type}
        ds = ds.assign_coords(coords)
        print(ds.dims)

        # ASSUMES NONE OF THE COORDINATES HAVE THE SAME SIZE: REQUIRE THAT time!=700 AND ALL WILL BE FINE... 
        dim_lengths = {v.size: k for k,v in coords.items()}
        for l in time_lengths: # include the additional time lengths for the labelling of coordinates in the DataArrays.
            dim_lengths[l] = 'time_index'

        max_time_length = int(np.max(time_lengths))
        # for each variable in the profile_[n]/high_rate/ part of the file, we need to create an xr.DataArray to hold its information for all 3 profiles, with the other required dimensions included.
        for k in f['profile_1']['high_rate'].keys():
            # determine the shape the values need to take on
            shape_inprofile = list(f['profile_1']['high_rate'][k].shape)
            # generate the list of axis names for the values
            axis_names = [dim_lengths[v] for v in shape_inprofile]
            # if 'time index' is in axis_names, we need to ensure that length is set to max_time_length
            if 'time_index' in axis_names:
                shape_inprofile[0] = max_time_length
            vals = np.zeros(shape=(3,*shape_inprofile))

            # populate vals with the values from the three profiles
            for p in profile:
                # if time_index is being used, we need to know how many NaNs we need to pad the data with:
                insert_vals = f['profile_' + str(p)]['high_rate'][k][()]
                if 'time_index' in axis_names:
                    padding_length = int(max_time_length - time_lengths[p-1])
                    if padding_length:
                        padding_shape = [int(v) for v in insert_vals.shape]
                        padding_shape[0] = padding_length
                        padding_nan = np.empty(padding_shape) * np.nan
                        insert_vals = np.concatenate((insert_vals,padding_nan))

                vals[p-1,...] = insert_vals

            # regenerate the list of axis names for vals
            axis_names = [dim_lengths[v] for v in vals.shape]
            print(f'{k} | {vals.shape}: {axis_names}')

            # generate attributes for the xarray DataArray
            attrs = {k:v for k,v in f['profile_1']['high_rate'][k].attrs.items()}

            # need to subset the coordinates based on which are present in vals
            da_coords = {v: coords[v] for v in axis_names}

            # create the DataArray and append it to the Dataset
            da = xr.DataArray(vals,coords=da_coords, dims=axis_names, attrs=attrs)
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


'''Example code
fname = '/home/users/eeasm/ICESAT_data/RGT0749_Cycles_10-12-bigger/processed_ATL09_20210211004659_07491001_005_01.h5'
ds = load_xarray_from_ATL09(fname)

print(ds)
'''