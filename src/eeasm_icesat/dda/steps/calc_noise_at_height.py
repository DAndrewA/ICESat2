'''Author: Andrew Martin
Creation Date: 22/6/23

Script containing function to calculate the noise profile at height of masked data.
'''

import numpy as np

def calc_noise_at_height(data, cloud_mask, heights, dem, altitude, quantile, include_nans=False, smooth_bins=2, verbose=False):
    '''Function to calculate the noise profile of the ATL09 data from high altitude measurements.

    This function calculates the noise by taking the mean and standard deviation of values in the data array that are a certain altitude above the dem and not contained in the cloud_mask from density1. The aim of this is to allow the filling of the cloud mask with noisy values with a reasonable power spectrum.
    
    INPUTS:
        data : np.ndarray
            (n,m) numpy array containing the raw ATL09 profile data that is used as input for the density calculations.

        cloud_mask : np.ndarray (dtype=bool)
            (n,m) numpy array containing the mask for cloudy pixels (1s) and non cloudy pixels (0s) determined in the first pass of the DDA.

        heights : np.ndarray
            (m,) numpy array conatining the height values for the vertical bins.

        dem : np.ndarray
            (n,) numpy array containing the Digital Elevation Model heights determined from the ATL09 data.

        altitude : float
            Altitude in meters above which data will be considered to be noisy

        quantile : float
            Quantile value given in threshold_args2. This is used to ensure that the noise shouldn't pollute the threshold calculation if signal exists, but will reduce noise from being classified as signal.

        include_nans : bool
            Include np.nan values in the mean and standard deviation calculations as 0-values. If set to True, this will cause the mean and sd to be dramatically lower than they otherwise would be, due to the empty bins at the top of all profiles.

        smooth_bins : int
            Number of profiles either side of a given profile over which a rolling average of mean and sd values are taken.

        verbose : bool
            Flag for printing debug statements to the log
 
    OUTPUTS:
        mean : np.ndarray
            (n,) numpy array containing the smoothed mean noise value for each profile

        sd : np.ndarray
            (n,) numpy array containing the smoothed standard deviation value for each vertical profile's noise spectrum.
    '''
    if verbose: print('==== dda.steps.calc_noise_at_height()')
    (n_prof, n_vert) = data.shape
    # create a mask based on bin altitude above ground level
    delta_heights = heights.reshape((1,n_vert)) - dem.reshape(n_prof,1)
    altitude_mask = delta_heights >= altitude
    
    # create the final data mask
    data_mask = np.logical_or(altitude_mask, cloud_mask)
    if include_nans:
        data[np.isnan(data)] = 0
    else:
        data_mask = np.logical_or(data_mask, np.isnan(data))

    data[data_mask] = np.nan

    # calculate the quantile values for each vertical profile
    quant_vals = np.nanquantile(data,quantile, axis=1)
    if verbose: print(f'{np.max(quant_vals)=}  |  {np.min(quant_vals)=}')

    # calculate the profile means and standard deviations
    if verbose: print('Calculating mean and sd')
    mean = np.zeros_like(quant_vals)
    sd = np.zeros_like(quant_vals)
    for i, prof in enumerate(data):
        mean[i] = np.nanmean(prof[prof < quant_vals[i]])
        sd[i] = np.nanstd(prof[prof < quant_vals[i]])

    if smooth_bins > 0:
        if verbose: print('Smoothing mean and sd')
        width = 2*smooth_bins + 1
        mean = np.convolve(mean, np.ones(width)/width, mode='same')
        sd = np.convolve(sd, np.ones(width)/width, mode='same')

    return mean, sd

    
    




    
