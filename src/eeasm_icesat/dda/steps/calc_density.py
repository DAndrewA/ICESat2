'''Author: Andrew Martin
Creation Date: 16/6/23

Function to calculate the density field from data and a data mask.
'''

import numpy as np
from scipy.signal import convolve2d

def calc_density(data, data_mask, kernal, density_args, verbose=False):
    '''Function to calculate the density field from data and a data_mask using the provided kernal.
    
    INPUTS:
        data : np.ndarray
            nxm numpy array containing intensity data for n vertical profiles of m vertical height bins.

        data_mask : np.ndarray (dtype=boolean)
            nxm boolean numpy array containing a mask for valid data for the density calculation. 1s represent invalid data, 0s represent valid data.

        kernal : np.ndarray
            jxk numpy array (smaller than data) that defines the kernal the data is convolved by in the density field caluclation.

        density_args: dictionary
            dictionary containing additional arguments for the calculation of the density field, namely, the other arguments in scipy.signal.convolve2d.

    OUTPUTS:
        density : np.ndarray
            nxm numpy array containing the density field of data.
    '''
    print('==== dda.steps.calc_density()')
    density = convolve_masked(data, data_mask, kernal, density_args)
    return density


def convolve_masked(data, mask, kernal, **kwargs):
    '''Function to perform a convolution of a kernal on masked data.
    
    The convention is that masked values are 1s in mask, and the data to convolve is 0s in the mask.
    For a convolution on masked data, this is essentially treating the nan values as 0, but also calculating the changed kernal normalisation due to the mask.

    !!!! The normalised density field is returned !!!!

    INPUTS:
        data : np.ndarray
            array containing the data for which we want to perform the masked convolution on

        mask : np.ndarray (dtype=boolean)
            array of the same shape as data that contains 1s where nans and masked values are, and 0s where the desired data exists.

        kernal : np.ndarray
            convolutional kernal

        kwargs : other arguments to be passed to np.convolve

    OUTPUTS:
        density : np.ndarray
            numpy array the same shape as data that contains the density field of data convolved with kernal.
    '''
    convargs = {'mode':'same', 'boundary':'symm'} # default convargs
    for arg in ['mode','boundary','fillvalue']:
        if arg in kwargs:
            convargs[arg] = kwargs[arg]

    norm = convolve2d(~mask, kernal, **convargs)
    masked_data = data.copy()
    masked_data[mask] = 0
    density = convolve2d(masked_data,kernal, **convargs)

    # normalise density field
    density[norm>0] = density[norm>0] / norm[norm>0]
    return density
