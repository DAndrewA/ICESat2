'''Author: Andrew Martin
Creation date: 09/05/2023

Script containing functions to calculate the cloud layer properties from the cloudmask and density profiles from the DDA-atmos run.

The function takes heavy inspiration from Adam Hayes' function compute_cloud_layers_v2 (14/01/2020) as seen in the ICESAT2 ATL04/09 ATBD part 2 (page 117) [https://doi.org/10.5067/48PJ5OUJOP4C]
'''
import numpy as np
import xarray as xr


def compute_cloud_layers(ds, coord_height='height', coord_x='time', numLayers=10, min_depth=90, min_sep=90, ground_clearance=50):
    '''Function for computing the cloud layer properties from output of the DDA-atmos algorithm
    
    INPUTS:
        ds : xr.Dataset
            xarray dataset containing the cloud_mask, density and height fields.

        coord_height : string
            The name of the height coordinate for the dataset.

        coord_x : string
            The 'horizontal' coordinate to iterate the algorithm over.

        numLayers : int
            The maximum number of layers to be output in the data product. Set to 10 to match output from ATL09 data.

        min_depth : float
            The minimum depth of a cloud as given in the units of dim_height (i.e. meters)

        min_sep : float
            The minimum separation between cloud layers in the units of dim_height (i.e. meters)

        ground_clearance : float
            The minimum height above ground level (height=0) that will be considered for the cloud flags. If a cloud layer exists down to 50m, then the cloud base will be set as 0m

    OUPUTS:
        ds : xr.Dataset
            xarray dataset containing the additional fields: layer_bot, layer_top, layer_dens, layer_ib, msw_flag, cloud_flag_atm, layer_conf_dens
    '''
    # get the arrays for the coordinates
    xcoor = ds.coords[coord_x]
    ycoor = ds.coords[coord_height]

    # get the index of the lowest bin we want to consider
    y_min_i = int(np.sum(ycoor < ground_clearance))
    # get the bin numbers for the separation and depth parameters
    dy = ycoor[1] - ycoor[0]
    min_depth_bins = int(np.round(min_depth/dy))
    min_sep_bins = int(np.round(min_sep/dy))
    bins_buffer = int(np.max([min_depth_bins,min_sep_bins]))

    # extract the cloud mask numpy array with the indices (x,y)
    cloud_mask = ds.transpose(coord_x,coord_height,...).cloud_mask.values
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
    newds = ds.expand_dims(dim={'layer': np.arange(numLayers)})
    for k in list(ds.keys()):
        newds[k] = (ds[k].dims,ds[k].values)
    
    newds['layer_bot'] = (['layer',coord_x],layer_bot)
    newds['layer_top'] = (['layer',coord_x],layer_top)
    newds['cloud_flag_atm'] = ([coord_x],cloud_flag_atm)

    newds['cm_up'] = ([coord_height], cm_up)
    newds['cm_down'] = ([coord_height],cm_down)
    newds['cm'] = ([coord_height],cm)
    return newds
