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
    raise NotImplementedError


def _add_d2s(ds):
    '''Function to add d2s (distance to Summit) coordinate to xr dataset.
    
    INPUTS:
        ds [xr.Dataset]: xarray dataset containing the ATL09 data
        
    OUTPUTS:
        ds [xr.Dataset]: ATL09 xarray Dataset with the newly added d2s coordinate
    '''
    # TODO look into whether or not there's a WGS method for obtaining separations mroe accurately...

    # coordinates for Summit extracted from Google Maps. Is there a more accurate/reliable source of coordinates?
    summit_lat = 72.5802131599
    summit_lon = -38.4561163693

    # lambda functions for handling degrees inputs
    sind = lambda degrees: np.sin(np.deg2rad(degrees))
    cosd = lambda degrees: np.cos(np.deg2rad(degrees))

    # dot product of normalised polar vectors described in (lat,lon) coords: to find the angle between them.
    dot_prod = sind(ds['latitude'])*sind(summit_lat) + cosd(ds['latitude'])*cosd(summit_lat) * ( cosd(ds['longitude'])*cosd(summit_lon) + sind(ds['longitude'])*sind(summit_lon) )
    
    a = 6400 # in km
    distance_to_summit = np.arccos(dot_prod) * a

    ds['d2s'] = distance_to_summit
    return ds.set_coords('d2s')