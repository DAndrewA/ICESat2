import os
import h5py as h5
import xarray as xr
import numpy as np
import icepyx as ipx

def load_xarray_from_ATL09(filename,subsetVariables=None,createNan=True):
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
    
    INPUTS:
        filename : string
            filename of the .h5 ATL09 file to be loaded.

        subsetVariables : None, itterable of strings
            Itterable containing strings of the variables to be extracted from the h5 file's profiles.

        createNan : boolean
            Flag for whether or not to utilise the _FillValue attribute in data to create NaN values in the data. If True, will apply da.where(da < _FillValue), if False then the data won't be changed upon loading.

    OUTPUTS:
        ds : xr.DataSet object
            The xarray dataset containing the ATL09 data, with profile, time_index, height, layer and surface type as coordinates.
    '''

    subset_default = ('cab_prof','delta_time','density_pass1','density_pass2','ds_va_bin_h','latitude','longitude','prof_dist_x','prof_dist_y','range_to_top','surface_bin','surface_h_dens','surface_height','surface_width')
    subset_clouds = ('apparent_surf_reflec','asr_cloud_probability','cloud_flag_asr','cloud_flag_atm','cloud_fold_flag','ds_layers','layer_attr','layer_bot','layer_con','layer_conf_dens','layer_dens','layer_flag','layer_top','msw_flag') # TODO introduce functionality for subsetting variables

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
            # if subsetting of variables is being used, only include desired variables.
            if subsetVariables is not None:
                if k not in subsetVariables:
                    continue
            
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
            #attrs = {k:v for k,v in f['profile_1']['high_rate'][k].attrs.items()}
            attrs = {}
            for j,v in f['profile_1']['high_rate'][k].attrs.items():
                if type(v) == np.bytes_:
                    # solution from anon582847382: https://stackoverflow.com/questions/23618218/numpy-bytes-to-plain-string
                    v = v.decode('UTF-8')
                attrs[j] = v

            # if _FillValue is in the keys, extract the value
            fillValue = None
            if '_FillValue' in attrs:
                fillValue = attrs['_FillValue'][0]

            # need to subset the coordinates based on which are present in vals
            da_coords = {v: coords[v] for v in axis_names}

            # create the DataArray and append it to the Dataset
            da = xr.DataArray(vals,coords=da_coords, dims=axis_names, attrs=attrs)

            # if createNan is active, and fillValue is not None, then we want to create Nan values in the data array
            if createNan and fillValue is not None:
                da = da.where(da < fillValue)

            ds[k] = da

        return ds


def load_rate(filename,rate,subset,createNan,verbose=False):
    '''Function to load in the ATL09 subset variables from filename for the given rate.

    This function will perform what load_xarray_from_ATL09() did as of commit 7a75a7f, except with the ability to select the specific rate from which the variables are taken. In this way, load_xarray_from_ATL09 is now a wrapper function for load_rate.

    INPUTS:
        filename : string
            Full filename with extension for the ATL09 .h5 file to be loaded.

        rate : string, ['high_rate', 'low_rate']
            String denoting which rate to use in the profile.

        subset : None, iterable of strings
            If None, select all variables in the given rate. Otherwise, an iterable of all the desired variables from the ATL09 file.

        createNan : bool
            Flag to create Nan values in the data or to use the _FillValue when encountering erroneous data.

        verbose : bool
            Flag for whether or not to print information as function progresses.
    
    OUTPUTS:
        ds : xr.Dataset
            dataset containing the loaded variables for the given rate, as well as the desired dimensions.
    '''
    if verbose:
        print('='*25)
        print(f'load_rate({filename=}, {rate=}, {subset=}, {createNan=}, {verbose=})')

    ds = xr.Dataset()
    with h5.File(filename,'r') as f:
        # start by extracting the coordinate dimensions: profile, time, height and layer
        profile = np.array([1,2,3])
        height = f['profile_1'][rate]['ds_va_bin_h'][()]
        layer = np.arange(10)
        surface_type = np.arange(5)

        # delta_time differs between profiles. As such, we need to find the length of the time dimensions and pick the longest one
        time_lengths = np.zeros((3,))
        for p in profile:
            time_lengths[p-1] = int(f[f"profile_{p}"][rate]['delta_time'].size)
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
        # for each variable in the profile_[n]/<rate>/ part of the file, we need to create an xr.DataArray to hold its information for all 3 profiles, with the other required dimensions included.
        for k in f['profile_1'][rate].keys():
            # if subsetting of variables is being used, only include desired variables.
            if subset is not None:
                if k not in subset:
                    continue
            
            # determine the shape the values need to take on
            shape_inprofile = list(f['profile_1'][rate][k].shape)
            # generate the list of axis names for the values
            axis_names = [dim_lengths[v] for v in shape_inprofile]
            # if 'time index' is in axis_names, we need to ensure that length is set to max_time_length
            if 'time_index' in axis_names:
                shape_inprofile[0] = max_time_length
            vals = np.zeros(shape=(3,*shape_inprofile))

            # populate vals with the values from the three profiles
            for p in profile:
                # if time_index is being used, we need to know how many NaNs we need to pad the data with:
                insert_vals = f[f'profile_{p}'][rate][k][()]
                if 'time_index' in axis_names:
                    padding_length = int(max_time_length - time_lengths[p-1])
                    if padding_length: # if the length of the time dimension and times for the variable dont match
                        padding_shape = [int(v) for v in insert_vals.shape]
                        padding_shape[0] = padding_length
                        padding_nan = np.empty(padding_shape) * np.nan
                        # insert sufficient nan values at the end to pad the output to alllow time_index to function as a dimension
                        insert_vals = np.concatenate((insert_vals,padding_nan))

                vals[p-1,...] = insert_vals

            # regenerate the list of axis names for vals
            axis_names = [dim_lengths[v] for v in vals.shape]
            if verbose: print(f'{k} | {vals.shape}: {axis_names}')

            # generate attributes for the xarray DataArray
            #attrs = {k:v for k,v in f['profile_1']['high_rate'][k].attrs.items()}
            attrs = {}
            for j,v in f['profile_1'][rate][k].attrs.items():
                if type(v) == np.bytes_:
                    # solution from anon582847382: https://stackoverflow.com/questions/23618218/numpy-bytes-to-plain-string
                    v = v.decode('UTF-8')
                attrs[j] = v

            # if _FillValue is in the keys, extract the value
            fillValue = None
            if '_FillValue' in attrs:
                fillValue = attrs['_FillValue'][0]

            # need to subset the coordinates based on which are present in vals
            da_coords = {v: coords[v] for v in axis_names}

            # create the DataArray and append it to the Dataset
            da = xr.DataArray(vals,coords=da_coords, dims=axis_names, attrs=attrs)

            # if createNan is active, and fillValue is not None, then we want to create Nan values in the data array
            if createNan and fillValue is not None:
                da = da.where(da != fillValue)

            ds[k] = da

        return ds












SUBSET_DEFAULT = ('delta_time','ds_va_bin_h','latitude','longitude','cab_prof','density_pass2','surface_height','layer_top','layer_bot', 'cloud_flag_atm')

'''Example code
fname = '/home/users/eeasm/ICESAT_data/RGT0749_Cycles_10-12-bigger/processed_ATL09_20210211004659_07491001_005_01.h5'
ds = load_xarray_from_ATL09(fname)

print(ds)
'''