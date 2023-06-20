'''Author: Andrew Martin
Creation Date: 16/6/23

Function to caluclate the cloud mask, given the density field, thresholds and data mask, with the option to remove small clusters.
'''

import numpy as np
from skimage.morphology import remove_small_objects

def calc_cloud_mask(density, threshold, data_mask=None, remove_small_clusters=0, verbose=False):
    '''Function to calculate the cloud mask from a density field and the associated thresholds.
    
    INPUTS:
        density : np.ndarray
            nxm numpy array containing the density field

        threshold : np.ndarray
            (x,1) numpy ndarray containing the threshold value for each vertical profile.

        data_mask : np.ndarray (dtype=boolean), None
            nxm numpy array determining which values in the input data are invalid. If not None, then regions of the cloud_mask will be set to 0 where data_mask is True. Otherwise, cloud_mask will not be affected.

        remove_small_clusters : int
            Variable denoting how big the minimum cluster size can be in the mask. If a connected cluster of masked pixels (clouds) are smaller than this value, they will be removed according to skimage.morphology.remove_small_objects. If 0, no clusters are removed.

        verbose : bool
            Flag for printing out debug statements

    OUTPUTS:
        cloud_mask : np.ndarray (dtype=boolean)
            nxm numpy array containing cloudy pixels (1s) and non-cloudy pixels (0s).
    '''
    if verbose: print(f'===== dda.steps.calc_cloud_mask()')
    cloud_mask = np.greater(density,threshold).astype(bool)
    if data_mask is not None:
        cloud_mask[data_mask] = 0

    if remove_small_clusters > 0:
        if verbose: print(f'Removing small clusters of size {remove_small_clusters} or smaller.')
        cloud_mask = remove_small_objects(cloud_mask,min_size=remove_small_clusters)

    return cloud_mask