'''Author: Andrew Martin
Creation Date: 20/6/23

Functions for cerating kernals for use in the DDA algorithm.
'''

import numpy as np

def Gaussian(sigma_y, sigma_x=None, a_m=None, cutoff=None, n=None, m=None, dx=1,dy=1, verbose=False, **kwargs):
    '''Function to calculate and return a normalised Gaussian kernal.
    
    In order to work, this function requires:
        sigma_y, {sigma_x OR a_m}, {cutoff OR n AND m}

    In the case for the implementation of the DDA algorithm, x represents the horizontal dimension (axis=0) and y represents the vertical dimension (axis=1).

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

        verbose : bool
            Flag for printing out debug statements

        **kwargs : any additional arguments. These won't be used however.

    OUTPUTS:
        kernal : np.ndarray
            2-dimensional numpy array for the Gaussian kernal.
    '''
    if verbose: print('==== dda.steps.create_kernal.Gaussian()')
    if sigma_x is None:
        if a_m is None:
            print('dda.steps.create_kernal.Gaussian: a_m and sigma_x undefined')
            raise ValueError
        sigma_x = sigma_y * a_m
    
    if cutoff is not None:
        n = 2 * np.round(sigma_y/dy * cutoff) + 1
        m = 2 * np.round(sigma_x/dx * cutoff) + 1

    x = np.arange(-(m//2), m//2+1)*dx
    y = np.arange(-(n//2), n//2+1)*dy
    X,Y = np.meshgrid(y,x) # order reversed due to x,y definition of indices in this library
    if verbose:
        print(f'({n=}, {m=})  {X.shape=}')
        print(f'{x=}')
        print(f'{y=}')
    gaussian = lambda x,y,sx,sy: np.exp(-0.5 * (np.power(x/sx, 2) + np.power(y/sy, 2)))
    
    kernal = gaussian(X,Y,sigma_y,sigma_x)
    return kernal / np.sum(kernal) # return the normalised version of the kernal
