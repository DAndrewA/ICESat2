'''Author: Andrew Martin
Creation Date: 16/6/23

A function to logically combine cloud masks, with the option to remove small clusters after the combination.
'''

import numpy as np
from skimage.morphology import remove_small_objects

def combine_masks(masks, remove_small_clusters=0):
    '''Function to logically combine multiple cloud masks, with the option to remove small clusters of pixels afterwards.
    
    INPUTS:
        masks : iterable of (n,m) np.ndarrays (dtype=boolean)
            Iterable of numpy ndarrays that are all boolean and the same shape. These are the individual cloud masks, with 1s indicating cloud and 0 indicating cloud-free pixels.

        remove_small_clusters : int
            Variable denoting the minimum cluster size for pixels to be considered in the cloud mask. If 0, no clusters of pixels will be removed.
    
    OUTPUTS:
        combined_mask : np.ndarray
            nxm numpy array containing the logically combined cloud masks, that has had small clusters removed.
    '''
    combined_mask = np.zeros_like(masks[0])
    for m in masks:
        combined_mask = np.logical_or(combined_mask, m)

    if remove_small_clusters > 0:
        combined_mask = remove_small_objects(combined_mask, min_size=remove_small_clusters)

    return combined_mask