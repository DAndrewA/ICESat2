'''Author: Andrew Martin
Creation Date: 16/6/23

Function to get the ground return bin in the data (if it exists) by checking bins in a density pass that occur within a tolerence of the DEM and are found in the cloud mask.
'''

import numpy as np

def get_ground_bin(density, cloud_mask, heights, dem, dem_tol):
    '''Function to get the bin associated with the ground return signal.
    
    The algorithm steps are outlined in the ATL09 ATBD part 2 Sec22.3.
    
    NOTE: the curent implementation of the algorithm assumes the values of heights are evenly spaced and ordered.

    INPUTS:
        density : np.ndarray
            nxm numpy array for the density field of the dda calculation

        cloud_mask : np.ndarray (dtype=boolean)
            nxm numpy array for the output cloud mask of the dda

        heights : np.ndarray
            (m,) numpy array containing the height coordinates of the data
        
        dem : np.ndarray
            (n,) numpy array containing the DEM heights for the data

        dem_tol : int
            number of height bins (pixels) that a 'cloudy' pixel must be within the dem of to qualify as being part of the gorund signal.

    OUTPUTS:

    '''
    #Ensure that the heights variable is in ascending order, and flip density and cloud_mask if required.
    dh = 0
    if (np.diff(heights)<0).any():
        if (np.diff(heights)>=0).any(): # raise error if not ordered
            msg = 'heights isnt ordered'
            raise ValueError(msg)
        heights = np.flip(heights)
        density = np.flip(density,axis=1)
        cloud_mask = np.flip(cloud_mask,axis=1)
        dh = np.mean(np.diff(heights))

    dem_bin = np.floor_divide(dem,dh)
