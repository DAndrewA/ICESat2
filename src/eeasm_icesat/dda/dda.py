'''Author: Andrew Martin
Creation date: 05/05/2023

Scripts for implementing the DDA-atmos cloud detection algorithm on backscatter data.

The function will operate on a 2-dimensional numpy array, where values given are the backscatter observations. The 'density' will be calculated for the backscatter based on the designated kernal.
From there, a second run to get lower density cloud regions can be performed, or the cleanup of the data to get the cloud layers can be performed.

I'm aiming to write the script in such a way that functions can be modularly selected so that different versions of the DDA algorithm can be implemented in the single script.
'''

import numpy as np
from scipy import signal
from skimage.morphology import remove_small_objects


def kernal_Gaussian(sigma_y, sigma_x=None, a_m=None,
                    cutoff=None, n=None, m=None, 
                    dx=1,dy=1, **kwargs):
    '''Function to calculate and return a normalised Gaussian kernal.
    
    In order to work, this function requires:
        sigma_y, {sigma_x OR a_m}, {cutoff OR n AND m}

    INPUTS:
        dx : float, np.timedelta64
            The horizontal resolution of the data. Can be a distance or a time.

        dy : float, np.timedelta64
            The vertical resolution of the data. Can be a distance or a time.

        sigma_y : type(dy)
            The standard deviation of the kernal in the vertical direction. Given in the same units as dy.

        sigma_x : type(dx)
            The standard deviation of the kernal in the horizontal resolution. Given in the same units as dx. Supersedes a_m 

        a_m : float
            The anisotropy (in units) of the kernal, defined as sigma_x/sigma_y

        cutoff : float
            Number of standard deviations in both directions to cut the kernal off at. Supersedes n and m

        n : int
            Height of the kernal in pixels

        m : float
            Width of the kernal in pixels

        **kwargs : any additional arguments. These won't be used however.

    OUTPUTS:
        kernal : np.ndarray
            2-dimensional numpy array for the Gaussian kernal.
    '''
    if sigma_x is None:
        if a_m is None:
            print('dda.kernal_Gaussian: a_m and sigma_x undefined')
            raise ValueError
        sigma_x = sigma_y * a_m
    
    if cutoff is not None:
        n = 2 * np.round(sigma_y/dy * cutoff) + 1
        m = 2 * np.round(sigma_x/dx * cutoff) + 1

    x = np.arange(-m//2, m//2+1)*dx
    y = np.arange(-n//2, n//2+1)*dy
    X,Y = np.meshgrid(x,y)
    
    gaussian = lambda x,y,sx,sy: np.exp(-0.5 * (np.power(x/sx, 2) + np.power(y/sy, 2)))
    kernal = gaussian(X,Y,sigma_x,sigma_y)
    return kernal / np.sum(kernal) # return the normalised version of the kernal


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

    '''
    convargs = {'mode':'same', 'boundary':'symm'} # default convargs
    for arg in ['mode','boundary','fillvalue']:
        if arg in kwargs:
            convargs[arg] = kwargs[arg]

    norm = signal.convolve2d(~mask, kernal, **convargs)
    masked_data = data.copy()
    masked_data[mask] = 0
    density = signal.convolve2d(masked_data,kernal, **convargs)

    # normalise density field
    density[norm>0] = density[norm>0] / norm[norm>0]
    return density, norm


def calc_thresholds(data, mask):
    raise NotImplementedError


def dda(in_data,
        kernal_args={}, density_args={}, threshold_args={}, 
        two_pass=False,
        kernal_args2={}, density_args2={}, threshold_args2={}):
    '''Function to run the DDA-atmos algortihm on the input ndarray.
    
    This will be the function to call in order to perform the full DDA-atmos algorithm on the input data. It will allow the user to configure the kernal, implement their own density function (if they so wish) and designate how the cloud-threshoilding is performed.

    INPUTS:
        in_data : np.ndarray (dtype=float)
            2-dimensional numpy ndarray which will contain the input data for the DDA-atmos algorithm.

        kernal_args : dict
            Dictionary containing the arguments for the kernal computation. If 'kernalfunc' is not a specified key, then the default Gaussian kernal will be used. Otherwise, additional kernal functions can be specified.
            Defaults to None, where default arguments will be used.

        density_args : dict
            Dictionary containing arguments for the density calculation.

        threshold_args : dict
            Dictionary containing arguments for the threshold calculation.

        two_pass : boolean
            Flag to determine if the algorithm should perform a second pass of the DDA-atmos algorithm with an updated density mask. If yes, then the following arguments will be utilised.

        kernal_args2 : dict
            Same as kernal_args. If not specified, kernal_args will be used.

        density_args2 : dict
            Same as density_args, except for the second pass. If not specified, density_args will be used.

        threshold_args2 : dict
            Same as threshold_args, except for the second pass. If not specified, threshold_args will be used.

    OUTPUTS:
        return_data : dict : see following descriptions

        density1 : np.ndarray
            The calculated density field from the first pass

        density2 : np.ndarray
            The calculated density field from the second pass

        cloud_mask : np.ndarray
            The boolean cloud mask for the whole algorithm. This is the output that has had small clusters removed, so cloud_mask_passes can't be directly derived from cloud_mask

        cloud_mask_passes : np.ndarray
            Cloud mask containing data for both passes. 0: no cloud; 1: cloud in pass 1; 2: cloud in pass 2; 3: cloud in both pass 1 and pass 2

    '''
    return_data = {}

    # calculate the kernal from the given parameters
    if kernal_args is not None:
        if 'kernalfunc' not in kernal_args:
            kernal_args['kernalfunc'] = kernal_Gaussian
    else:
        kernal_args = {'kernalfunc':kernal_Gaussian}
    kernal = kernal_args['kernalfunc'](**kernal_args)

    # calculate the density field from the data using the masked convolution
    mask = np.isnan(in_data)
    density, norm = convolve_masked(in_data, mask, kernal, **density_args)
    return_data['density1'] = density

    return return_data
    # calculate the thresholds for the cloud-pixels from the masked density field, and calculate the cloud_mask as a result
    thresholds = calc_thresholds(density, mask, **threshold_args)
    cloud_mask = np.greater(density, thresholds)

    if two_pass:

        # calculate the second kernal
        if kernal_args2 is not None:
            if 'kernalfunc' not in kernal_args2:
                kernal_args2['kernalfunc'] = kernal_Gaussian
        else:
            kernal_args2 = kernal_args
        kernal2 = kernal_args2['kernalfunc'](**kernal_args2)
    
        # TODO: implement noise in place of original clouds, rather than masked as 0 values (see ATBD pg135)
        if density_args2 is None:
            density_args2 = density_args
        mask2 = np.logical_or(cloud_mask,mask)
        density2, norm = convolve_masked(in_data, mask2, kernal2, **density_args2)
        return_data['density2'] = density2

        if threshold_args2 is None:
            threshold_args2 = threshold_args
        thresholds2 = calc_thresholds(density2, mask2, **threshold_args2)
        cloud_mask2 = np.greater(density2, thresholds2)


        return_data['cloud_mask_passes'] = cloud_mask.astype(int) + 2*cloud_mask2.astype(int)

        # the final cloud mask is the combined set of determined cloud pixels from run 1 and run 2
        cloud_mask = np.logical_or(cloud_mask, cloud_mask2)

    cloud_mask = remove_small_objects(cloud_mask,min_size=300)
    return_data['cloud_mask'] = cloud_mask
    
    return return_data