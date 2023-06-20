'''Author: Andrew Martin
Creation Date: 20/6/23

Functions to run my implementation of the DDA-atmos algorithm on ATL09 data.
'''

import numpy as np
import xarray as xr

import steps as steps

def dda_atl(data, heights,
        kernal_args={}, density_args={}, threshold_args={}, 
        kernal_args2={}, density_args2={}, threshold_args2={},
        min_cluster_size=300, remove_clusters_in_pass=False, fill_clouds_with_noise=True):
    '''Function to run the full DDA-atmos algorithm on the ATL09 data.
    
    This follows the threading described in the ATBD part 2 Section 21. 

    INPUTS:
        data : np.ndarray
            (n,m) numpy array, the ATL09 cab_prof data that will be the input for the DDA algorithm
    
        heights : np.ndarray
            (m,) numpy array that contains the heights of the vertical bins in the ATL09 data.

        kernal_args, kernal_args2 : dict
            Dictionaries containing the additional parameters required for the kernal calculation, for passes 1 and 2.

        density_args, density_args2 : dict
            Dictionaries containing the additional parameters for the density calculation in passes 1 and 2.

        threshold_args, threshold_args2 : dict
            Dictionaries containing the additional parameters for the threshold calculation

        min_cluster_size : int
            Minimum connected-cluster size for pixels in the cloud mask to not be removed.

        remove_clusters_in_pass : bool
            Flag for removing small clusters in cloud_mask[1,2] if True. Otherwise, small clusters will only be removed after the masks have been combined.

    OUTPUTS:

    '''
    # Threading: 1: Run DDA-atmos to determination of combined decluster mask [section 3.1 to 3.5]

    #TODO: implement kernal creation

    data_mask = np.isnan(data)

    density1 = steps.calc_density_field(data, data_mask, kernal1, **density_args)
    thresholds1 = steps.calc_threshold(density1, data_mask, **threshold_args)
    if remove_clusters_in_pass:
        cloud_mask1 = steps.calc_cloud_mask(density1,thresholds1,data_mask, remove_small_clusters=min_cluster_size)
    else:
        cloud_mask1 = steps.calc_cloud_mask(density1,thresholds1,data_mask)

    # update the data_mask variable to include cloud_mask1.
    if fill_clouds_with_noise:
        raise NotImplementedError
        # fill data[cloud_mask1] with noise
        density2 = steps.calc_density_field(data,data_mask, kernal2, **density_args2)
    else:
        data_mask = np.logical_or(data_mask, cloud_mask1)
        density2 = steps.calc_density_field(data, data_mask, kernal2, **density_args2)
    thresholds2 = steps.calc_threshold(density2, data_mask, **threshold_args2)
    if remove_clusters_in_pass:
        cloud_mask2 = steps.calc_cloud_mask(density2,thresholds2,data_mask, remove_small_clusters=min_cluster_size)
    else:
        cloud_mask2 = steps.calc_cloud_mask(density2,thresholds2,data_mask)
    # create the combined cloud_mask variable
    cloud_mask_combined = steps.combine_masks((cloud_mask1,cloud_mask2), remove_small_clusters=min_cluster_size)



