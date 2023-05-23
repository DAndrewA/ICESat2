'''Author: Andrew Martin
Creation date: 23/5/23

Function to interpolate a low_rate dataset onto the time dimension of a high_rate dataset loaded from load_xarray_from_ATL09.
'''

from .add_coordinates import _add_time
import xarray as xr

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

    interpCoords = {'time': ds.time.values}

    # for each DataArray in ds_low
    for k in ds_low.keys():
        if k in ds.keys():
            continue # avoids producing duplicate DataArrays

        da = ds_low[k].interp(coords=interpCoords)
        ds[k] = da

    return ds
        

