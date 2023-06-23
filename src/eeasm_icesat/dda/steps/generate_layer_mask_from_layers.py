'''Author: Andrew Martin
Creation Date: 23/6/23

Function to create a layer_mask variable from layer_top and layer_bot vectors
'''

import numpy as np

def generate_layer_mask_from_layers(layer_bot, layer_top, heights, verbose=False):
    '''Function to generate a layer_mask field given the layer boundaries.

    INPUTS:
        layer_bot : np.ndarray
            (n,n_layers) numpy array containing the layer top heights derived either from the DDA or given in the ATL09 data.

        layer_top : np.ndarray
            (n,n_layers) numpy array containing the layer bottom heights derived either from the dda or given in the ATL09 data.

        heights : np.ndarray
            (m,) numpy array of the height value for each vertical bin
    
        verbose : bool
            Flag for printing debug statements

    OUTPUTS:
        layer_mask : np.ndarray (dtype=bool)
            (n,m) numpy array containing 1s where the clouds exist and 0s where they don't
    '''
    if verbose: print('==== generate_layer_mask_from_layers()')
    (n_prof, n_layers) = layer_bot.shape
    (n_vert,) = heights.shape

    # check heights is ordered. If not, raise an error
    desc = False
    if (np.diff(heights)<0).any():
        if (np.diff(heights)>=0).any(): # raise error if not ordered
            msg = 'heights isnt ordered'
            raise ValueError(msg)
        desc = True
        #if descending, flip the heights values to have them in ascending order
        heights = np.flip(heights)

    layer_mask = np.zeros((n_prof, n_vert))

    # for each profile and each layer, set the layer_mask within the cloud to 1
    for i, (bots, tops) in enumerate(zip(layer_bot,layer_top)):
        for b,t in zip(bots, tops):
            # if both top and bottom height are valid values
            if ~np.isnan(b) and ~np.isnan(t):
                pmask = np.logical_and( heights <= t, heights >= b )
                layer_mask[i,pmask] = 1

    if desc:
        if verbose: print('Flipping final heights and layer_mask')
        heights = np.flip(heights)
        layer_mask = np.flip(layer_mask, axis=1)

    layer_mask = layer_mask.astype(bool)
    return layer_mask
