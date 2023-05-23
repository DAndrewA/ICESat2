'''Author: Andrew Martin
Creation date: 23/5/23

Function to interpolate a low_rate dataset onto the time dimension of a high_rate dataset loaded from load_xarray_from_ATL09.
'''

from .add_coordinates import _add_time
import xarray as xr
import numpy as np

def interp_low_to_high(ds_low, ds_high, concat=True):
    '''Function to interpolate a low_rate dataset onto the time dimension of a high_rate dataset.
    
    INPUTS:
        ds_low : xr.Dataset
            dataset containing low_rate data variables. Direct output from load_xarray_from_ATL09.

        ds_high : xr.Dataset
            dataset containing the high_rate variables. These have the additional coordinate 'time' (rather than time_index), so are the output of add_coordinates().

        concat : bool
            Flag for whether to insert the interpolated data variables from ds_low into ds_high and return that, or to simply return the interpolated version of ds_low
    
    OUTPUTS:
        ds : xr.Dataset
            Dataset containing the interpolated low_rate values. If concat==True, this is generated from ds_high.
    '''
    # firstly, we need to add the time coordinate to ds_low
    ds_low = _add_time(ds_low)

    # setup the output dataset to use
    if concat:
        ds = ds_high
    else:
        # extract the dims from ds_high
        dims = ds_high.dims
        coords = ds_high.coords
        attrs = ds_low.attrs
        ds = xr.Dataset(coords=coords, attrs=attrs)
        print(ds)

    # for each DataArray in ds_low
    for k in ds_low.keys():
        if k in ds.keys():
            continue # avoids producing duplicate DataArrays

        # get the dimensions required for the interpolated DataArray
        
        # time coordinates handled as float64 to allow interpolation (casting errors)
        epoch = np.datetime64('2018-01-01').astype('datetime64[s]')
        time_low = (ds_low.time.values - epoch).astype(float)
        time_high = (ds_high.time.values - epoch).astype(float)

        data_low = ds_low[k].values

        # extract the desired shape for the high_data variable
        high_shape = [*data_low.shape]
        high_shape[:2] = [*time_high.shape]
        high_shape = tuple(high_shape)
        data_high = np.zeros(high_shape)

        try:
            for p in [0,1,2]: # for each profile in the data
                data_high[p] = np.interp(time_high[p],time_low[p],data_low[p])
        except Exception as err:
            print(f'interp_low_to_high: {k} can\'t be interpolated, likely as contains additional height coordinate.')
            raise err
            continue # skip if error occurs

        # fix coordinates for new data array
        coords = {'profile': ds.profile.values, 'time_index':ds.time_index.values}

        print(coords)

        da = xr.DataArray(data=data_high, coords=coords, attrs=ds_low[k].attrs)
        ds[k] = da

    return ds
        

