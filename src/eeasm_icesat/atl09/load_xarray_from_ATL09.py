import os
import h5py as h5
import xarray as xr
import numpy as np

def load_xarray_from_ATL09(filename,subsetVariables=None,get_low_rate=False, subsetVariables_low=None, createNan=True, verbose=False):
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

        subsetVariables : None, iterable of strings
            Itterable containing strings of the variables to be extracted from the h5 file's profiles.

        get_low_rate : bool
            Flag for whether or not to get data from both the high and low rate variables.

        subsetVariables_low : None, iterable of strings
            Iterable containing  strings of the variable names to be extracted from the ATL09 low_rate parts of the profiles.

        createNan : boolean
            Flag for whether or not to utilise the _FillValue attribute in data to create NaN values in the data. If True, will apply da.where(da < _FillValue), if False then the data won't be changed upon loading.

        verbose : bool
            Flag for whether or not to print data related to the laoding process.

    OUTPUTS:
        ds_high : xr.Dataset
            The xarray dataset containing the high_rate ATL09 data, with profile, time_index, height, layer and surface type as coordinates.

        ds_low : xr.Dataset (IFF get_low_rate==True)
            xarray Dataset containing the low_rate ATL09 data.
    '''

    ds_high = load_rate(filename=filename, rate='high_rate', subset=subsetVariables, createNan=createNan, verbose=verbose)
    
    if not get_low_rate:
        return ds_high # this is to maintain backwards compatability with older code.

    ds_low = load_rate(filename=filename, rate='low_rate', subset=subsetVariables_low, createNan=createNan, verbose=verbose)

    return ds_high, ds_low


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
        if verbose: print(ds.dims)

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
                fillValue = attrs['_FillValue']#[0]

            # need to subset the coordinates based on which are present in vals
            da_coords = {v: coords[v] for v in axis_names}

            # create the DataArray and append it to the Dataset
            da = xr.DataArray(vals,coords=da_coords, dims=axis_names, attrs=attrs)

            # if createNan is active, and fillValue is not None, then we want to create Nan values in the data array
            if createNan and fillValue is not None:
                da = da.where(da != fillValue)

            ds[k] = da

        return ds


def preproc_delta_time(ds):
    return ds.rename_dims( # rename dimension to standardise across profiles
        {'delta_time':'time_index'}
    ).drop_indexes( # drop the index from delta_time to allow time_index to be an integer index
        'delta_time'
    ).reset_coords( # turn delta_time from a coordinate into a variable
        'delta_time'
    )


def extrapolate_var(ds, var, dim, verbose=False):
    """Function to extrapolate the values in "delta_time" so that they can be used as coordinates for a given dataset.
    nan values in coordinates lead to errors, even when associated data is uniformly nan too
    """
    if verbose: print("="*5 + f" EXTRAPOLATING {var} along {dim} dimension")
    da = ds[var]
    dtype = da.dtype
    da = da.astype(np.float64)
    da = da.where(da > -9e+18) # replace fill of NaT values with NaN

    ds[var] = da.interpolate_na(
        dim=dim,
        fill_value="extrapolate"
    ).astype(dtype)
    if verbose: print("SUCCESS")
    return ds


def load_rate_by_group(
    fname: str, 
    rate: str, 
    subset_vars: None | list[str] = None, 
    verbose: bool = False
) -> xr.Dataset:
    """Function to load either the high_rate or low_rate data from an ATL09 data file
    
    INPUTS:
        fname: str
            full path to the file from which data will be loaded

        rate: str = "low_rate" | "high_rate"
            Which rate group from which data will be loaded

        subset_vars: None | list[str]
            List of variables to keep in the Dataset.
            None results in all variables being kept.

        verbose: bool
            Flag for printing for debug purposes

    OUTPUTS:
        ds: xr.Dataset
            Xarray dataset containing ATL09 data
    """

    if verbose: 
        print("="*10 + f" LOADING {os.path.basename(fname)}: {rate}")
        print("Loading individual profiles...", end="")
    ds_rate_list = [
        xr.open_dataset(
            fname,
            group=f"/profile_{p}/{rate}"
        )
        for p in [1,2,3]
    ]
    if verbose: 
        print("SUCCESS")
        print("Preprocessing delta_time -> time_index...",end="")

    ds_rate_list = [
        preproc_delta_time(ds)
        for ds in ds_rate_list
    ]
    if verbose: print("SUCCESS") 

    longest_time_dim = np.max([
        ds.time_index.size
        for ds in ds_rate_list
    ])
    pad_sizes = [
        longest_time_dim - ds.time_index.size
        for ds in ds_rate_list
    ]
    if verbose: print(f"{pad_sizes=}")

    if subset_vars is not None:
        ds_rate_list = [
            ds[subset_vars]
            for ds in ds_rate_list
        ]
        if verbose: 
            print(f"VARS SUBSET")
            print(subset_vars)
            print("SUCCESS")

    
    ds_rate_list = [
        ds.pad(
            pad_width = {
                'time_index': (0, ps)
            },
            #mode='maximum' # TODO: remove line if extrapolation of delta_time is succesful
        )
        for ds, ps in zip(ds_rate_list, pad_sizes)
    ]
    print("PADDING SUCCESS")

    ds_rate_list = [
        extrapolate_var(ds, "delta_time", "time_index")
        for ds in ds_rate_list
    ]

    ds = xr.concat(
        ds_rate_list, dim="profile"
    ).assign_coords(
        {
            "profile": ( ("profile",), [1,2,3] )
        }
    ).set_coords(
        "delta_time"
    )

    return ds
    

def load_xarray_from_groups(
    fname, 
    subset_vars_high = None,
    get_low_rate = True,
    subset_vars_low = None,
    verbose: bool = False
) -> xr.Dataset:
    """Function to load an xarray dataset from an ATL09 h5 file, utilising the "group" argument in xarrays load_dataset
    
    INPUTS:
        fname: string
            Full path to the .h5 file containing the ATL09 data to be loaded

        subset_vars_high: None | list[str]
            A list of strings denoting variable names to keep.
            If None, all variables from high_rate groups are loaded.

        get_low_rate: bool
            Flag for if the low-rate dataset should be loaded too.

        subset_vars_low: None | list[str]
            A list of strings denoting variable names to keep from the low_rate data
            If None, all variables are loaded

        verbose: bool
            Flag for verbose printing when loading, for debug purposes

    OUTPUT:
        ds: xr.Dataset
            xarray dataset containing data from the high_rate and low_rate groups of each profile_[123] group in the h5 file
    """
    ds_high = load_rate_by_group(fname, "high_rate", subset_vars_high, verbose=verbose)
    ds_high = extrapolate_var(ds_high, "delta_time", "time_index", verbose=verbose)

    if get_low_rate:
        ds_low = load_rate_by_group(fname, "low_rate", subset_vars_low, verbose=verbose)

        # pad dimension time_index of ds_low to match that of ds_high
        high_time_len = ds_high.time_index.size
        low_time_len = ds_low.time_index.size
        ds_low.pad(
            pad_width = {
                "time_index":(0, high_time_len - low_time_len)
            },
        )

        ds_low = extrapolate_var(ds_low, "delta_time", "time_index", verbose=verbose)


SUBSET_DEFAULT = ('delta_time','ds_va_bin_h','latitude','longitude','cab_prof','surface_height','layer_top','layer_bot', 'cloud_flag_atm', 'dem_h')
SUBSET_CLOUDS = (*SUBSET_DEFAULT,'apparent_surf_reflec','asr_cloud_probability','cloud_flag_asr','cloud_flag_atm','cloud_fold_flag','ds_layers','layer_attr','layer_bot','layer_con','layer_conf_dens','layer_dens','layer_flag','layer_top','msw_flag')

SUBSET_LOW_DEFAULT = ('delta_time','ds_va_bin_h','latitude','longitude')
SUBSET_LOW_CAL = (*SUBSET_LOW_DEFAULT, 'cal_c')

'''Example code
fname = '/home/users/eeasm/ICESAT_data/RGT0749_Cycles_10-12-bigger/processed_ATL09_20210211004659_07491001_005_01.h5'
ds_high, ds_low = load_xarray_from_ATL09(fname,get_low_rate=True)

ds_high = load_xarray_from_ATL09(fname)

print(ds)
'''
