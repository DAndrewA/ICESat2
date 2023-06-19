'''Author: Andrew Martin
Creation Date: 16/6/23

Function to get the ground return bin in the data (if it exists) by checking bins in a density pass that occur within a tolerence of the DEM and are found in the cloud mask.
'''

import numpy as np

def get_ground_bin(density, cloud_mask, heights, dem, dem_tol):
    '''Function to get the bin associated with the ground return signal.
    
    The algorithm steps are outlined in the ATL09 ATBD part 2 Sec22.3.
    
    NOTE: the curent implementation of the algorithm assumes the values of heights are evenly spaced and ordered.
    NOTE: the dem_hop output variable isn't currently implemented.

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
        ground_bin : np.ndarray (dtype=int)
            (n,) numpy array containing the index of the ground in the profiles with respect to the orientation of the heights coordinate

        ground_height: np.ndarray
            (n,) numpy array containing the height values determined by the algorithm.
    '''
    (n_prof,n_vert) = density.shape
    #Ensure that the heights variable is in ascending order, and flip density and cloud_mask if required.
    dh = 0
    flipped = False
    if (np.diff(heights)<0).any():
        if (np.diff(heights)>=0).any(): # raise error if not ordered
            msg = 'heights isnt ordered'
            raise ValueError(msg)
        heights = np.flip(heights)
        density = np.flip(density,axis=1)
        cloud_mask = np.flip(cloud_mask,axis=1)
        dh = np.mean(np.diff(heights))
        flipped = True

    dem_bin = np.floor_divide(dem,dh)

    # reshape heights and dem to allow for "outer product" to be created
    delta_heights = heights.reshape((1,n_vert)) - dem.reshape((n_prof,1))

    delta_below = np.less_equal(delta_heights, dem+dem_tol*dh)
    delta_above = np.greater_equal(delta_heights, dem-dem_tol*dh)
    possible_ground = np.logical_and(delta_above,delta_below) # creates a mask of values +- dem_tol from the dem height
    possible_ground = np.logical_and(possible_ground, cloud_mask)

    ground_identified = np.max(possible_ground, axis=1).astype(bool)
    
    ground_bin = np.zeros_like(dem,dtype=int)
    ground_height = np.zeros_like(dem)

    for i,b in enumerate(ground_identified):
        if b: # if ground has been identified in the profile
            max_dens = np.max(density[i,possible_ground[i,:]])
            g_bin = np.min(np.nonzero(density[i,:] == max_dens)[0]) # takes the lowest index where the bin has a density equal to the maximum density in the profile that is within the dem tolerance
            ground_bin[i] = g_bin
    
    ground_height = dem + dh*(ground_bin - dem_bin)

    if flipped: # flip the indices back to the original height-coordinate-orientation
        ground_bin = n_vert - ground_bin - 1

    return ground_bin,ground_height
        
