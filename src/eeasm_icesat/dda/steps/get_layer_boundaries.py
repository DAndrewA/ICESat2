'''Author: Andrew Martin
Creation Date: 16/6/23

The function to extract the layer height variables using the consolidated layer mask.
'''

import numpy as np
import numba

#@numba.jit(nopython=True)
def get_layer_boundaries(layer_mask, heights, n_layers=10, top_down=True, verbose=False):
    '''Function to extract the layer boundary heights using the consolidated layer_mask and the heights variable.
    
    The function can be performed from the top-down or bottom-up, which is given as an argument. NOTE: if top_down=False, then layer_bot and layer_top need to be swapped in the subsequent analysis

    Numba has been implemented to speed up computation
    
    INPUTS:
        layer_mask : np.ndarray (dtype=boolean)
            nxm numpy array containing the consolidated cloud layer mask information.

        heights : np.ndarray
            (m,) numpy array of the vertical height coordinates associated with each pixel. They should be ordered, either ascending or descending, but CANNOT be unordered.

        n_layers : int
            The maximum number of cloud layers to keep track of. The default for ATL09 is 10.

        top_down : bool
            Flag for whether to perform the layer assignment from the top-down or bottom-up.

        verbose : bool
            Flag for printing out debug statements

    OUTPUTS:
        num_cloud_layers : np.ndarray (dtype=int)
            (n,) numpy array containing the number of detected cloud layers in each profile

        layer_bot : np.ndarray
            (n,n_layers) numpy array containing the bottom heights of the layers.

        layer_top : np.ndarray
            (n,n_layers) numpy array containing the top heights of the detected layers.
    '''
    if verbose: print('==== dda.steps.get_layer_boundaries()')
    (n_prof, n_vert) = layer_mask.shape
    layer_bot = np.zeros((n_prof,n_layers)) *np.nan
    layer_top = np.zeros_like(layer_bot) *np.nan
    num_cloud_layers = np.zeros((n_prof,))
    
    # check heights is ordered. If not, raise an error
    desc = False
    if (np.diff(heights)<0).any():
        if (np.diff(heights)>=0).any(): # raise error if not ordered
            msg = 'heights isnt ordered'
            raise ValueError(msg)
        desc = True
        if verbose: print('heights is in descending order.')
        
    # correctly order heights and layer_mask for our analysis
    if (top_down and not desc) or (not top_down and desc):
        layer_mask = np.flip(layer_mask,axis=1)
        heights = np.flip(heights,axis=-1)
        print('layer_mask and heights flipped to account for desired direction of layer counting.')

    if verbose:print(f'{heights[0]=}  |  {heights[-1]=}')
    # for each profile
    for i, profile in enumerate(layer_mask):
        # iterate through the profile and assign layers
        inCloud = False
        layer_n = 0
        for j, (b, h) in enumerate(zip(profile, heights)):
            if b and not inCloud:
                layer_top[i,layer_n] = h
                inCloud = True
            elif not b and inCloud:
                layer_bot[i,layer_n] = heights[j-1]
                layer_n += 1
                inCloud = False
                if layer_n == n_layers:
                    break
        if inCloud: # if the final bit is in a cloud, correct the number of layers variable and set the cloud bottom to -1000
            layer_bot[i,layer_n] = -1000
            layer_n += 1
        num_cloud_layers[i] = layer_n

    if not top_down:
        layer_bot, layer_top = layer_top, layer_bot # swap the labelling of the variables as bottom_up counting will find cloud bottoms first rather than cloud tops.
        if verbose: print(f'Swapped layer_bot and layer_top because {top_down=}.')
    return num_cloud_layers, layer_bot, layer_top
