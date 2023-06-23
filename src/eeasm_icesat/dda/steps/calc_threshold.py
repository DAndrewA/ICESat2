'''Author: Andrew Martin
Creation Date: 16/6/23

Function to calculate the cloud layer threshold, given the data matrix, a data mask and the threshold parameters.
'''

import numpy as np

def calc_threshold(density, data_mask=None, downsample=0, segment_length=5, bias=60, sensitivity=1, quantile=90, verbose=False, **kwargs):
    '''Function to calculate the threshold values for cloud pixels in each vertical profile of the density field.
    
    This function represents the synthesis of methods A and B in the ATL04/09 ATBD part 2 [https://doi.org/10.5067/48PJ5OUJOP4C]. The default arguments are for method B (although the bias and sensitivity values likely need changing for MPL data)

    INPUTS:
        density : np.ndarray
            nxm numpy array containing the density field data.

        data_mask : None, np.ndarray (dtype=boolean)
            nxm numpy array containing the locations of the invalid data points. If None, then no special handling of the NaN values will be performed for the quantile calculation.

        downsample : int
            The number of bins (squared) to downsample the input data by. The downsampling takes the maximum value within a (dxd) square to use in the quantile caluclation. Here, d = 2*downsample+1 to ensure the max value is centered on the correct pixel. A value of 0 performs no downsampling.

        segment_length : int
            The number of vertical profiles (after downsampling) to consider in the moving window for the quantile calculation. The number will be 2*segment_length+1, to ensure that the measurement is always centered on the correct profile.

        bias : float
            The offset bia used in calculating the threshold.

        sensitivity : float
            The linear coefficient that multiplies the quantile value in the threshold calculation.

        quantile : float
            Value between 0 and 100 (in %), the quantile value that is to be used in the threshold calculation.

        verbose : bool
            Flag for printing out debug statements

        kwargs : additional arguments won't be used.

    OUTPUTS:
        thresholds : np.ndarray
            (n,1) numpy array containing the threshold value for clouds in each vertical profile in data.
    '''
    if verbose: print('==== dda.steps.calc_threshold()')
    (n_prof,n_vert) = density.shape
    downsample_matrix = _downsample_matrix(density, downsample, verbose)
    # need to access the downsampled matrix and perform the quantile calculations...
    if verbose: print('Calculating thresholds.')
    if data_mask is not None: # if the data mask is provided, set the masked values to nan. Otherwise, they will have some density value.
        downsample_matrix[data_mask] = np.nan

    thresholds = np.zeros(n_prof)
    for xx in range(n_prof):
        # handle edge cases:
        delta = 2*downsample+1
        xleft = xx-segment_length*delta
        xright = xx+segment_length*delta
        if xleft < 0 or xright > n_prof-1:
            xleft = np.max([0,xleft])
            xright = np.min([xright, n_prof-1])
        # extract collums that have independant maximum values per pixel
        quantileData = downsample_matrix[xleft:xright+1:delta,:]

        quantile_value = np.nanquantile(quantileData,quantile)
        thresholds[xx] = bias + sensitivity*quantile_value

    thresholds = np.expand_dims(thresholds,axis=-1) # set the shape to (n,1) rather than (n,) for broadcasting when calculating cloud_mask
    return thresholds


def calc_threshold_vectorized(density, data_mask=None, downsample=0, segment_length=5, bias=60, sensitivity=1, quantile=90, verbose=False, **kwargs):
    '''Function to calculate the threshold values for cloud pixels in each vertical profile of the density field.
    
    This function represents the synthesis of methods A and B in the ATL04/09 ATBD part 2 [https://doi.org/10.5067/48PJ5OUJOP4C]. The default arguments are for method B (although the bias and sensitivity values likely need changing for MPL data)

    This version of the function is vectorized to improve speed of execution. It will however, be more memory intensive.

    INPUTS:
        density : np.ndarray
            nxm numpy array containing the density field data.

        data_mask : None, np.ndarray (dtype=boolean)
            nxm numpy array containing the locations of the invalid data points. If None, then no special handling of the NaN values will be performed for the quantile calculation.

        downsample : int
            The number of bins (squared) to downsample the input data by. The downsampling takes the maximum value within a (dxd) square to use in the quantile caluclation. Here, d = 2*downsample+1 to ensure the max value is centered on the correct pixel. A value of 0 performs no downsampling.

        segment_length : int
            The number of vertical profiles (after downsampling) to consider in the moving window for the quantile calculation. The number will be 2*segment_length+1, to ensure that the measurement is always centered on the correct profile.

        bias : float
            The offset bia used in calculating the threshold.

        sensitivity : float
            The linear coefficient that multiplies the quantile value in the threshold calculation.

        quantile : float
            Value between 0 and 100 (in %), the quantile value that is to be used in the threshold calculation.

        verbose : bool
            Flag for printing out debug statements

        kwargs : additional arguments won't be used.

    OUTPUTS:
        thresholds : np.ndarray
            (n,1) numpy array containing the threshold value for clouds in each vertical profile in data.
    '''
    if verbose: print('==== dda.steps.calc_threshold_vectorized()')
    (n_prof, n_vert) = density.shape
    downsample_matrix = _downsample_matrix(density, downsample, verbose)
    # need to access the downsampled matrix and perform the quantile calculations...
    if verbose: print('Calculating thresholds.')
    if data_mask is not None: # if the data mask is provided, set the masked values to nan. Otherwise, they will have some density value.
        downsample_matrix[data_mask] = np.nan

    thresholds = np.zeros(n_prof)

    if verbose: print('Creating denity_stacked.')
    delta = 2*downsample+1
    pad_vals = np.arange(-segment_length,segment_length+1)*delta
    # create the large data array to store all the values for the window
    density_stacked = np.zeros((n_prof, (2*segment_length+1)*n_vert))
    if verbose: print(pad_vals)
    if verbose: print(f'{density_stacked.shape=}')

    for i, pad in enumerate(pad_vals):
        pad = int(pad)
        if pad < 0: # left pad for pad less than zero
            pad_mat = np.pad(downsample_matrix,((0,0),(-pad,0)),constant_values=(np.nan))[:,:pad]
        else: # paddings greater than 0 are right-padded
            pad_mat = np.pad(downsample_matrix,((0,0),(0,pad)),constant_values=(np.nan))[:,pad:]

        density_stacked[:, i*n_vert:(i+1)*n_vert] = pad_mat

    thresholds = bias + sensitivity* np.nanquantile(density_stacked,quantile,axis=1)

    thresholds = np.expand_dims(thresholds,axis=-1) # set the shape to (n,1) rather than (n,) for broadcasting when calculating cloud_mask
    return thresholds, density_stacked


def _downsample_matrix(density,downsample, verbose=False):
    '''Funciton to perform the downsampling of the matrix for threshold calculation as used in earlier versions of the ATL09 product.
    
    INPUTS:
        density : np.ndarray
            (n,m) numpy array of the density values to be downsampled.

        downsample : int
            The number of bins (squared) to downsample the input data by. The downsampling takes the maximum value within a (dxd) square to use in the quantile caluclation. Here, d = 2*downsample+1 to ensure the max value is centered on the correct pixel. A value of 0 performs no downsampling.

        verbose : bool
            Flag for printing debug statements to output log

    OUTPUTS:
        downsample_matrix : np.ndarray
            (n,m) numpy array containing the values for the downsampled density matrix
    '''
    # perform the downsampling first on a profile-by-profile basis
    (n_prof,n_vert) = density.shape
    downsample_matrix = density.copy()
    
    if downsample > 0:
        if verbose: print('Downsampling matrix.')
        for xx in range(n_prof):
            # ensure the indices lie within the bounds of data
            ileft = np.max([0,xx-downsample])
            iright = np.min([n_prof,xx+downsample])
            for yy in range(n_vert):
                ibot = np.max([0,yy-downsample])
                itop = np.min([n_vert,yy+downsample])
                # ignores nan values, unless all values are nan and then return nan.
                downsample_matrix[xx,yy] = np.nanmax(density[ileft:iright,ibot:itop])
    
    return downsample_matrix
