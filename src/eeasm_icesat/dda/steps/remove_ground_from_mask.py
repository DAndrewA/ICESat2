'''Author: Andrew Martin
Creation Date: 16/6/23

Function to remove bins recognised as containing the ground signal from a mask.
'''

import numpy as np

def remove_ground_from_mask(layer_mask, ground_bin, cloud_mask, ground_width, heights, verbose=False):
    '''Function to remove the ground signal from a cloud_mask if the ground bins are present in layer_mask.

    As ground_bin should already take into account the ordering of heights, then heights is included to see whether the bin index needs to be incremented or decremented when iterating through the ground touching layer.
    
    INPUTS:
        layer_mask : np.ndarray (dtype=bool)
            nxm numpy array containing the mask for the consolidated cloud layers

        ground_bin : np.ndarray (dtype=int)
            (n,) numpy array containing the detected ground bin using get_ground_bin. This is independent of the ordering of heights.

        cloud_mask : np.ndarray (dtype=bool)
            nxm numpy array containing containing the combined cloud masks from the dda passes. This is what the ground signal will be removed from.

        ground_width : int
            Number of bins that the ground is expected to extend from the value in ground bin. This can be considered as the height of the kernal from the convolution.

        heights : np.ndarray
            (m,) numpy array used to determine if the masks are ordered in ascending or descending height. This changes whether the layers are counted from the top-down or bottom-up.

        verbose : bool
            Flag for printing out debug statements

    OUTPUTS:
        cloud_mask_no_ground : np.ndarray (dtype=bool)
            nxm numpy array containing the combined cloud mask information from the dda passes, with the ground signal removed.

        ground_mask : np.ndarray (dtype=bool)
            nxm numpy array containing a mask denoting ground pixels (1s) and non-ground pixels (0s).
    '''
    if verbose: print('==== dda.steps.remove_ground_from_mask()')
    cloud_mask_no_ground = cloud_mask.copy()
    ground_mask = np.zeros_like(cloud_mask)
    # determine if the counting needs to be flipped
    order = 1 # counting increments 
    if (np.diff(heights)<0).any():
        if (np.diff(heights)>=0).any(): # raise error if not ordered
            msg = 'heights isnt ordered'
            raise ValueError(msg)
        order = -1 # counting decerements

    for i,p in enumerate(layer_mask):
        g_bin = ground_bin[i]
        if ~np.isnan(g_bin): # if the ground signal has been detected
            # remove the ground signal from cloud_mask
            cloud_mask_no_ground[i,int(g_bin-ground_width):int(g_bin+ground_width+1)] = 0
            ground_mask[i,int(g_bin-ground_width):int(g_bin+ground_width+1)] = cloud_mask[i,int(g_bin-ground_width):int(g_bin+ground_width+1)]
    
    return cloud_mask_no_ground, ground_mask