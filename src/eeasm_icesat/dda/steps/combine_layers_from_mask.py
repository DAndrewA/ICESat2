'''Author: Andrew Martin
Creation Date: 16/6/23

The function to perform the up- and down-passes on the consolidated cloud mask to calculate the layer mask, from which the layer variables are calculated.
'''

import numpy as np

def combine_layers_from_mask(cloud_mask, min_depth=3, min_sep=3):
    '''Function to perform up- and down-passes on cloud_mask to create layers with the minimum depth and separation.
    
    INPUTS:
        cloud_mask : np.ndarray (dtype=boolean)
            nxm numpy array containin the consolidated cloud mask. 1s represent cloudy pixels, 0s represent cloud-free pixels.

        min_depth : int
            The minimum number of pixels a cloud layer can contain.

        min_sep : int
            The minimum number of pixels that can seperate two cloud layers.

    OUTPUTS:
        layer_mask : np.ndarray (dtype=boolean)
            nxm numpy array containing 1s for cloudy pixels and 0s for non-cloudy pixels. This has cloud layers of a minimum thickness and layers with a minimum separation.
    '''

    (n_prof, n_vert) = cloud_mask.shape
    buffer = np.max([min_depth,min_sep])
    layer_mask = np.zeros_like(cloud_mask)

    for i, profile in cloud_mask:
        # for each vertical profile
        cm_up = np.zeros_like(profile).astype(bool) # cloud masks that will be consolidated
        cm_down = np.zeros_like(profile).astype(bool)

        #upwards pass
        inCloud = False
        for j,b in enumerate(profile[:-buffer]):
            # b is a bool, 1 for cloud, 0 for not
            if b and not inCloud:
                # if there are min_depth_bins 1s in a row, this should evaluate as True
                if np.all(profile[j:j+min_depth] == 1):
                    inCloud=True
            elif not b and inCloud:
                # if there are min_sep_bins 0s in a row, this should evaluate as True
                if np.all(profile[j:j+min_sep] == 0):
                    inCloud = False
            cm_up[j] = inCloud

        # downwards pass
        inCloud = False
        for j,b in enumerate(profile[:buffer-1:-1]):
            jdash = n_vert-j
            if b and not inCloud:
                # if there are min_depth_bins 1s in a row, this should evaluate as True
                if np.all(profile[jdash-min_depth:jdash] == 1):
                    inCloud=True
            elif not b and inCloud:
                # if there are min_sep_bins 0s in a row, this should evaluate as True
                if np.all(profile[jdash-min_sep:jdash] == 0):
                    inCloud = False
            cm_down[jdash-1] = inCloud

        # we now combine the up and down pass to consolidate the cloud layers
        cm = np.logical_or(cm_up,cm_down)
        layer_mask[i,:] = cm

    return layer_mask
