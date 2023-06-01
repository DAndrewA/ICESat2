'''Author: Andrew Martin
Creation date: 09/05/2023

Script containing functions to calculate the cloud layer properties from the cloudmask and density profiles from the DDA-atmos run.

The function takes heavy inspiration from Adam Hayes' function compute_cloud_layers_v2 (14/01/2020) as seen in the ICESAT2 ATL04/09 ATBD part 2 (page 117) [https://doi.org/10.5067/48PJ5OUJOP4C]
'''
import numpy as np
import xarray as xr


def compute_cloud_layers(ds, coord_height='height', coord_x='time', sel_args={}, numLayers=10, min_depth=90, min_sep=90, ground_clearance=50):
    '''Function for computing the cloud layer properties from output of the DDA-atmos algorithm
    
    INPUTS:
        ds : xr.Dataset
            xarray dataset containing the cloud_mask, density and height fields.

        coord_height : string
            The name of the height coordinate for the dataset.

        coord_x : string
            The 'horizontal' coordinate to iterate the algorithm over.

        sel_args : dictionary
            Dictionary containing arguments for selection of the appropriate data from the dataset (i.e. if the profile dimension needs to be accounted for). Leave blank to not consider 

        numLayers : int
            The maximum number of layers to be output in the data product. Set to 10 to match output from ATL09 data.

        min_depth : float
            The minimum depth of a cloud as given in the units of dim_height (i.e. meters)

        min_sep : float
            The minimum separation between cloud layers in the units of dim_height (i.e. meters)

        ground_clearance : float, np.ndarray
            The minimum height above ground level (height=0) that will be considered for the cloud flags. If a cloud layer exists down to 50m, then the cloud base will be set as 0m.
            If given as a numpy array, must be the same shape as the coord_x.

    OUPUTS:
        ds : xr.Dataset
            xarray dataset containing the additional fields: layer_bot, layer_top, layer_dens, layer_ib, msw_flag, cloud_flag_atm, layer_conf_dens
    '''
    # get the arrays for the coordinates
    xcoor = ds.coords[coord_x]
    ycoor = ds.coords[coord_height]

    # if the height coordinate isn't in ascending order, need to make sure to flip it
    flipped = False
    if (np.diff(ycoor)<=0).any():
        if (np.diff(ycoor)>0).any(): # raise error if not ordered
            msg = 'ycoor isnt ordered'
            raise ValueError(msg)
        flipped = True
        ycoor = np.flip(ycoor)

    # get the index of the lowest bin we want to consider (in the case that ground_clearance is a float)
    if type(ground_clearance) != np.ndarray:
        y_min_i = int(np.sum(ycoor < ground_clearance))

    # get the bin numbers for the separation and depth parameters
    dy = ycoor[1] - ycoor[0]
    min_depth_bins = int(np.round(min_depth/dy))
    min_sep_bins = int(np.round(min_sep/dy))
    bins_buffer = int(np.max([min_depth_bins,min_sep_bins]))

    # extract the cloud mask numpy array with the indices (horizontal,height).
    cloud_mask_da = ds.transpose(coord_x,coord_height,...).cloud_mask
    if sel_args != {}:
        cloud_mask_da = cloud_mask_da.sel(**sel_args)
    cloud_mask = cloud_mask_da.values
    del cloud_mask_da

    if flipped:
        cloud_mask = np.flip(cloud_mask, axis=1)

    print(f'dda.compute_cloud_layers: {cloud_mask.shape=}')
    layer_bot = np.zeros((numLayers, xcoor.size))*np.nan
    layer_top = np.zeros((numLayers, xcoor.size))*np.nan
    #layer_conf_dens = np.zeros((numLayers, xcoor.size))
    #layer_dens = np.zeros((numLayers, xcoor.size))
    #layer_ib = np.zeros((numLayers, xcoor.size))
    #msw_flag = np.zeros(xcoor.size)
    cloud_flag_atm = np.zeros(xcoor.size)

    # go through each vertical profile
    for i,profile in enumerate(cloud_mask):
        cm_up = np.zeros_like(profile)
        cm_down = np.zeros_like(profile)

        # if ground clearance is a numpy array, y_min_i needs to be caluclated at each profile
        if type(ground_clearance) == np.ndarray:
            y_min_i = int(np.sum(ycoor < ground_clearance[i]))

        #upwards pass
        inCloud = False
        for j,b in enumerate(profile[y_min_i:-bins_buffer]):
            # b is a bool, 1 for cloud, 0 for not
            j = j+y_min_i
            if b and not inCloud:
                # if there are min_depth_bins 1s in a row, this should evaluate as True
                if np.all(profile[j:j+min_depth_bins] == 1):
                    inCloud=True
            elif not b and inCloud:
                # if there are min_sep_bins 0s in a row, this should evaluate as True
                if np.all(profile[j:j+min_sep_bins] == 0):
                    inCloud = False
            if inCloud:
                cm_up[j] = 1

        # downwards pass
        inCloud = False
        for j,b in enumerate(profile[:y_min_i+bins_buffer:-1]):
            jdash = profile.size-j
            if b and not inCloud:
                # if there are min_depth_bins 1s in a row, this should evaluate as True
                if np.all(profile[jdash-min_depth_bins:jdash] == 1):
                    inCloud=True
            elif not b and inCloud:
                # if there are min_sep_bins 0s in a row, this should evaluate as True
                if np.all(profile[jdash-min_sep_bins:jdash] == 0):
                    inCloud = False
            if inCloud:
                cm_down[jdash-1] = 1

        # consolidate up and down passes
        cm = np.logical_or(cm_up,cm_down)

        # determine layer properties from top to bottom...
        # downwards pass
        n_layers = 0
        inCloud = False
        for j,b in enumerate(cm[::-1]):
            jdash = profile.size-j-1
            # detect cloud tops
            if b and not inCloud:
                n_layers += 1
                layer_top[n_layers-1,i] = ycoor[jdash]
                inCloud = True
            # detect cloud bases
            if not b and inCloud:
                layer_bot[n_layers-1,i] = ycoor[jdash+1] # +1 as its the previous cell containing cloud
                inCloud = False
                if n_layers >= numLayers:
                    print('dda.compute_cloud_layers: max number of cloud layers reached, continuing...')
                    continue
        if inCloud: # this should only run if ground_clearance < 0.5dy
            print('compute_cloud_layers: ground clearance set too low, cloud detected at ground level.')
            layer_bot[n_layers-1,i] = 0
        cloud_flag_atm[i] = n_layers

    # setup dimension and coordinates for ds to accomodate cloud layers
    # the use of newds is to ensure not all variables require the layer coordinate
    if 'layer' not in ds.dims: 
        # the following code also stops 'layer' from being copied into every DataArray's shape
        newds = ds.expand_dims(dim={'layer': np.arange(numLayers)})
        for k in newds:
            newds[k] = ds[k]
        ds = newds.copy()
        del newds

    # for each calculated layer parameter, insert it into the dataset
    for k,d in zip(['layer_bot','layer_top','cloud_flag_atm'],
                   [layer_bot,layer_top,cloud_flag_atm]):
        if ds.get(k) is None: 
            # if the variable doesn't already exist, create it
            new_desired_dims = (*sel_args.keys(), coord_x)
            if d.ndim == 2:
                new_desired_dims = (*new_desired_dims, 'layer')
            new_dims = [dim for dim in ds.dims if dim in new_desired_dims]
            new_shape = [int(ds.dims[dd]) for dd in new_dims]
            ds[k] = xr.DataArray(data=np.zeros(new_shape), dims=new_dims)

        # create a dataArray with the calculated data, that can be transposed into the correct format
        if d.ndim == 2:
            dims = {'layer':ds.dims['layer'],
                    coord_x:ds.dims[coord_x]}
        else:
            dims = {coord_x:ds.dims[coord_x]}
        da = xr.DataArray(d, dims=dims)

        # transpose the data into the correct dimensional order for the dataset
        new_dims = [dim for dim in ds.dims if dim in dims] # gets the dataset-ordered dimensions
        print(f'reordering dims: dims={dims.keys()}; reordered={new_dims}')
        da = da.transpose(*new_dims)
        
        if sel_args != {}:
            out_mask = None
            for sa in sel_args:
                if out_mask is None:
                    out_mask = (ds[sa] == sel_args[sa])
                else:
                    out_mask = out_mask & (ds[sa].coords(sa) == sel_args[sa])
            ds[k] = xr.where(out_mask, da, ds[k])
        else:
            ds[k] = da
    
    return ds
