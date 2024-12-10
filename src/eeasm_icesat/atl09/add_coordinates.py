'''Author: Andrew Martin
Created: 10/01/2023

Functions for adding convenient coordinates to an ATL09 xarray dataset.
'''

import xarray as xr
import numpy as np

def add_coordinates(ds, lonlat=None):
    '''Function to add all of the conveneience coordinates to an xr dataset.
    
    INPUTS:
        ds [xr.Dataset]: xarray dataset containing the ATL09 data

        lonlat: dict; None
            If not None, a dictionary of longitude and latitude to be passed into _add_d2s(), given in decimal degrees.
        
    OUTPUTS:
        ds [xr.Dataset]: ATL09 xarray Dataset with the newly added coordinates
    '''
    # sequentially add all additional coordinates
    if lonlat is not None:
        ds = _add_d2s(ds, **lonlat)
    else:
        ds = _add_d2s(ds)

    ds = _add_height_AGL(ds)
    ds = _add_time(ds)
    return ds


def _add_d2s(ds, lat=72.5802131599, lon=-38.4561163693):
    '''Function to add d2s (distance to Summit, km) coordinate to xr dataset.
    
    INPUTS:
        ds [xr.Dataset]: xarray dataset containing the ATL09 data

        lat : float
            Float defining the latitude of the point to caluclate the distance to, given in decimal degrees. Defaults to Summit's latitude.

        lon : float
            Float describing the longitude of the ground-point from which to calculate the distance to. Given in decimal degrees. Defaults to Summit's longitude
        
    OUTPUTS:
        ds [xr.Dataset]: ATL09 xarray Dataset with the newly added d2s coordinate
    '''
    # TODO look into whether or not there's a WGS method for obtaining separations mroe accurately...
    # TODO test function

    # coordinates for Summit extracted from Google Maps. Is there a more accurate/reliable source of coordinates?

    # lambda functions for handling degrees inputs
    sind = lambda degrees: np.sin(np.deg2rad(degrees))
    cosd = lambda degrees: np.cos(np.deg2rad(degrees))

    # dot product of normalised polar vectors described in (lat,lon) coords: to find the angle between them.
    dot_prod = sind(ds['latitude'])*sind(lat) + cosd(ds['latitude'])*cosd(lat) * ( cosd(ds['longitude'])*cosd(lon) + sind(ds['longitude'])*sind(lon) )
    
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
    NOTE: chnages 10/12/2024 to improve precision on final time values from [s] to [ns]
    
    INPUTS:
        ds [xr.Dataset]: xarray dataset containing the ATL09 data
        
    OUTPUTS:
        ds [xr.Dataset]: ATL09 xarray Dataset with the newly added time coordinate
    '''
    time = ds['delta_time']
    time = time.interpolate_na(dim='time_index',fill_value='extrapolate')
    one_second = np.timedelta64(1_000_000_000, 'ns')

    epoch = np.datetime64('2018-01-01').astype('datetime64[ns]')

    time = epoch + time*one_second
    ds['time'] = time.astype('datetime64[ns]')#.interpolate_na(dim='time_index', fill_value='extrapolate')
    return ds.set_coords('time')
