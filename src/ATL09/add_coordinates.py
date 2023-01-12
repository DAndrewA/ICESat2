'''Author: Andrew Martin
Created: 10/01/2023

Functions for adding convenient coordinates to an ATL09 xarray dataset.
'''

import xarray as xr
import numpy as np

def add_coordinates(ds):
    '''Function to add all of the conveneience coordinates to an xr dataset.
    
    INPUTS:
        ds [xr.Dataset]: xarray dataset containing the ATL09 data
        
    OUTPUTS:
        ds [xr.Dataset]: ATL09 xarray Dataset with the newly added coordinates
    '''
    # sequentially add all additional coordinates
    ds = _add_d2s(ds)
    ds = _add_height_AGL(ds)
    ds = _add_time(ds)
    return ds


def _add_d2s(ds):
    '''Function to add d2s (distance to Summit, km) coordinate to xr dataset.
    
    INPUTS:
        ds [xr.Dataset]: xarray dataset containing the ATL09 data
        
    OUTPUTS:
        ds [xr.Dataset]: ATL09 xarray Dataset with the newly added d2s coordinate
    '''
    # TODO look into whether or not there's a WGS method for obtaining separations mroe accurately...
    # TODO test function

    # coordinates for Summit extracted from Google Maps. Is there a more accurate/reliable source of coordinates?
    summit_lat = 72.5802131599
    summit_lon = -38.4561163693

    # lambda functions for handling degrees inputs
    sind = lambda degrees: np.sin(np.deg2rad(degrees))
    cosd = lambda degrees: np.cos(np.deg2rad(degrees))

    # dot product of normalised polar vectors described in (lat,lon) coords: to find the angle between them.
    dot_prod = sind(ds['latitude'])*sind(summit_lat) + cosd(ds['latitude'])*cosd(summit_lat) * ( cosd(ds['longitude'])*cosd(summit_lon) + sind(ds['longitude'])*sind(summit_lon) )
    
    a = 6400 # in km
    distance_to_summit = np.arccos(dot_prod) * a # in km

    ds['d2s'] = distance_to_summit.interpolate_na(dim='time_index',fill_value='extrapolate')
    return ds.set_coords('d2s')


def _add_height_AGL(ds):
    '''Function to add height_AGL (height above ground level) coordinate to ATL09 dataset.
    
    INPUTS:
        ds [xr.Dataset]: xarray dataset containing the ATL09 data
        
    OUTPUTS:
        ds [xr.Dataset]: ATL09 xarray Dataset with the newly added height_AGL coordinate
    '''
    # TODO test and see if this can be plotted against...
    # TODO test function works...

    # order of subtraction then addition to preserve order of coordinates in height_AGL
    hAGL = (-ds['surface_height'] + ds['ds_va_bin_h']).where(ds['surface_height'] <1e38).interpolate_na(dim='time_index',fill_value='extrapolate',keep_attrs=True)

    ds['height_AGL'] = hAGL
    return ds.set_coords('height_AGL')


def _add_time(ds):
    '''Function to add time coordinate to ATL09 dataset.
    
    INPUTS:
        ds [xr.Dataset]: xarray dataset containing the ATL09 data
        
    OUTPUTS:
        ds [xr.Dataset]: ATL09 xarray Dataset with the newly added time coordinate
    '''
    time = ds['delta_time']
    time = time.interpolate_na(dim='time_index',fill_value='extrapolate').astype('timedelta64[s]')
    epoch = np.datetime64('2018-01-01').astype('datetime64[s]')
    time = time + epoch
    ds['time'] = time#.interpolate_na(dim='time_index', fill_value='extrapolate')
    return ds.set_coords('time')
