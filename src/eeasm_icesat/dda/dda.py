'''Author: Andrew Martin
Creation date: 05/05/2023

Scripts for implementing the DDA-atmos cloud detection algorithm on backscatter data.

The function will operate on a 2-dimensional numpy array, where values given are the backscatter observations. The 'density' will be calculated for the backscatter based on the designated kernal.
From there, a second run to get lower density cloud regions can be performed, or the cleanup of the data to get the cloud layers can be performed.

I'm aiming to write the script in such a way that functions can be modularly selected so that different versions of the DDA algorithm can be implemented in the single script.
'''

import numpy as np
import xarray as xr
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


def calc_thresholds(data, downsample=0, segment_length=5, bias=60, sensitivity=1, quantile=90, **kwargs):
    '''Function to calculate the threshold for cloud pixels in the backscatter data.
    
    This function represents the synthesis of methods A and B in the ATL04/09 ATBD part 2 [https://doi.org/10.5067/48PJ5OUJOP4C]. The default arguments are for method B (although the bias and sensitivity values likely need changing for MPL data)

    INPUTS:
        data : np.ndarray
            2 dimesnsional (nxm) array containing the density field calculated in the DDA algortithm.

        downsample : int
            The number of bins (sqaured) to downsample the input data by. The downsampling takes the maximum value within a (dxd) square to use in the quantile caluclation. Here, d = 2*downsample+1 to ensure the max value is centered on the correct pixel. A value of 0 performs no downsampling.

        segment_length : int
            The number of vertical profiles (after downsampling) to consider in the moving window for the quantile calculation. The number will be 2*segment_length+1, to ensure that the measurement is always centered on the correct profile.

        bias : float
            The offset bia used in calculating the threshold.

        sensitivity : float
            The linear coefficient that multiplies the quantile value in the threshold calculation.

        quantile : float
            Value between 0 and 100 (in %), the quantile value that is to be used in the threshold calculation.

        kwargs : any additional arguments won't be used.

    OUTPUTS:
        threshold : np.ndarray
            The threshold value for clouds in each vertical profile in data. (1xm) matrix.

    '''
    # perform the downsampling first on a profile-by-profile basis
    downsample_matrix = data.copy()
    ny,nx = data.shape
    print(f'{downsample=}')
    if downsample > 0:
        print('dda.calc_thresholds: downsampling matrix')
        for xx in range(nx):
            # ensure the indices lie within the bounds of data
            ileft = np.max([0,xx-downsample])
            iright = np.min([nx,xx+downsample])
            for yy in range(ny):
                ibot = np.max([0,yy-downsample])
                itop = np.min([ny,yy+downsample])
                # ignores nan values, unless all values are nan and then return nan.
                downsample_matrix[yy,xx] = np.nanmax(data[ibot:itop,ileft:iright])

    # now need to access the downsampled matrix and perform the quantile calculations...
    print('dda.calc_thresholds: calculating thresholds')
    # NOTE: there are two approaches to the quantile calculation. Either the nans can be ignored, or considered as 0s. This will obvoiously impact the number of points being considered and thus the eventual quantile value. Change the following line ONLY to investigate this behaviour.
    downsample_matrix[np.isnan(downsample_matrix)] = 0 # this includes the nan values in the quantile calculation.
    thresholds = np.zeros(nx)
    for xx in range(nx):
        # handle edge cases:
        delta = 2*segment_length+1
        if xx-segment_length*delta < 0 or xx+segment_length*delta >= nx:
            for nn in np.arange(-segment_length,segment_length+1):
                quantileData = np.array([])
                if xx+nn*delta > 0 and xx+nn*delta<nx:
                    quantileData = np.concatenate((quantileData,downsample_matrix[:,xx+nn*delta]))
        # extract collums that have independant maximum values per pixel
        else:
            quantileData = downsample_matrix[:,xx-segment_length*delta:xx+segment_length*delta+1:delta]
        quantile_value = np.nanquantile(quantileData,quantile/100)
        thresholds[xx] = bias + sensitivity*quantile_value

    return thresholds

        


def dda(in_data,
        kernal_args={}, density_args={}, threshold_args={}, 
        two_pass=True,
        kernal_args2={}, density_args2={}, threshold_args2={},
        min_size=300):
    '''Function to run the DDA-atmos algortihm on the input ndarray.
    
    This will be the function to call in order to perform the full DDA-atmos algorithm on the input data. It will allow the user to configure the kernal, implement their own density function (if they so wish) and designate how the cloud-threshoilding is performed.

    INPUTS:
        in_data : np.ndarray (dtype=float)
            2-dimensional (nxm) numpy ndarray which will contain the input data for the DDA-atmos algorithm. There will be m profiles of n height bins.

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

        min_size : int
            Minimum size for cloud clusters to be, otherwise they're removed.

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
    if kernal_args != {}:
        if 'kernalfunc' not in kernal_args:
            kernal_args['kernalfunc'] = kernal_Gaussian
    else:
        kernal_args = {'kernalfunc':kernal_Gaussian}
    kernal = kernal_args['kernalfunc'](**kernal_args)

    # calculate the density field from the data using the masked convolution
    mask = np.isnan(in_data)
    density, norm = convolve_masked(in_data, mask, kernal, **density_args)
    return_data['density_pass1'] = density

    # calculate the thresholds for the cloud-pixels from the masked density field, and calculate the cloud_mask as a result
    thresholds = calc_thresholds(density, **threshold_args)
    #return_data['thresholds1'] = thresholds
    cloud_mask = np.greater(density, thresholds)

    if two_pass:

        # calculate the second kernal
        if kernal_args2 != {}:
            if 'kernalfunc' not in kernal_args2:
                kernal_args2['kernalfunc'] = kernal_Gaussian
        else:
            kernal_args2 = kernal_args
        kernal2 = kernal_args2['kernalfunc'](**kernal_args2)
    
        # TODO: implement noise in place of original clouds, rather than masked as 0 values (see ATBD pg135)
        if density_args2 == {}:
            density_args2 = density_args
        mask2 = np.logical_or(cloud_mask,mask)
        density2, norm = convolve_masked(in_data, mask2, kernal2, **density_args2)
        return_data['density_pass2'] = density2

        if threshold_args2 == {}:
            threshold_args2 = threshold_args
        thresholds2 = calc_thresholds(density2, **threshold_args2)
        #return_data['thresholds2'] = thresholds2
        cloud_mask2 = np.greater(density2, thresholds2)


        return_data['cloud_mask_passes'] = cloud_mask.astype(int) + 2*cloud_mask2.astype(int)

        # the final cloud mask is the combined set of determined cloud pixels from run 1 and run 2
        cloud_mask = np.logical_or(cloud_mask, cloud_mask2)

    cloud_mask = remove_small_objects(cloud_mask,min_size=300)
    return_data['cloud_mask'] = cloud_mask
    
    return return_data


def dda_from_xarray(ds, dda_var, coord_height, coord_x, sel_args = {},**dda_kwargs):
    '''Implements dda but using xarray dataset as input.
    
    INPUTS:
        ds : xr.Dataset
            xarray dataset containing variable [dda_var] as the input numpy array to the dda algorithm.

        dda_var : string
            the string variable name for the dda input array

        coord_height : string
            string for the name of the height dimension the dda_var can be transposed by.

        coord_x : string
            string for the name of the horizontal dimension the dda_var can be transposed by.

        sel_args : dict
            dictionary containing additional arguments for selecting the input data. This is used in case the input variable dda_var has additional dimensions (e.g. profile). If empty, then no additional selections will be performed.

        dda_kwargs : all additional arguments used in dda()

    OUTPUTS:
        ds : xr.Dataset
            same xarray dataset used in input, but with additional data in the relevant fields for the output.
    '''
    # extract the input variable from the dataset
    dda_in_da = ds[dda_var]
    mask = None
    if sel_args != {}:
        dda_in_da = dda_in_da.sel(**sel_args)
        # generate the mask used later to input values back into ds
        for k in sel_args:
                if mask is None:
                    mask = (ds[k] == sel_args[k])
                else:
                    mask = mask & (ds[k].coords(k) == sel_args[k])


    dda_in = dda_in_da.transpose(coord_height, coord_x).values

    # determine if the data was transposed to be input to the dda algorithm
    transposed = False
    if dda_in.shape != dda_in_da.values.shape:
        transposed=True
    print('dda_from_xarray')
    print(f'{transposed=} : {dda_in.shape=} ; {dda_in_da.values.shape=}')

    # perform the dda algorithm
    dda_out = dda(in_data=dda_in, **dda_kwargs)

    # if they don't exist create the new dda_out variables in ds_in and populate them according to the selection rules
    # each output array in the dictionary should be of the shape (height, coord_x), and can thus be made like dda_var...
    for k in dda_out:
        if ds.get(k) is None: 
            # if the variable doesn't already exist, create it
            ds[k] = xr.zeros_like(ds[dda_var])
            
        if transposed:
            dda_out[k] = dda_out[k].T

        # in the desired area, fill in with dda_out[k], otherwise, maintain the current value of ds_in[k]
        if mask is not None:
            ds[k] = xr.where(mask, dda_out[k], ds[k])
        else:
            ds[k] = (ds[k].dims,dda_out[k])

    return ds


